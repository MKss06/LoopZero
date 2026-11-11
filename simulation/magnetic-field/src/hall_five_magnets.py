"""Confere a nova grade Hall e compara uma fileira hipotética de cinco cuboides."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

import magpylib as magpy
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from compare_hall_mountings import AXES_LOCAL, mounting_setup
from hall_analysis import ROOT, _workbook_sheets
from hall_grid_analysis import MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM, PREVIOUS_SCALE_V_PER_T
from magnet_geometry import dimensions_for


SOURCE = ROOT / "data" / "experiments" / "hall-sensor" / "mapeamento_cinco_imans.xlsx"
OUTPUT = ROOT / "data" / "processed" / "hall-sensor"
STEM = "mapeamento-cinco-imans-horizontal"
SIDES = ("Lado 1", "Lado 2")
X_MM = (5, 10, 20, 30, 50)
Y_MM = (-10, 0, 10)
ADC_TO_V = 5.0 / 1023  # tensão nominal usada na planilha; não aferida
MAGNET_COUNT = 5
SS49E_DATASHEET = (
    "https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/"
    "products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/"
    "documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf"
)


@dataclass(frozen=True)
class Position:
    side: str
    x_mm: int
    y_mm: int
    count: int
    mean_adc: float
    voltage_v: float


@dataclass(frozen=True)
class References:
    initial_count: int
    initial_adc: float
    final_count: int
    final_adc: float

    @property
    def drift_v(self) -> float:
        return (self.final_adc - self.initial_adc) * ADC_TO_V


def _close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
        raise ValueError(f"Valor divergente em {label}: {actual} ≠ {expected}")


def _verify_formulas(source: Path) -> None:
    """Confere fórmulas e caches, sem recalcular ou alterar o arquivo XLSX."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(source) as book:
        root = ElementTree.fromstring(book.read("xl/worksheets/sheet1.xml"))
    formulas = {}
    for cell in root.findall(".//m:c", ns):
        expression = cell.find("m:f", ns)
        if expression is not None:
            cached = cell.find("m:v", ns)
            if cached is None or cached.text is None:
                raise ValueError(f"Fórmula sem valor em cache: {cell.get('r')}")
            formulas[cell.get("r")] = (expression.text, float(cached.text))
    expected = {f"F{number}": f"E{number}*5/1023" for number in range(5, 35)}
    expected.update({"D39": "C39*5/1023", "D40": "C40*5/1023",
                     "C41": "C40-C39", "D41": "D40-D39"})
    if set(formulas) != set(expected):
        raise ValueError("Conjunto de fórmulas inesperado na planilha")
    for cell, expression in expected.items():
        if formulas[cell][0] != expression:
            raise ValueError(f"Fórmula inesperada em {cell}")


