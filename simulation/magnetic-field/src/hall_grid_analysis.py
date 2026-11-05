"""Confere a grade Hall e compara suas 30 posições com o modelo horizontal existente."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import magpylib as magpy
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from compare_hall_mountings import AXES_LOCAL, mounting_setup
from hall_analysis import ROOT, _workbook_sheets


SOURCE = ROOT / "data" / "experiments" / "hall-sensor" / "mapeamento_hall_grade.xlsx"
REVISED_SOURCE = ROOT / "data" / "experiments" / "hall-sensor" / "mapeamento_hall_grade_revisado_x5.xlsx"
OUTPUT = ROOT / "data" / "processed" / "hall-sensor"
SIDES = ("Lado 1", "Lado 2")
X_MM = (5, 10, 20, 30, 50)
Y_MM = (-10, 0, 10)
ADC_VREF_V = 5.0  # conversão nominal inscrita na planilha, não alimentação aferida
ADC_MAX = 1023
SENSITIVITY_MV_PER_MT = 14.0  # SS49E Honeywell típico, sem calibração individual
# Valor publicado em comparacao-horizontal.md para vertical_z; NÃO reajustar com a grade.
PREVIOUS_SCALE_V_PER_T = -12.320751
MODEL_SENSOR_HEIGHT_MM = 2.24  # cenário anterior: centro do ímã, não altura medida
MODEL_ZERO_OFFSET_MM = 0.0  # cenário anterior: lacuna física = X nominal, não medida
STEM = "mapeamento-hall-horizontal"


@dataclass(frozen=True)
class GridPoint:
    side: str
    x_mm: int
    y_mm: int
    count: int
    mean_adc: float
    reference_adc: float
    mean_voltage_v: float
    delta_v_mv: float
    estimated_field_mt: float
    note: str


def _close(actual: float, expected: float, label: str, atol: float = 1e-9) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=atol):
        raise ValueError(f"Cálculo divergente em {label}: {actual} ≠ {expected}")


def load_grid(source: Path = SOURCE) -> tuple[list[GridPoint], dict[str, tuple[int, int, float]]]:
    """Lê caches do XLSX e refaz a aritmética sem modificar a planilha."""
    sheets = _workbook_sheets(source)
    original_tabs = {"Mapa", "Médias por posição"}
    if set(sheets) not in (original_tabs, original_tabs | {"Reteste X5"}):
        raise ValueError("Esperadas as abas Mapa e Médias por posição, com Reteste X5 opcional")
    retest_rows = sheets.get("Reteste X5")
    map_rows = sheets["Mapa"]
    detail_rows = sheets["Médias por posição"]
    expected_header = ("Lado", "X (mm)", "Y (mm)", "n", "Média ADC",
                       "Referência início (ADC)", "Referência fim (ADC)",
                       "Referência aplicada (ADC)", "Tensão média (V)",
                       "ΔV (mV)", "Campo estimado (mT)", "Observação")
    if tuple(detail_rows[1].get(chr(65 + column)) for column in range(12)) != expected_header:
        raise ValueError("Cabeçalhos inesperados na grade")
    if tuple(map_rows[11].get(column) for column in ("B", "C", "D", "G", "H", "I")) != (
        "Y = −10 mm", "Y = 0 mm", "Y = +10 mm",
        "Y = −10 mm", "Y = 0 mm", "Y = +10 mm",
    ):
        raise ValueError("Cabeçalhos Y inesperados na aba Mapa")
    references = {}
    for side, row_number in zip(SIDES, (6, 7)):
        row = map_rows[row_number]
        if row["A"] != side:
            raise ValueError("Lado inesperado na referência")
        start_n, end_n = int(row["B"]), int(row["D"])
        if start_n <= 0 or end_n <= 0:
            raise ValueError("Contagem de referência inválida")
        start_adc, end_adc = float(row["C"]), float(row["E"])
        applied = (start_adc + end_adc) / 2  # médias de blocos, não média ponderada
        _close(float(row["F"]), applied, f"referência {side}")
        references[side] = (start_n, end_n, applied)
    if retest_rows is not None:
        initial = retest_rows[5]
        final = retest_rows[6]
        retest_start = float(initial["C"])
        retest_end = float(final["C"])
        retest_reference = (retest_start + retest_end) / 2
        _close(float(retest_rows[7]["C"]), retest_reference, "referência do reteste")
        if int(initial["B"]) <= 0 or int(final["B"]) <= 0:
            raise ValueError("Contagem de referência do reteste inválida")
    points = []
    for number in range(2, 32):
        row = detail_rows.get(number)
        if row is None:
            raise ValueError(f"Falta a posição da linha {number}")
        side, x_mm, y_mm = row["A"], int(row["B"]), int(row["C"])
        if side not in SIDES or x_mm not in X_MM or y_mm not in Y_MM:
            raise ValueError(f"Posição inesperada na linha {number}")
        count, mean_adc = int(row["D"]), float(row["E"])
        if count <= 0 or not 0 <= mean_adc <= ADC_MAX:
            raise ValueError(f"Contagem ou média ADC inválida na linha {number}")
        if not math.isclose(count * mean_adc, round(count * mean_adc), abs_tol=1e-6):
            raise ValueError(f"Média ADC incompatível com leituras inteiras na linha {number}")
        if retest_rows is not None and x_mm == 5:
            start_adc, end_adc, reference_adc = retest_start, retest_end, retest_reference
        else:
            reference_row = map_rows[6 if side == SIDES[0] else 7]
            start_adc, end_adc = float(reference_row["C"]), float(reference_row["E"])
            reference_adc = references[side][2]
        _close(float(row["F"]), start_adc, f"início linha {number}")
        _close(float(row["G"]), end_adc, f"fim linha {number}")
        _close(float(row["H"]), reference_adc, f"referência linha {number}")
        mean_voltage_v = mean_adc * ADC_VREF_V / ADC_MAX
        delta_v_mv = (mean_adc - reference_adc) * ADC_VREF_V / ADC_MAX * 1000
        estimated_field_mt = delta_v_mv / SENSITIVITY_MV_PER_MT
        _close(float(row["I"]), mean_voltage_v, f"tensão linha {number}")
        _close(float(row["J"]), delta_v_mv, f"ΔV linha {number}")
        _close(float(row["K"]), estimated_field_mt, f"campo linha {number}")
        points.append(GridPoint(side, x_mm, y_mm, count, mean_adc, reference_adc,
                                mean_voltage_v, delta_v_mv, estimated_field_mt,
                                row.get("L", "")))
    keys = [(point.side, point.x_mm, point.y_mm) for point in points]
    expected = {(side, x_mm, y_mm) for side in SIDES for x_mm in X_MM for y_mm in Y_MM}
    if len(points) != 30 or len(set(keys)) != 30 or set(keys) != expected:
        raise ValueError("A grade deve conter exatamente 30 posições distintas")
    by_key = {key: point for key, point in zip(keys, points)}
    for row_number, x_mm in enumerate(X_MM, start=12):
        row = map_rows[row_number]
        if int(row["A"]) != x_mm or int(row["F"]) != x_mm:
            raise ValueError("Eixo X divergente na aba Mapa")
        for side, columns in ((SIDES[0], ("B", "C", "D")),
                              (SIDES[1], ("G", "H", "I"))):
            for y_mm, column in zip(Y_MM, columns):
                _close(float(row[column]), by_key[(side, x_mm, y_mm)].estimated_field_mt,
                       f"Mapa {side}, X={x_mm}, Y={y_mm}")
    if retest_rows is not None:
        original_points, _ = load_grid(SOURCE)
        old_by_key = {(point.side, point.x_mm, point.y_mm): point for point in original_points}
        distributions: dict[tuple[str, int, int], list[tuple[int, int]]] = {}
        for row_number in range(23, 37):
            row = retest_rows[row_number]
            key = (row["B"], int(row["C"]), int(row["D"]))
            distributions.setdefault(key, []).append((int(row["E"]), int(row["F"])))
        if set(distributions) != {(side, 5, y_mm) for side in SIDES for y_mm in Y_MM}:
            raise ValueError("Distribuições do reteste incompletas")
        for row_number, reference_group in ((5, range(18, 20)), (6, range(20, 23))):
            distribution = [(int(retest_rows[n]["E"]), int(retest_rows[n]["F"]))
                            for n in reference_group]
            count = sum(frequency for _, frequency in distribution)
            mean = sum(adc * frequency for adc, frequency in distribution) / count
            if count != int(retest_rows[row_number]["B"]):
                raise ValueError("Contagem de referência do reteste divergente")
            _close(mean, float(retest_rows[row_number]["C"]), "distribuição da referência")
        for point in points:
            key = (point.side, point.x_mm, point.y_mm)
            old = old_by_key[key]
            if point.x_mm != 5:
                if point != old:
                    raise ValueError(f"Posição não retestada alterada: {key}")
                continue
            row_number = 10 + SIDES.index(point.side) * 3 + Y_MM.index(point.y_mm)
            row = retest_rows[row_number]
            if (row["A"], int(row["B"]), int(row["C"])) != key:
                raise ValueError(f"Chave de reteste divergente: {key}")
            distribution = distributions[key]
            count = sum(frequency for _, frequency in distribution)
            mean = sum(adc * frequency for adc, frequency in distribution) / count
            if count != point.count or count != int(row["D"]):
                raise ValueError(f"Contagem de reteste divergente: {key}")
            _close(mean, point.mean_adc, f"distribuição {key}")
            _close(float(row["E"]), point.mean_adc, f"média reteste {key}")
            if int(row["F"]) != old.count:
                raise ValueError(f"Contagem histórica divergente: {key}")
            _close(float(row["G"]), old.mean_adc, f"média histórica {key}")
            _close(float(row["H"]), point.mean_adc - old.mean_adc, f"Δ ADC {key}")
            for column, value in (("I", point.reference_adc), ("J", point.mean_voltage_v),
                                  ("K", point.delta_v_mv), ("L", point.estimated_field_mt)):
                _close(float(row[column]), value, f"Reteste {key} coluna {column}")
    return points, references


def model_reference_field_t(side: str, x_mm: int, y_mm: int) -> float:
    """Bz do cenário anterior; Hall fixo e centro do ímã em Y_global = −Y_grade."""
    setup = mounting_setup(side, x_mm, MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM)
    setup.magnet.position = np.asarray(setup.magnet.position) + (0, -y_mm / 1000, 0)
    field_local = np.asarray(magpy.getB(setup.magnet, setup.sensor), dtype=float)
    return float(np.dot(field_local, AXES_LOCAL["vertical_z"]))


def comparison_rows(points: list[GridPoint]) -> list[dict[str, object]]:
    rows = []
    for point in points:
        b_reference_t = model_reference_field_t(point.side, point.x_mm, point.y_mm)
        predicted_v = PREVIOUS_SCALE_V_PER_T * b_reference_t
        rows.append({
            "side": point.side, "x_mm": point.x_mm, "y_mm": point.y_mm,
            "count": point.count, "mean_adc": point.mean_adc,
            "reference_adc": point.reference_adc,
            "mean_voltage_v": point.mean_voltage_v,
            "delta_v_observed_v": point.delta_v_mv / 1000,
            "field_estimated_mt": point.estimated_field_mt,
            "bz_reference_mt": b_reference_t * 1000,
            "delta_v_model_v": predicted_v,
            "residual_v": point.delta_v_mv / 1000 - predicted_v,
            "field_model_effective_mt": predicted_v * 1000 / SENSITIVITY_MV_PER_MT,
            "note": point.note,
        })
    return rows


def _matrix(rows: list[dict[str, object]], side: str, key: str) -> np.ndarray:
    by_key = {(row["side"], row["x_mm"], row["y_mm"]): row for row in rows}
    return np.array([[by_key[(side, x_mm, y_mm)][key] for y_mm in Y_MM]
                     for x_mm in X_MM], dtype=float)


def plot_maps(rows: list[dict[str, object]], target: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.6), layout="constrained")
    max_abs = max(abs(float(row[key])) for row in rows
                  for key in ("delta_v_observed_v", "delta_v_model_v"))
    max_residual = max(abs(float(row["residual_v"])) for row in rows)
    for row_index, side in enumerate(SIDES):
        for col_index, (key, title) in enumerate((
            ("delta_v_observed_v", "ΔV medido (V)"),
            ("delta_v_model_v", "ΔV modelo existente (V)"),
            ("residual_v", "Medido − modelo (V)"),
        )):
            ax = axes[row_index, col_index]
            limit = max_residual if col_index == 2 else max_abs
            image = ax.imshow(_matrix(rows, side, key), cmap="RdBu_r", vmin=-limit,
                              vmax=limit, aspect="auto", origin="lower")
            ax.set(xticks=range(3), xticklabels=Y_MM, yticks=range(5), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)", title=f"{side}: {title}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="V")
    fig.suptitle("Grade discreta (X sem espaçamento proporcional) · modelo horizontal · sem reajuste")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_outputs(source: Path, output: Path, points: list[GridPoint],
                  references: dict[str, tuple[int, int, float]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows = comparison_rows(points)
    with (output / f"{STEM}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm", "n", "media_adc",
                         "referencia_aplicada_adc", "tensao_media_v", "delta_v_medido_v",
                         "campo_estimado_mt_ss49e_tipico_sem_calibracao_individual",
                         "bz_magpylib_referencia_1t_mt_nao_medido",
                         "delta_v_modelo_escala_anterior_v", "residuo_medido_menos_modelo_v",
                         "bz_modelo_escala_efetiva_mt_nao_medido", "observacao_planilha"))
        for row in rows:
            writer.writerow((row["side"], row["x_mm"], row["y_mm"], row["count"],
                             *(f"{row[key]:.9f}" for key in (
                                 "mean_adc", "reference_adc", "mean_voltage_v",
                                 "delta_v_observed_v", "field_estimated_mt",
                                 "bz_reference_mt", "delta_v_model_v", "residual_v",
                                 "field_model_effective_mt")), row["note"]))
    plot_maps(rows, output / f"{STEM}.png")
    side_mae = {side: sum(abs(float(r["residual_v"])) for r in rows if r["side"] == side) / 15
                for side in SIDES}
    overall_mae = sum(abs(float(r["residual_v"])) for r in rows) / 30
    overall_rmse = (sum(float(r["residual_v"]) ** 2 for r in rows) / 30) ** 0.5
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    lines = [
        "# Mapeamento Hall em 30 posições × modelo horizontal", "",
        "**Histórico substituído em X=5 mm:** os seis valores desta primeira "
        "grade foram substituídos pelo [reteste vigente](mapeamento-hall-x5-revisado.md). "
        "Este relatório e seus mapas permanecem para rastreabilidade; "
        "não representam a grade vigente completa.", "",
        f"Fonte original preservada: [mapeamento_hall_grade.xlsx](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) "
        f"(SHA-256 `{source_hash}`). A aba `Médias por posição` contém **30 "
        "médias de blocos seriais**, não as linhas individuais da porta serial: "
        f"{sum(p.count for p in points)} amostras com ímã resumidas. Há ainda "
        f"{sum(reference[0] + reference[1] for reference in references.values())} "
        "amostras de referência resumidas. Não é possível recalcular cada média "
        "ADC a partir de leituras individuais ausentes; foram conferidas "
        "as fórmulas, os valores em cache e as 30 células do mapa. A observação "
        "da posição lado 1, X=10, Y=−10 mm diz que a média usa a repetição "
        "estável após um primeiro bloco com troca de patamar; essa escolha "
        "da fonte foi preservada, sem reconstruir o bloco omitido.", "",
        "## Cálculos conferidos", "",
        "Para cada lado, a referência aplicada é a **média simples** das médias "
        "ADC do começo e do fim, sem ponderação pelos tamanhos dos blocos. "
        "A planilha não tem tempo por posição, então não permite interpolar "
        "deriva temporal. A conversão inscrita é `tensão = média ADC × 5/1023 V`, "
        "com 5 V nominais, não aferidos. `ΔV = (média ADC − referência aplicada) "
        "× 5/1023 × 1000 mV` e `campo estimado = ΔV/14 mT`.", "",
        "O experimentador identificou o sensor como **Honeywell SS49E** do kit "
        "Elegoo de 37 sensores. Os **14 mV/mT** são a sensibilidade típica da "
        "[ficha Honeywell](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf) "
        "(1,4 mV/G × 10 G/mT), não uma calibração individual. O campo em mT "
        "é estimado a partir de tensão; não é medição de campo calibrada.", "",
        "| Lado | n início | Referência início (ADC) | n fim | Referência fim (ADC) | Referência aplicada (ADC) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    map_rows = _workbook_sheets(source)["Mapa"]
    for side in SIDES:
        n_start, n_end, applied = references[side]
        map_row = map_rows[6 if side == SIDES[0] else 7]
        lines.append(f"| {side} | {n_start} | {float(map_row['C']):.6f} | {n_end} | "
                     f"{float(map_row['E']):.6f} | {applied:.6f} |")
    lines += ["", "## Comparação sem ajuste novo", "",
              "[Mapa observado, mapa calculado e resíduos em volts]"
              f"({STEM}.png) · [Tabela completa de 30 posições]({STEM}.csv). "
              "A posição X é tratada como a distância horizontal nominal da "
              "face próxima ao Hall; Y é tratado **provisoriamente** como "
              "deslocamento lateral ao longo do comprimento do ímã. O Hall "
              "fica fixo e o centro do ímã é deslocado para `Y_global = −Y_grade`. "
              "O sinal e a origem física de Y não foram documentados "
              "independentemente. X=0 não aparece nesta grade. O gráfico "
              "organiza as posições X como categorias; o espaçamento vertical "
              "das células não é proporcional aos milímetros.", "",
              "Foi reutilizado o cenário de [comparação horizontal anterior]"
              "(comparacao-horizontal.md): comprimento em +Y, polarização "
              "local +Z de **1 T apenas como referência matemática**, virada "
              "rígida entre os lados, projeção candidata `vertical_z`, Hall na "
              "altura do centro do ímã e deslocamento do zero igual a 0 mm. "
              f"A escala elétrica **{PREVIOUS_SCALE_V_PER_T:+.6f} V/T** é a já "
              "publicada para as 14 médias de 5–50 mm da outra coleta. "
              "**Nenhuma escala, altura ou deslocamento foi ajustado à grade.** "
              "As alturas, o eixo sensível, a magnetização real e a distância "
              "física permanecem desconhecidos. A média dimensional do "
              "cuboide é 19,37 × 9,40 × 4,48 mm.", "",
              "| Conjunto | MAE entre ΔV medido e modelo (V) |",
              "| --- | ---: |"]
    for side in SIDES:
        lines.append(f"| {side} (15 posições) | {side_mae[side]:.6f} |")
    lines += [f"| Ambos (30 posições) | {overall_mae:.6f} |", "",
              f"RMSE conjunto: **{overall_rmse:.6f} V**. Esses números medem "
              "a transferência do cenário anterior a esta grade; não validam "
              "a orientação sensível do Hall. A componente de referência "
              "Magpylib e a versão com escala efetiva são cálculos, não "
              "campo medido. Um [estudo exploratório separado de uma escala "
              "comum](mapeamento-hall-escala-exploratoria.md) examina os "
              "resíduos sem substituir esta comparação fixa.", "",
              "## Leitura dos mapas", "",
              "A grade registra sinal positivo para o lado 1 e negativo para "
              "o lado 2 em todas as posições. O maior módulo em cada lado "
              "ocorre em X=5 mm, Y=0 mm. A concentração central e a inversão "
              "de sinal podem ser comparadas visualmente com o cenário "
              "horizontal, mas a concordância quantitativa deve ser julgada "
              "pelos resíduos da tabela e do gráfico. Assimetria entre Y=−10 "
              "e Y=+10 mm pode refletir alinhamento ou outra característica "
              "da montagem; esta planilha não identifica sua causa.", "",
              "A resposta estimada em mT apenas reescala ΔV. A curva `vertical_z` "
              "não demonstra que esse seja o eixo sensível real. Se a face "
              "marcada do SS49E estivesse apontada horizontalmente para o "
              "ímã, a projeção normal candidata seria X, cuja escala elétrica "
              "não foi identificada no ajuste anterior simétrico. São "
              "necessários a orientação do chip, a definição física de X/Y, "
              "a altura relativa e o zero físico antes de atribuir significado "
              "físico aos resíduos.", "",
              "Reproduza a conferência e os mapas com `.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/hall_grid_analysis.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    points, references = load_grid(args.source)
    write_outputs(args.source, args.output, points, references)
    print(f"{len(points)} posições conferidas; mapas em {args.output}")


if __name__ == "__main__":
    main()
