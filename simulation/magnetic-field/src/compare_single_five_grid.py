"""Compara as grades vigentes de um e cinco ímãs sem reajustar o modelo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hall_analysis import _workbook_sheets
from hall_five_magnets import SOURCE as FIVE_SOURCE, comparison_rows as five_rows, load_collection
from hall_grid_analysis import (
    MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM, OUTPUT,
    PREVIOUS_SCALE_V_PER_T, REVISED_SOURCE, SIDES, SOURCE as OLD_SINGLE_SOURCE,
    X_MM, Y_MM, load_grid, model_reference_field_t,
)

STEM = "comparacao-grade-um-cinco-imans"
ADC_TO_V = 5.0 / 1023  # conversão nominal registrada nas duas planilhas
RATIO_MARGIN = 2.0  # critério descritivo, não intervalo de confiança


def single_reference_ends() -> dict[tuple[str, int], tuple[float, float]]:
    """Recupera as referências por lado e do reteste X=5 da fonte vigente."""
    sheets = _workbook_sheets(REVISED_SOURCE)
    map_rows = sheets["Mapa"]
    retest = sheets["Reteste X5"]
    ends = {}
    for side, row_number in zip(SIDES, (6, 7)):
        start = float(map_rows[row_number]["C"])
        end = float(map_rows[row_number]["E"])
        for x_mm in X_MM:
            ends[(side, x_mm)] = (start, end)
        ends[(side, 5)] = (float(retest[5]["C"]), float(retest[6]["C"]))
    return ends


def calculate() -> tuple[list[dict[str, float | int | str]], dict[str, float]]:
    single, _ = load_grid(REVISED_SOURCE)
    five, references = load_collection(FIVE_SOURCE)
    five_by_key = {(r["side"], r["x_mm"], r["y_mm"]): r
                   for r in five_rows(five, references)}
    ends = single_reference_ends()
    if len(single) != 30 or len(five_by_key) != 30:
        raise ValueError("Esperadas duas grades de 30 posições")
    rows = []
    for point in single:
        key = (point.side, point.x_mm, point.y_mm)
        if key not in five_by_key:
            raise ValueError(f"Posição ausente na fileira: {key}")
        other = five_by_key[key]
        start_adc, end_adc = ends[(point.side, point.x_mm)]
        if not math.isclose(point.reference_adc, (start_adc + end_adc) / 2,
                            rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Referência única incompatível: {key}")
        single_delta = point.mean_voltage_v - point.reference_adc * ADC_TO_V
        if not math.isclose(single_delta, point.delta_v_mv / 1000,
                            rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"ΔV único incompatível: {key}")
        single_field = model_reference_field_t(*key)
        five_field = float(other["model_field_reference_t"])
        single_pred = PREVIOUS_SCALE_V_PER_T * single_field
        five_pred = PREVIOUS_SCALE_V_PER_T * five_field
        five_delta_initial = float(other["delta_initial_v"])
        five_delta_final = float(other["delta_final_v"])
        five_delta_middle = (five_delta_initial + five_delta_final) / 2
        drift_single = abs(end_adc - start_adc) * ADC_TO_V
        drift_five = abs(references.drift_v)
        threshold = RATIO_MARGIN * max(drift_single, drift_five)
        eligible = abs(single_delta) > threshold
        rows.append({
            "lado": point.side, "x_nominal_mm": point.x_mm,
            "y_nominal_mm": point.y_mm, "n_um": point.count,
            "n_cinco": int(other["count"]),
            "tensao_medida_um_v": point.mean_voltage_v,
            "ref_um_inicio_v": start_adc * ADC_TO_V,
            "ref_um_fim_v": end_adc * ADC_TO_V,
            "ref_um_aplicada_v": point.reference_adc * ADC_TO_V,
            "deriva_ref_um_modulo_v": drift_single,
            "delta_um_medido_v": single_delta,
            "tensao_medida_cinco_v": float(other["mean_voltage_v"]),
            "ref_cinco_inicio_v": references.initial_adc * ADC_TO_V,
            "ref_cinco_fim_v": references.final_adc * ADC_TO_V,
            "deriva_ref_cinco_fim_menos_inicio_v": references.drift_v,
            "delta_cinco_ref_inicio_v": five_delta_initial,
            "delta_cinco_ref_fim_v": five_delta_final,
            "delta_cinco_intermediario_ilustrativo_v": five_delta_middle,
            "diferenca_medida_intermediaria_cinco_menos_um_v": five_delta_middle - single_delta,
            "diferenca_medida_ref_inicio_cinco_menos_um_v": five_delta_initial - single_delta,
            "diferenca_medida_ref_fim_cinco_menos_um_v": five_delta_final - single_delta,
            "campo_modelo_um_referencia_1t_t": single_field,
            "campo_modelo_cinco_referencia_1t_t": five_field,
            "delta_um_modelo_escala_fixa_v": single_pred,
            "delta_cinco_modelo_escala_fixa_v": five_pred,
            "diferenca_modelo_cinco_menos_um_v": five_pred - single_pred,
            "residuo_um_v": single_delta - single_pred,
            "residuo_cinco_ref_inicio_v": five_delta_initial - five_pred,
            "residuo_cinco_ref_fim_v": five_delta_final - five_pred,
            "residuo_cinco_intermediario_v": five_delta_middle - five_pred,
            "residuo_diferenca_intermediaria_v": (five_delta_middle - single_delta)
                                                - (five_pred - single_pred),
            "limiar_razao_v": threshold,
            "razao_cinco_sobre_um": five_delta_middle / single_delta if eligible else "",
            "razao_estado": "calculavel" if eligible else "inconclusiva_referencia",
        })
    if len({(r["lado"], r["x_nominal_mm"], r["y_nominal_mm"]) for r in rows}) != 30:
        raise ValueError("Posições duplicadas")
    return rows, {"deriva_cinco_v": references.drift_v}


def metrics(rows: list[dict[str, float | int | str]], key: str) -> tuple[float, float]:
    errors = np.array([float(row[key]) for row in rows])
    return float(np.mean(np.abs(errors))), float(np.sqrt(np.mean(errors**2)))


def plot_triptych(rows: list[dict[str, float | int | str]], keys: tuple[str, str, str],
                  labels: tuple[str, str, str], title: str, target: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.4), layout="constrained")
    limit = max(abs(float(row[key])) for row in rows for key in keys)
    for i, side in enumerate(SIDES):
        lookup = {(int(r["x_nominal_mm"]), int(r["y_nominal_mm"])): r
                  for r in rows if r["lado"] == side}
        for j, (key, label) in enumerate(zip(keys, labels)):
            matrix = [[float(lookup[(x, y)][key]) for y in Y_MM] for x in X_MM]
            ax = axes[i, j]
            image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="RdBu_r",
                              vmin=-limit, vmax=limit)
            ax.set(xticks=range(3), xticklabels=Y_MM,
                   yticks=range(5), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)",
                   title=f"{side}: {label}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="V")
    fig.suptitle(title)
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_outputs(rows: list[dict[str, float | int | str]], meta: dict[str, float],
                  output: Path = OUTPUT) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / f"{STEM}.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plot_triptych(rows,
                  ("delta_um_medido_v", "delta_cinco_intermediario_ilustrativo_v",
                   "diferenca_medida_intermediaria_cinco_menos_um_v"),
                  ("1 ímã medido", "5 ímãs medidos · ref. média", "5 − 1 medido"),
                  "ΔV medido · cada coleta usa sua referência · cinco: média dos extremos ilustrativa",
                  output / f"{STEM}-medido.png")
    plot_triptych(rows,
                  ("delta_um_modelo_escala_fixa_v", "delta_cinco_modelo_escala_fixa_v",
                   "diferenca_modelo_cinco_menos_um_v"),
                  ("1 ímã calculado", "5 ímãs calculados", "5 − 1 calculado"),
                  "ΔV Magpylib · mesma componente vertical_z e escala fixa",
                  output / f"{STEM}-modelo.png")
    plot_triptych(rows,
                  ("residuo_um_v", "residuo_cinco_intermediario_v",
                   "residuo_diferenca_intermediaria_v"),
                  ("1 ímã", "5 ímãs · ref. média", "diferença"),
                  "Resíduos medido − calculado · referência média dos cinco apenas ilustrativa",
                  output / f"{STEM}-residuos.png")
    ratio_count = sum(row["razao_estado"] == "calculavel" for row in rows)
    lines = [
        "# Comparação direta das grades Hall: um e cinco ímãs", "",
        "## Fontes vigentes e método", "",
        f"Ímã único: [planilha revisada](../../experiments/hall-sensor/{REVISED_SOURCE.name}) "
        f"(SHA-256 `{hashlib.sha256(REVISED_SOURCE.read_bytes()).hexdigest()}`). "
        "Os seis pontos X=5 mm vêm do reteste válido; os outros 24 são da coleta "
        f"anterior [preservada](../../experiments/hall-sensor/{OLD_SINGLE_SOURCE.name}). "
        f"Fileira: [planilha original](../../experiments/hall-sensor/{FIVE_SOURCE.name}) "
        f"(SHA-256 `{hashlib.sha256(FIVE_SOURCE.read_bytes()).hexdigest()}`). "
        "São 30 posições por configuração, cruzadas exatamente por lado, X e Y. "
        "As planilhas e os resultados anteriores permanecem intactos.", "",
        "As coordenadas são **nominais**: X = 5, 10, 20, 30, 50 mm; "
        "Y = −10, 0, +10 mm. A correspondência de `lado 1` e `lado 2` "
        "entre coletas é assumida pela identificação registrada; não há "
        "verificação independente das polaridades dos cinco ímãs. "
        "Em um ímã, a referência aplicada é a média dos blocos inicial e "
        "final do lado, exceto X=5, que usa a referência própria do reteste. "
        "Em cinco ímãs, mostram-se separadamente as referências inicial e "
        "final. A média dos extremos é usada **apenas como cenário ilustrativo** "
        "para os mapas e métricas; não representa a referência verdadeira em "
        "cada instante. A faixa entre extremos não é intervalo de confiança.", "",
        "`ΔV = tensão média medida − referência sem ímã` (conversão ADC × 5/1023 V, "
        "nominal). Diferença observada = ΔV de cinco − ΔV de um. O Magpylib "
        "usa o mesmo Hall fixo, X horizontal, Y lateral, componente candidata "
        "`vertical_z` (+Z global), polarização de referência local +Z e escala "
        f"elétrica fixa **{PREVIOUS_SCALE_V_PER_T:+.6f} V/T**. Um cuboide médio "
        "é comparado com cinco cuboides médios encostados em X; a soma dos "
        "campos é calculada sem novo ajuste. Os campos em T são campos de "
        "**referência matemática para polarização de 1 T**, não medições "
        "absolutas calibradas. Não se aplica conversão em mT aos dados Hall "
        "nesta comparação.", "",
        f"[Tabela dos 30 pares com tensões, referências, ΔV, campos de referência, "
        f"previsões, resíduos e razões]({STEM}.csv) · "
        f"[mapas medidos]({STEM}-medido.png) · "
        f"[mapas calculados]({STEM}-modelo.png) · "
        f"[mapas de resíduos]({STEM}-residuos.png).", "",
        "## Métricas (volts)", "",
        "| Configuração | MAE | RMSE |", "| --- | ---: | ---: |",
    ]
    for label, key in (("Um ímã", "residuo_um_v"),
                       ("Cinco · referência inicial", "residuo_cinco_ref_inicio_v"),
                       ("Cinco · referência final", "residuo_cinco_ref_fim_v"),
                       ("Cinco · média ilustrativa", "residuo_cinco_intermediario_v"),
                       ("Diferença 5 − 1 · média ilustrativa", "residuo_diferenca_intermediaria_v")):
        mae, rmse = metrics(rows, key)
        lines.append(f"| {label} | {mae:.6f} | {rmse:.6f} |")
    lines += ["", "## Diferenças observadas e razão", "",
              f"A referência dos cinco caiu **{meta['deriva_cinco_v']:+.6f} V** "
              "entre início e fim; portanto, o ΔV calculado com a referência "
              "final é algebricamente maior em 0,013015 V para cada "
              "posição, e a diferença 5 − 1 também muda por esse valor. "
              "A tabela mostra ambos os extremos. A deriva da referência "
              "do ímã único varia por lado e pelo reteste e consta por linha. "
              "Em X=5, Y=0 mm, o lado 1 tem ΔV de **+0,7784 V** com um ímã "
              "e **+0,6001 V** com cinco (referência média ilustrativa); "
              "o lado 2 tem **−0,6482 V** e **−0,6247 V**. Em Y=±10 mm "
              "e X=5, o módulo da resposta de cinco também é menor. "
              "Em X=50 mm, as respostas são pequenas e a deriva de "
              "0,013015 V da fileira pode mudar sua interpretação de sinal. "
              "Nas seis coordenadas de X=5 mm, o módulo de ΔV da fileira "
              "é menor que o do ímã único sob a referência média ilustrativa; "
              "a tendência não é uniforme nas distâncias maiores. "
              "Essas diferenças são observações em volts sob as referências "
              "indicadas, não uma estimativa calibrada de campo.", "",
              f"A razão `ΔV_cinco_intermediário / ΔV_um` foi calculada em "
              f"**{ratio_count}/30** posições. Critério conservador: "
              "`|ΔV_um| > 2 × max(|deriva da referência de um|, "
              "|deriva da referência de cinco|)`. O fator 2 é uma regra "
              "exploratória para afastar denominadores pequenos, não um "
              "limite estatístico. Nas demais posições, a razão aparece "
              "como inconclusiva; nesta grade, são os 12 pontos em X=30 e "
              "50 mm. Mesmo onde calculada, a razão não mede "
              "quantas vezes o campo físico aumentou.", "",
              "## Limitações", "",
              "A fileira tem faces encostadas, mas as larguras individuais "
              "e a magnetização/polaridade de cada peça não foram medidas. "
              "O eixo sensível real do SS49E, a distância entre a marca X=0 "
              "e seu elemento interno, a altura e a orientação exata entre "
              "coletas permanecem hipóteses. As 30 médias da fileira resumem "
              "leituras individuais indisponíveis; não permitem estimar "
              "variância ponto a ponto. A deriva observada não determina a "
              "referência de cada instante. As escalas e geometrias foram "
              "herdadas para comparação exploratória, sem calibração ou "
              "validação independente.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    rows, meta = calculate()
    write_outputs(rows, meta, args.output)
    print(f"{len(rows)} pares de posições; {sum(r['razao_estado'] == 'calculavel' for r in rows)} razões calculáveis")


if __name__ == "__main__":
    main()