def load_collection(source: Path = SOURCE) -> tuple[list[Position], References]:
    _verify_formulas(source)
    sheets = _workbook_sheets(source)
    if len(sheets) != 1:
        raise ValueError("Esperada uma aba na planilha dos cinco ímãs")
    sheet = next(iter(sheets.values()))
    header = ("Lado", "X nominal (mm)", "Y (mm)", "N leituras", "Média ADC",
              "Tensão média calculada (V)")
    if tuple(sheet[4].get(chr(65 + i)) for i in range(6)) != header:
        raise ValueError("Cabeçalhos inesperados na grade")
    points = []
    for number in range(5, 35):
        row = sheet[number]
        side, x_mm, y_mm = row["A"], int(row["B"]), int(row["C"])
        count, mean_adc, voltage = int(row["D"]), float(row["E"]), float(row["F"])
        if side not in SIDES or x_mm not in X_MM or y_mm not in Y_MM:
            raise ValueError(f"Coordenada inesperada na linha {number}")
        if count <= 0 or not 0 <= mean_adc <= 1023:
            raise ValueError(f"ADC ou contagem inválido na linha {number}")
        _close(count * mean_adc, round(count * mean_adc), f"média ADC linha {number}", 1e-6)
        _close(voltage, mean_adc * ADC_TO_V, f"tensão linha {number}")
        points.append(Position(side, x_mm, y_mm, count, mean_adc, voltage))
    expected_keys = {(side, x_mm, y_mm) for side in SIDES for x_mm in X_MM for y_mm in Y_MM}
    if len(points) != 30 or {(p.side, p.x_mm, p.y_mm) for p in points} != expected_keys:
        raise ValueError("Esperadas 30 posições distintas")
    start, end, change = sheet[39], sheet[40], sheet[41]
    if not str(start["A"]).startswith("Inicial escolhida") or not str(end["A"]).startswith("Final"):
        raise ValueError("Referências sem ímã inesperadas")
    references = References(int(start["B"]), float(start["C"]),
                            int(end["B"]), float(end["C"]))
    if references.initial_count <= 0 or references.final_count <= 0:
        raise ValueError("Contagem de referência inválida")
    for number, count, adc in ((39, references.initial_count, references.initial_adc),
                               (40, references.final_count, references.final_adc)):
        _close(count * adc, round(count * adc), f"referência ADC linha {number}", 1e-6)
        _close(float(sheet[number]["D"]), adc * ADC_TO_V, f"referência V linha {number}")
    _close(float(change["C"]), references.final_adc - references.initial_adc, "deriva ADC")
    _close(float(change["D"]), references.drift_v, "deriva V")
    if "inferida como ADC 533" not in str(sheet[43]["A"]):
        raise ValueError("Nota de inferência da referência final ausente")
    return points, references


def five_magnet_field_t(side: str, x_mm: int, y_mm: int) -> float:
    """Cinco cuboides contíguos pelas bordas longas; mesmo vetor local +Z.

    A foto mostra a fileira ao longo de X e o Hall fixo perto de X=0.
    Como convenção de cálculo, X nominal é a lacuna até a peça mais próxima;
    As faces se tocam no modelo, conforme confirmado pelo experimentador.
    A posição interna do elemento sensível não foi medida.
    """
    setup = mounting_setup(side, x_mm, MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM)
    width_m = dimensions_for()[1]
    field = 0.0
    for index in range(MAGNET_COUNT):
        magnet = setup.magnet.copy()
        magnet.position = np.asarray(setup.magnet.position) + (
            index * width_m, -y_mm / 1000, 0.0)
        local_field = np.asarray(magpy.getB(magnet, setup.sensor), dtype=float)
        field += float(np.dot(local_field, AXES_LOCAL["vertical_z"]))
    return field


def comparison_rows(points: list[Position], refs: References) -> list[dict[str, object]]:
    rows = []
    middle_adc = (refs.initial_adc + refs.final_adc) / 2
    for point in points:
        model_field_t = five_magnet_field_t(point.side, point.x_mm, point.y_mm)
        predicted_v = PREVIOUS_SCALE_V_PER_T * model_field_t
        delta_initial_v = (point.mean_adc - refs.initial_adc) * ADC_TO_V
        delta_final_v = (point.mean_adc - refs.final_adc) * ADC_TO_V
        delta_middle_v = (point.mean_adc - middle_adc) * ADC_TO_V
        rows.append({
            "side": point.side, "x_mm": point.x_mm, "y_mm": point.y_mm,
            "count": point.count, "mean_adc": point.mean_adc,
            "mean_voltage_v": point.voltage_v,
            "reference_initial_voltage_v": refs.initial_adc * ADC_TO_V,
            "reference_final_voltage_v": refs.final_adc * ADC_TO_V,
            "delta_initial_v": delta_initial_v, "delta_final_v": delta_final_v,
            "delta_middle_v": delta_middle_v,
            "model_field_reference_t": model_field_t,
            "model_delta_v": predicted_v,
            "predicted_voltage_initial_v": refs.initial_adc * ADC_TO_V + predicted_v,
            "predicted_voltage_final_v": refs.final_adc * ADC_TO_V + predicted_v,
            "residual_initial_v": delta_initial_v - predicted_v,
            "residual_final_v": delta_final_v - predicted_v,
            "residual_middle_v": delta_middle_v - predicted_v,
            "reference_effect_on_residual_v": -refs.drift_v,
            "distance_to_reference_band_v": max(delta_initial_v - predicted_v,
                                                0.0, predicted_v - delta_final_v),
        })
    return rows


def _metric(rows: list[dict[str, object]], key: str) -> tuple[float, float]:
    errors = np.asarray([row[key] for row in rows], dtype=float)
    return float(np.mean(np.abs(errors))), float(np.sqrt(np.mean(errors**2)))


def plot_maps(rows: list[dict[str, object]], target: Path) -> None:
    by_key = {(r["side"], r["x_mm"], r["y_mm"]): r for r in rows}
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.5), layout="constrained")
    limit = max(abs(float(r[key])) for r in rows
                for key in ("delta_middle_v", "model_delta_v", "residual_middle_v"))
    for index, side in enumerate(SIDES):
        for column, (key, title) in enumerate((
            ("delta_middle_v", "ΔV com referência intermediária (V)"),
            ("model_delta_v", "Modelo de cinco ímãs (V)"),
            ("residual_middle_v", "Resíduo intermediário (V)"),
        )):
            matrix = [[by_key[(side, x, y)][key] for y in Y_MM] for x in X_MM]
            ax = axes[index, column]
            image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="RdBu_r",
                              vmin=-limit, vmax=limit)
            ax.set(xticks=range(3), xticklabels=Y_MM, yticks=range(5), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)", title=f"{side}: {title}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="V")
    fig.suptitle("Cinco ímãs · cenário geométrico explícito · mesma escala de cor")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def plot_curves(rows: list[dict[str, object]], target: Path) -> None:
    by_key = {(r["side"], r["x_mm"], r["y_mm"]): r for r in rows}
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7), layout="constrained", sharex=True)
    for i, side in enumerate(SIDES):
        for j, y in enumerate(Y_MM):
            selected = [by_key[(side, x, y)] for x in X_MM]
            ax = axes[i, j]
            lower = [r["delta_initial_v"] for r in selected]
            upper = [r["delta_final_v"] for r in selected]
            ax.fill_between(X_MM, lower, upper, alpha=0.25, color="#137d91",
                            label="Faixa das referências")
            ax.plot(X_MM, [r["delta_middle_v"] for r in selected], "o-",
                    color="#137d91", label="Referência intermediária")
            ax.plot(X_MM, [r["model_delta_v"] for r in selected], "s--",
                    color="#bd4c28", label="Modelo sem reajuste")
            ax.axhline(0, color="#777", linewidth=0.8)
            ax.grid(alpha=0.22)
            ax.set(title=f"{side}, Y={y:+d} mm", xlabel="X nominal (mm)", ylabel="ΔV (V)")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Faixa de ΔV pela deriva da referência · sem interpolação temporal")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_schematic(target: Path) -> None:
    """Desenha a hipótese de alinhamento, não uma planta medida da montagem."""
    blocks = "".join(
        f'<rect x="{390 + 65*i}" y="135" width="63" height="180" class="magnet"/>'
        f'<text x="{421 + 65*i}" y="230" text-anchor="middle">{i+1}</text>'
        for i in range(MAGNET_COUNT)
    )
    target.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="920" height="440" viewBox="0 0 920 440">
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0 L9 3 L0 6 Z" fill="#087e8b"/></marker></defs>
<style>text{{font:17px sans-serif;fill:#172c3b}}.small{{font:14px sans-serif}}.magnet{{fill:#dbe8f5;stroke:#174b75;stroke-width:2}}.axis{{stroke:#555;stroke-width:2;marker-end:url(#arrow)}}.move{{stroke:#087e8b;stroke-width:4;marker-end:url(#arrow)}}</style>
<text x="30" y="35">Vista superior X–Y: cenário Magpylib, não escala nem fotografia</text>
<rect x="100" y="185" width="15" height="80" fill="#202734"/><text x="55" y="165">Hall fixo</text>
{blocks}
<line x1="360" y1="95" x2="185" y2="95" class="move"/><text x="185" y="79">aproximação em −X</text>
<line x1="130" y1="360" x2="295" y2="360" class="axis"/><text x="300" y="365">+X</text>
<line x1="130" y1="360" x2="130" y2="285" class="axis"/><text x="137" y="290">+Y</text>
<text x="405" y="345" class="small">comprimentos paralelos a Y; centros separados por 9,40 mm em X</text>
<text x="30" y="405" class="small">Z é vertical: espessura deitada sobre a superfície. Lado 2: giro rígido das peças e da polarização local.</text>
</svg>''', encoding="utf-8")


def write_outputs(source: Path, output: Path, points: list[Position], refs: References) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows = comparison_rows(points, refs)
    with (output / f"{STEM}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        keys = ("side", "x_mm", "y_mm", "count", "mean_adc", "mean_voltage_v",
                "delta_initial_v", "delta_final_v", "delta_middle_v",
                "model_field_reference_t", "model_delta_v", "residual_initial_v",
                "residual_final_v", "residual_middle_v", "distance_to_reference_band_v")
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm", "n", "media_adc",
                         "tensao_media_medida_v", "delta_v_referencia_inicial_v",
                         "delta_v_referencia_final_v", "delta_v_referencia_intermediaria_ilustrativa_v",
                         "bz_modelo_referencia_1t_t_nao_medido",
                         "delta_v_modelo_cinco_imans_escala_fixa_v",
                         "residuo_referencia_inicial_v", "residuo_referencia_final_v",
                         "residuo_referencia_intermediaria_v", "distancia_modelo_faixa_referencias_v"))
        for row in rows:
            writer.writerow([row[key] if key in ("side", "x_mm", "y_mm", "count")
                             else f"{row[key]:.12f}" for key in keys])
    with (output / f"{STEM}-ponto-a-ponto.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.writer(stream)
        keys = ("side", "x_mm", "y_mm", "mean_voltage_v",
                "reference_initial_voltage_v", "predicted_voltage_initial_v",
                "residual_initial_v", "reference_final_voltage_v",
                "predicted_voltage_final_v", "residual_final_v",
                "reference_effect_on_residual_v", "distance_to_reference_band_v")
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm",
                         "tensao_media_medida_v", "referencia_sem_ima_inicial_v",
                         "tensao_total_prevista_ref_inicial_v", "residuo_ref_inicial_v",
                         "referencia_sem_ima_final_v", "tensao_total_prevista_ref_final_v",
                         "residuo_ref_final_v", "mudanca_residuo_ao_usar_ref_final_v",
                         "distancia_modelo_faixa_referencias_v"))
        for row in rows:
            writer.writerow([row[key] if key in ("side", "x_mm", "y_mm")
                             else f"{row[key]:.12f}" for key in keys])
    plot_maps(rows, output / f"{STEM}-mapas.png")
    plot_curves(rows, output / f"{STEM}-curvas.png")
    write_schematic(output / f"{STEM}-esquema.svg")
    counts = sum(point.count for point in points)
    middle_mae, middle_rmse = _metric(rows, "residual_middle_v")
    initial_mae, initial_rmse = _metric(rows, "residual_initial_v")
    final_mae, final_rmse = _metric(rows, "residual_final_v")
    band_mae, band_rmse = _metric(rows, "distance_to_reference_band_v")
    in_band = sum(row["distance_to_reference_band_v"] < 1e-12 for row in rows)
    by_key = {(row["side"], row["x_mm"], row["y_mm"]): row for row in rows}
    lines = [
        "# Nova coleta Hall: fileira de cinco ímãs", "",
        f"Fonte preservada: [mapeamento_cinco_imans.xlsx]"
        f"(../../experiments/hall-sensor/{source.name}), SHA-256 "
        f"`{hashlib.sha256(source.read_bytes()).hexdigest()}`. São **30 médias ADC** "
        f"de blocos que resumem **{counts} leituras com ímãs**. A planilha "
        "não contém essas leituras individuais. Todos os 30 valores de "
        "`tensão média = média ADC × 5/1023 V`, suas fórmulas e caches, "
        "consistência interna das contagens, referências e variação "
        "final–inicial foram conferidas. Sem as leituras individuais, não "
        "é possível auditar as médias nem as contagens de cada bloco. "
        "A tensão de 5 V é nominal, conforme a própria planilha.", "",
        "## Referência sem ímã e deriva", "",
        f"Referência inicial escolhida: **{refs.initial_adc:.6f} ADC** "
        f"({refs.initial_count} leituras; {refs.initial_adc*ADC_TO_V:.6f} V). "
        f"Referência final: **{refs.final_adc:.6f} ADC** "
        f"({refs.final_count} leituras; {refs.final_adc*ADC_TO_V:.6f} V). "
        f"Mudança final–inicial: **{refs.final_adc-refs.initial_adc:+.6f} ADC** "
        f"ou **{refs.drift_v:+.6f} V**. A nota da planilha diz que a "
        "primeira linha do bloco final estava cortada e foi **inferida como "
        "ADC 533** a partir da tensão exibida de cerca de 2,605 V; assim, a referência final "
        "e a deriva não são inteiramente observações diretas.", "",
        "Como não há horário por posição, calculamos ΔV com **ambas as "
        "referências**, sem atribuir uma evolução temporal a cada média. "
        "A faixa entre elas é um cenário de deriva entre os dois valores "
        "registrados, não um intervalo de confiança nem garantia de que "
        "a referência sempre ficou dentro dela. A referência intermediária "
        "é a média aritmética dos extremos, usada somente para mapas e "
        "métricas descritivas. Nenhum campo em mT é inferido dos dados Hall.", "",
        "## Modelo Magpylib sem novo ajuste", "",
        f"[Esquema dos eixos e da fileira assumida]({STEM}-esquema.svg). "
        "É uma vista de cálculo; não representa distâncias físicas medidas.", "",
        "**Disposição informada pelo experimentador:** cinco ímãs lado a "
        "lado pelos comprimentos, deitados pela espessura. Para representá-la, "
        "usamos cinco cuboides idênticos com as dimensões médias dos dez "
        "ímãs (19,37 × 9,40 × 4,48 mm), comprimentos paralelos a +Y global, "
        "espessuras verticais, bordas longas contíguas **sem espaço entre as "
        "faces, conforme confirmado pelo experimentador**, centros separados "
        "pela largura média de **9,40 mm** ao longo de +X global. "
        "A **foto da montagem** mostra o Hall fixo junto à marca X=0 e a "
        "fileira seguindo o eixo de aproximação X; as marcas Y indicam "
        "deslocamentos laterais. O código coloca os cinco centros em +X e "
        "move a fileira em −X quando X nominal diminui. Como **convenção "
        "não medida**, X nominal é a lacuna entre o ponto sensível modelado "
        "e a borda da peça mais próxima; não se conhece a distância real "
        "até o elemento interno. A separação entre faces é zero, mas "
        "as larguras individuais das cinco peças não foram identificadas. "
        "Y nominal desloca a "
        "fileira lateralmente. Foram registradas as posições nominais "
        "X = 5, 10, 20, 30 e 50 mm e Y = −10, 0 e +10 mm. Isso não "
        "identifica quais peças foram usadas. "
        "Para o lado 2, as cinco peças giram "
        "rigidamente com seu vetor local de polarização +Z. Todos os "
        "vetores locais +Z iguais são hipótese provisória de magnetização "
        "através da espessura; não conhecemos a direção nem a intensidade "
        "reais, nem se os cinco ímãs tinham polos alinhados.", "",
        "Reutilizamos o cenário anterior: centro do ímã a 2,24 mm da "
        "superfície como convenção geométrica, Hall na mesma altura relativa, "
        "deslocamento nominal–físico de 0 mm, projeção candidata `vertical_z` "
        f"e escala elétrica fixa **{PREVIOUS_SCALE_V_PER_T:+.6f} V/T** "
        "de campo de referência para polarização matemática de 1 T. "
        "Essa escala efetiva veio do ensaio anterior com um único ímã; "
        "sua transferência para cinco peças pressupõe resposta elétrica "
        "comparável e magnetizações semelhantes, sem confirmação. "
        "Esses valores não foram reajustados à nova coleta nem são "
        "medidas de altura, zero físico, sensibilidade ou magnetização. "
        "O campo calculado do modelo é mostrado em T de referência, não "
        "como mT medidos pelo Hall.", "",
        "### Auditoria da geometria implementada", "",
        "| Aspecto | Código atual | Registro experimental |",
        "| --- | --- | --- |",
        "| Dimensões | Cinco cuboides iguais de 19,37 × 9,40 × 4,48 mm, média de dez peças dimensionadas | Não há identificação dimensional individual das cinco peças usadas |",
        "| Centros e espaçamento | `x = X_nominal + 4,70 + (0, 9,40, 18,80, 28,20, 37,60) mm`; `y = −Y_nominal`; `z = 2,24 mm`; separação entre faces = 0 | Foto mostra a sequência em X, Hall junto a X=0 e Y lateral; contato entre faces confirmado pelo experimentador; distância ao elemento interno desconhecida |",
        "| Lado 1 | Comprimento local X → +Y global; largura local Y → −X; espessura local Z → +Z | Eixos longos transversais à sequência de aproximação X na foto; face de apoio visível |",
        "| Lado 2 | Giro rígido de 180° em torno do comprimento de cada peça: X local → +Y, Y local → +X, Z local → −Z; Hall fixo | A descrição do ensaio anterior com um ímã diz que a face apoiada ficou para cima; a nova planilha não registra como as cinco peças foram viradas nem sua ordem depois do giro |",
        "| Magnetização | Cada cuboide tem `polarization=(0,0,+1)` T **local** como referência; o giro leva o vetor junto; as cinco contribuições são somadas | Polaridade, intensidade e uniformidade de cada peça não foram medidas |",
        "| Leitura | Componente candidata vertical global `vertical_z`; escala elétrica −12,320751 V/T herdada do ensaio de um ímã | Eixo sensível, altura e distância física do elemento Hall não foram medidos nesta coleta |", "",
        "O código mantém os cinco centros em +X ao gerar cada lado. Uma "
        "virada física da fileira como conjunto inverteria a ordem das "
        "peças; como os cinco cuboides do cenário são idênticos, essa "
        "permutação não altera o campo calculado, mas pode importar para "
        "cinco ímãs reais distintos. A **foto enviada pelo experimentador "
        "nesta conversa** mostra cinco barras com eixos longos paralelos e "
        "faces maiores voltadas para cima, em sequência na direção X. O "
        "módulo Hall está parado próximo à marca X=0; as marcas Y são "
        "laterais. Assim, a disposição geral implementada coincide com a "
        "foto, e **nenhuma posição de cuboide foi alterada** nesta revisão. "
        "A imagem não mede altura, posição interna do Hall ou "
        "polaridade das peças; também não estabelece a correspondência "
        "entre a face fotografada e os lados da planilha. A convenção de "
        "sinal `y = −Y_nominal` e a projeção `vertical_z` continuam "
        "hipóteses, não orientações sensíveis comprovadas. Esta foto não "
        "foi arquivada no repositório.", "",
        "### Sinal elétrico e eixo candidato", "",
        "O sensor foi identificado pelo experimentador como **Honeywell SS49E**. "
        f"A [ficha técnica Honeywell]({SS49E_DATASHEET}) (tabela 1, figura 2 "
        "e desenho de polaridade) descreve resposta linear bipolar: o "
        "campo em um sentido aumenta a tensão em relação ao nulo; no "
        "sentido oposto a diminui. Na aproximação observada, a tensão "
        "**sobe no lado 1 e desce no lado 2**. Com a referência intermediária "
        "apenas ilustrativa, os três pontos de X=50 mm do lado 1 ainda "
        "ficam ligeiramente abaixo dela; o aumento descreve a tendência "
        "ao aproximar, não o sinal de cada ΔV contra toda referência. "
        "No cenário calculado, `vertical_z` é a componente **+Z global** "
        "(vertical à superfície), não o eixo X da trajetória. A "
        "polarização local +Z de referência produz componente modelada "
        "negativa no lado 1 e positiva no lado 2; a escala efetiva "
        f"**{PREVIOUS_SCALE_V_PER_T:+.6f} V/T** inverte esses sinais e "
        "resulta em ΔV calculado positivo no lado 1 e negativo no lado 2 "
        "nas 30 posições. O sinal dessa escala depende do referencial e "
        "da polarização de referência escolhidos; não é uma medição do "
        "sinal físico da sensibilidade do SS49E. A foto mostra o "
        "encapsulamento junto a X=0, mas não fixa o eixo sensível "
        "do chip em relação a +Z, nem os polos dos cinco ímãs.", "",
        "## Comparação em volts", "",
        f"[Tabela ponto a ponto com as duas referências]({STEM}-ponto-a-ponto.csv) · "
        f"[Tabela de ΔV e campo de referência do modelo]({STEM}.csv) · "
        f"[Mapas]({STEM}-mapas.png) · "
        f"[Curvas com faixa de referência]({STEM}-curvas.png). "
        "Resíduo = ΔV observado sob cada referência − ΔV calculado pelo "
        "modelo. `Distância modelo–faixa` vale zero se o modelo cair entre "
        "os dois ΔV extremos; caso contrário, é a distância até o extremo "
        "mais próximo. A série intermediária não corrige a deriva.", "",
        "| Referência aplicada | Posições | MAE (V) | RMSE (V) |",
        "| --- | ---: | ---: | ---: |",
        f"| Inicial | 30 | {initial_mae:.6f} | {initial_rmse:.6f} |",
        f"| Final | 30 | {final_mae:.6f} | {final_rmse:.6f} |",
        f"| Intermediária ilustrativa | 30 | {middle_mae:.6f} | {middle_rmse:.6f} |", "",
        "| Lado, referência intermediária | Posições | MAE (V) | RMSE (V) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for side in SIDES:
        side_rows = [row for row in rows if row["side"] == side]
        mae, rmse = _metric(side_rows, "residual_middle_v")
        lines.append(f"| {side} | 15 | {mae:.6f} | {rmse:.6f} |")
    lines += ["",
        f"Mesmo escolhendo, para cada posição, o extremo de referência "
        f"mais favorável ao modelo, a distância à faixa tem MAE "
        f"**{band_mae:.6f} V** e RMSE **{band_rmse:.6f} V**. "
        f"O modelo cai na faixa das duas referências em **{in_band}/30** "
        "posições. Isso descreve apenas este cenário geométrico e de "
        "deriva; não identifica a montagem real.", "",
    ]
    for side in SIDES:
        center = by_key[(side, 5, 0)]
        edge = by_key[(side, 5, 10)]
        lines.append(f"- {side}, X=5 mm: no centro Y=0, ΔV intermediário "
                     f"{center['delta_middle_v']:+.6f} V versus modelo "
                     f"{center['model_delta_v']:+.6f} V; em Y=+10 mm, "
                     f"{edge['delta_middle_v']:+.6f} V versus "
                     f"{edge['model_delta_v']:+.6f} V.")
    compatible = [row for row in rows if row["distance_to_reference_band_v"] < 1e-12]
    near = [row for row in rows if row["x_mm"] == 5]
    lines += ["", "### Tensão medida, tensão prevista e referência por posição", "",
              "`V_prevista = V_referência_sem_ímã + ΔV_modelo`; "
              "`resíduo = V_medida − V_prevista`. As letras `i` e `f` "
              "indicam as referências inicial e final. Trocar somente a "
              f"referência de **{refs.initial_adc*ADC_TO_V:.6f}** para "
              f"**{refs.final_adc*ADC_TO_V:.6f} V** diminui a tensão total "
              f"prevista e aumenta **cada** resíduo em "
              f"**{-refs.drift_v:.6f} V**. Isso é uma análise dos dois "
              "cenários de referência, não uma correção temporal conhecida.", "",
              "| Lado | X | Y | V medida | V ref. i | V prevista i | Resíduo i | V ref. f | V prevista f | Resíduo f |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(f"| {row['side']} | {row['x_mm']} | {row['y_mm']:+d} | "
                     f"{row['mean_voltage_v']:.6f} | "
                     f"{row['reference_initial_voltage_v']:.6f} | "
                     f"{row['predicted_voltage_initial_v']:.6f} | "
                     f"{row['residual_initial_v']:+.6f} | "
                     f"{row['reference_final_voltage_v']:.6f} | "
                     f"{row['predicted_voltage_final_v']:.6f} | "
                     f"{row['residual_final_v']:+.6f} |")
    lines += ["", "### O que cabe na deriva registrada", "",
              f"Em **{len(compatible)}/30** posições, a previsão fica entre "
              "as duas tensões calculadas com as referências registradas: "
              + ", ".join(f"{row['side']}, X={row['x_mm']}, Y={row['y_mm']:+d} mm"
                          for row in compatible) + ". "
              f"Nas outras **{len(rows)-len(compatible)}/30**, a escolha "
              "entre esses dois extremos não elimina o resíduo do cenário. "
              f"Em X=5 mm, a menor distância do modelo à faixa é "
              f"**{min(row['distance_to_reference_band_v'] for row in near):.6f} V**, "
              f"muito acima dos **{-refs.drift_v:.6f} V** de mudança de "
              "referência. Para sinais pequenos em X=50 mm, essa mudança "
              "pode ser da mesma ordem da resposta. A faixa dos dois valores "
              "não é intervalo de confiança e não garante que a linha de "
              "base real permaneceu entre eles; portanto, a classificação "
              "não prova a causa de cada discrepância.", "",
              "### Verificação mínima antes de repetir a grade", "",
              "A maior incerteza física é a pose relativa da fileira e do "
              "elemento Hall: qual borda fica próxima, larguras individuais, "
              "altura e significado físico de X=5 mm e Y=0. Também faltam "
              "o eixo sensível do Hall e a orientação/polaridade de cada "
              "ímã; a escala herdada de um único ímã não substitui essas "
              "informações. A foto já recebida mostra a disposição geral; "
              "antes de uma grade completa, registre **uma foto da posição "
              "real de medição com régua e vista lateral**, marcando a "
              "borda mais próxima, o elemento Hall e o sentido de X/Y. "
              "Marque o sentido de polo de cada peça com uma referência "
              "simples, sem tratar essa checagem como medida de intensidade. "
              "Depois faça apenas **três posições em X=5 mm, lado 1, "
              "Y=−10, 0, +10 mm**, com leitura sem ímã imediatamente "
              "antes e depois, guardando ADC individual e horário. Esse "
              "perfil curto testa o maior desacordo lateral e separa "
              "melhor uma mudança de referência de uma mudança de forma "
              "espacial; se persistir, confirme a pose e os polos antes "
              "de repetir as 30 posições.", "",
        "## Limitações", "",
        "Sem ordem temporal das médias, leituras individuais, posição física "
        "do Hall, geometria real da fileira, orientação sensível confirmada "
        "e caracterização de cada magnetização, o resíduo não separa "
        "deriva elétrica, diferenças entre os ímãs e erro de geometria. "
        "A conversão `ΔV/14 mV/mT` não foi aplicada: além de ser uma "
        "sensibilidade típica e não calibração individual, o ΔV por posição "
        "depende da referência incerta durante esta coleta. "
        "A planilha e todos os resultados das coletas anteriores foram "
        "preservados.", "",
        "Reproduza com `.\\.venv\\Scripts\\python.exe "
        "simulation/magnetic-field/src/hall_five_magnets.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    points, refs = load_collection(args.source)
    write_outputs(args.source, args.output, points, refs)
    print(f"{len(points)} médias conferidas; deriva {refs.drift_v:+.6f} V; sem ajuste")


if __name__ == "__main__":
    main()
