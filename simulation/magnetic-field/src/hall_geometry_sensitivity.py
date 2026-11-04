"""Grade de altura relativa × deslocamento para o modelo Hall horizontal."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import magpylib as magpy
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

from compare_hall_mountings import mounting_setup, template
from hall_analysis import OUTPUT, ROOT, SOURCE, Result, _workbook_sheets, calculate, load_readings, verify_comparison
from magnet_geometry import dimensions_for


AXIS = "vertical_z"  # projeção candidata do relatório horizontal; não eixo medido
FIT_DISTANCES_MM = (5, 10, 15, 20, 30, 40, 50)
SIDES = ("Lado 1", "Lado 2")
STEM = "sensibilidade-geometrica-horizontal"
HEIGHTS_RELATIVE_MM = tuple(float(x) for x in np.arange(-2.0, 2.0001, 0.25))
OFFSETS_MM = tuple(float(x) for x in np.arange(0.0, 6.0001, 0.25))
ADC_LOW_V = 0.0
ADC_HIGH_V = 5.0  # limite de leitura nominal inferido, não especificação do AH49E


@dataclass(frozen=True)
class Scenario:
    height_relative_mm: float
    offset_mm: float
    scale_v_per_t: float
    mae_v: float
    rmse_v: float
    zero_delta_v: dict[str, float]
    zero_output_v: dict[str, float]
    zero_within_adc_range: bool


def sensor_height_mm(height_relative_mm: float) -> float:
    """Conversão interna; a entrada da análise é relativa ao centro do ímã."""
    return dimensions_for()[2] * 1000 / 2 + height_relative_mm


def validate_outside_magnet(height_relative_mm: float, offset_mm: float) -> None:
    """Rejeita deslocamentos negativos e qualquer ponto estritamente interno."""
    if not np.isfinite(height_relative_mm) or not np.isfinite(offset_mm):
        raise ValueError("Altura relativa e deslocamento devem ser finitos")
    if offset_mm < 0:
        raise ValueError("Deslocamento negativo colocaria o Hall dentro do ímã em 0 mm")
    setup = mounting_setup("Lado 1", 0, sensor_height_mm(height_relative_mm), offset_mm)
    local_position = setup.magnet.orientation.inv().apply(setup.sensor.position - setup.magnet.position)
    half_dimensions = np.asarray(setup.magnet.dimension, dtype=float) / 2
    if np.all(np.abs(local_position) < half_dimensions - 1e-12):
        raise ValueError("O elemento Hall ficaria dentro do volume do ímã")


def fit_scenario(results: list[Result], height_relative_mm: float, offset_mm: float) -> Scenario:
    validate_outside_magnet(height_relative_mm, offset_mm)
    selected = [r for r in results if r.distance_mm in FIT_DISTANCES_MM]
    if len(results) != 16 or len(selected) != 14 or sum(r.distance_mm == 0 for r in results) != 2:
        raise ValueError("Esperadas 14 médias de 5 a 50 mm e dois pontos de 0 mm")
    height = sensor_height_mm(height_relative_mm)
    field = np.array([template(r.side, r.distance_mm, AXIS, height, offset_mm) for r in selected])
    observed = np.array([r.delta_v_mv / 1000 for r in selected])
    denominator = float(np.dot(field, field))
    if denominator <= 0:
        raise ValueError("Template sem campo para ajustar a escala")
    scale = float(np.dot(field, observed) / denominator)
    residuals = observed - scale * field
    zero_rows = {r.side: r for r in results if r.distance_mm == 0}
    zero_delta = {side: scale * template(side, 0, AXIS, height, offset_mm) for side in SIDES}
    zero_output = {side: zero_rows[side].reference_voltage_v + zero_delta[side] for side in SIDES}
    return Scenario(
        height_relative_mm, offset_mm, scale,
        float(np.mean(np.abs(residuals))), float(np.sqrt(np.mean(np.square(residuals)))),
        zero_delta, zero_output,
        all(ADC_LOW_V <= zero_output[side] <= ADC_HIGH_V for side in SIDES),
    )


def run_grid(results: list[Result], heights: tuple[float, ...] = HEIGHTS_RELATIVE_MM,
             offsets: tuple[float, ...] = OFFSETS_MM) -> list[Scenario]:
    if not heights or not offsets:
        raise ValueError("A grade não pode ser vazia")
    return [fit_scenario(results, height, offset) for height in heights for offset in offsets]


def representative_scenarios(scenarios: list[Scenario]) -> list[tuple[str, Scenario]]:
    """Melhor, alternativa de erro próximo, base e melhor com 0 mm na faixa ADC."""
    best = min(scenarios, key=lambda s: (s.rmse_v, abs(s.height_relative_mm), s.offset_mm))
    by_key = {(s.height_relative_mm, s.offset_mm): s for s in scenarios}
    selected: list[tuple[str, Scenario]] = [("melhor na grade", best)]
    mirror = by_key.get((-best.height_relative_mm, best.offset_mm))
    if mirror is not None and mirror != best:
        selected.append(("altura espelhada", mirror))
    near = [s for s in scenarios if s.rmse_v <= best.rmse_v * 1.10 + 1e-12 and s not in dict(selected).values()]
    if near:
        alternative = max(near, key=lambda s: (abs(s.height_relative_mm - best.height_relative_mm)
                                                + abs(s.offset_mm - best.offset_mm), -s.rmse_v))
        selected.append(("alternativa próxima", alternative))
    baseline = by_key.get((0.0, 0.0))
    if baseline is not None and baseline not in dict(selected).values():
        selected.append(("cenário anterior", baseline))
    adc_valid = [s for s in scenarios if s.zero_within_adc_range]
    if adc_valid:
        best_adc_valid = min(adc_valid, key=lambda s: s.rmse_v)
        if best_adc_valid not in dict(selected).values():
            selected.append(("melhor com 0–5 V", best_adc_valid))
    return selected


def prediction_rows(results: list[Result], scenario: Scenario) -> list[dict[str, object]]:
    height = sensor_height_mm(scenario.height_relative_mm)
    rows = []
    for r in results:
        observed = r.delta_v_mv / 1000
        predicted = scenario.scale_v_per_t * template(r.side, r.distance_mm, AXIS,
                                                       height, scenario.offset_mm)
        rows.append({
            "side": r.side, "distance_mm": r.distance_mm, "count": r.count,
            "used_for_fit": r.distance_mm in FIT_DISTANCES_MM,
            "observed_v": observed, "predicted_v": predicted, "residual_v": observed - predicted,
            "output_predicted_v": r.reference_voltage_v + predicted,
        })
    return rows


def plot_heatmap(scenarios: list[Scenario], heights: tuple[float, ...],
                 offsets: tuple[float, ...], target: Path) -> None:
    by_key = {(s.height_relative_mm, s.offset_mm): s for s in scenarios}
    matrix = np.array([[by_key[(h, o)].rmse_v for o in offsets] for h in heights])
    valid_zero = np.array([[by_key[(h, o)].zero_within_adc_range for o in offsets]
                           for h in heights], dtype=float)
    best = min(scenarios, key=lambda s: s.rmse_v)
    fig, ax = plt.subplots(figsize=(9, 6.4), layout="constrained")
    image = ax.imshow(matrix * 1000, origin="lower", aspect="auto", cmap="viridis",
                      extent=(offsets[0] - (offsets[1] - offsets[0]) / 2,
                              offsets[-1] + (offsets[1] - offsets[0]) / 2,
                              heights[0] - (heights[1] - heights[0]) / 2,
                              heights[-1] + (heights[1] - heights[0]) / 2))
    ax.contour(offsets, heights, matrix, levels=[best.rmse_v * 1.10],
               colors="white", linewidths=1.2)
    if valid_zero.min() != valid_zero.max():
        ax.contour(offsets, heights, valid_zero, levels=[0.5],
                   colors="orange", linewidths=1.4, linestyles="--")
    ax.scatter(best.offset_mm, best.height_relative_mm, marker="x", s=90,
               color="red", label="menor RMSE na grade")
    ax.set(xlabel="Deslocamento físico − nominal (mm)",
           ylabel="Altura do Hall − centro do ímã (mm)",
           title="RMSE nas 14 médias · branco: +10% · laranja: limite 0–5 V em 0 mm")
    ax.legend(loc="upper right")
    fig.colorbar(image, ax=ax, label="RMSE (mV)")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def plot_curves(results: list[Result], representatives: list[tuple[str, Scenario]], target: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True,
                             gridspec_kw={"height_ratios": (2, 1)}, layout="constrained")
    top, bottom = axes
    colors = ["#1764a3", "#c95b24", "#558b2f", "#7952a0"]
    for side, marker in (("Lado 1", "o"), ("Lado 2", "s")):
        selected = [r for r in results if r.side == side and r.distance_mm in FIT_DISTANCES_MM]
        top.scatter([r.distance_mm for r in selected], [r.delta_v_mv / 1000 for r in selected],
                    color="black", marker=marker, s=28, label=f"{side}: observado", zorder=4)
    for index, (label, scenario) in enumerate(representatives):
        predicted = prediction_rows(results, scenario)
        for side, linestyle in (("Lado 1", "-"), ("Lado 2", "--")):
            series = [r for r in predicted if r["side"] == side and r["used_for_fit"]]
            top.plot([r["distance_mm"] for r in series], [r["predicted_v"] for r in series],
                     color=colors[index], linestyle=linestyle, label=f"{label}: {side}")
            bottom.plot([r["distance_mm"] for r in series], [r["residual_v"] for r in series],
                        color=colors[index], linestyle=linestyle, marker=".")
    top.set(ylabel="ΔV (V)", title="Curvas representativas · 5–50 mm")
    bottom.set(xlabel="Distância nominal (mm)", ylabel="Resíduo (V)")
    bottom.set_xticks(FIT_DISTANCES_MM)
    for ax in axes:
        ax.axhline(0, color="#555", linewidth=0.8)
        ax.grid(alpha=0.23)
    top.legend(fontsize=7, ncol=2)
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_outputs(source: Path, output: Path, results: list[Result],
                  scenarios: list[Scenario], heights: tuple[float, ...], offsets: tuple[float, ...]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    best = min(scenarios, key=lambda s: (s.rmse_v, abs(s.height_relative_mm), s.offset_mm))
    representatives = representative_scenarios(scenarios)
    near = [s for s in scenarios if s.rmse_v <= best.rmse_v * 1.10 + 1e-12]
    ordered = sorted(scenarios, key=lambda s: (s.rmse_v, abs(s.height_relative_mm), s.offset_mm))
    with (output / f"{STEM}-grade.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("altura_relativa_mm", "deslocamento_mm", "escala_efetiva_v_por_t",
                         "mae_14_v", "rmse_14_v", "delta_v_zero_lado1_v", "delta_v_zero_lado2_v",
                         "saida_zero_lado1_v", "saida_zero_lado2_v", "zero_dentro_adc_0a5v"))
        for s in scenarios:
            writer.writerow((f"{s.height_relative_mm:.3f}", f"{s.offset_mm:.3f}",
                             f"{s.scale_v_per_t:.9f}", f"{s.mae_v:.9f}", f"{s.rmse_v:.9f}",
                             *(f"{s.zero_delta_v[side]:.9f}" for side in SIDES),
                             *(f"{s.zero_output_v[side]:.9f}" for side in SIDES),
                             "sim" if s.zero_within_adc_range else "nao"))
    with (output / f"{STEM}-residuos.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("cenario", "altura_relativa_mm", "deslocamento_mm", "lado",
                         "distancia_nominal_mm", "n", "usado_no_ajuste", "delta_v_observado_v",
                         "delta_v_previsto_v", "residuo_v", "saida_prevista_v"))
        for label, scenario in representatives:
            for r in prediction_rows(results, scenario):
                writer.writerow((label, f"{scenario.height_relative_mm:.3f}", f"{scenario.offset_mm:.3f}",
                                 r["side"], r["distance_mm"], r["count"],
                                 "sim" if r["used_for_fit"] else "nao",
                                 *(f"{r[key]:.9f}" for key in
                                   ("observed_v", "predicted_v", "residual_v", "output_predicted_v"))))
    plot_heatmap(scenarios, heights, offsets, output / f"{STEM}-mapa.png")
    plot_curves(results, representatives, output / f"{STEM}-curvas.png")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    try:
        source_label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source_label = str(source)
    lines = [
        "# Sensibilidade geométrica do modelo Hall horizontal", "",
        f"Fonte: `{source_label}` (SHA-256 `{source_hash}`). As **904 leituras** foram "
        "reagregadas e conferidas com a aba `Comparação`. A planilha e os "
        "resultados anteriores não foram alterados. A [montagem horizontal](comparacao-horizontal.md) "
        "define a peça, a virada rígida e a projeção candidata **vertical_z** "
        "usada aqui; o eixo sensível real não foi medido.", "",
        "## Parâmetros e convenções", "",
        "- `altura_relativa_mm = z_Hall − z_centro_ímã`. Valores positivos colocam "
        "o elemento acima do centro; negativos, abaixo. O centro do ímã fica "
        "a 2,24 mm da superfície neste modelo apoiado, mas **a entrada da grade "
        "é relativa**; não se presume altura medida do Hall.",
        "- `deslocamento_mm = lacuna_física − distância_nominal`. Assim, "
        "`lacuna_física = d_nominal + deslocamento`, medida horizontalmente "
        "da face próxima do ímã ao elemento Hall. Deslocamento positivo põe "
        "o elemento mais longe; zero põe o ponto no plano da face em 0 mm. "
        "Somente deslocamentos não negativos são aceitos, e o código também "
        "verifica que o ponto não fica **dentro** do cuboide.",
        f"- Grade exploratória: altura relativa de **{heights[0]:+.2f} a {heights[-1]:+.2f} mm**, "
        f"passo **{heights[1]-heights[0]:.2f} mm**; deslocamento de "
        f"**{offsets[0]:.2f} a {offsets[-1]:.2f} mm**, passo "
        f"**{offsets[1]-offsets[0]:.2f} mm**. São limites escolhidos para "
        "exploração, **não limites medidos**.", "",
        "Em cada uma das combinações da grade, ajusta-se **apenas uma escala "
        "elétrica comum aos dois lados**, por mínimos quadrados sem intercepto, "
        "nas mesmas 14 médias de 5–50 mm. O erro mostrado é calculado nessas "
        "14 médias. O ponto de 0 mm nunca entra no ajuste nem na escolha "
        "do menor erro. As tensões em 0 mm da planilha são **medições reais**; "
        "as tensões obtidas pelo modelo nesse ponto são cálculos de extrapolação.", "",
        f"[Mapa de RMSE]({STEM}-mapa.png) · [Grade completa]({STEM}-grade.csv) · "
        f"[Curvas representativas]({STEM}-curvas.png) · "
        f"[Resíduos de cada cenário mostrado]({STEM}-residuos.csv).", "",
        "## Melhores resultados da grade", "",
        "| Ordem | Altura relativa (mm) | Deslocamento (mm) | Escala efetiva (V/T ref.) | MAE (V) | RMSE (V) |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, s in enumerate(ordered[:10], 1):
        lines.append(f"| {index} | {s.height_relative_mm:+.2f} | {s.offset_mm:.2f} | "
                     f"{s.scale_v_per_t:+.6f} | {s.mae_v:.6f} | {s.rmse_v:.6f} |")
    lines += ["", f"**{len(near)} de {len(scenarios)} combinações** têm RMSE até 10% "
              "acima do mínimo. Nessa faixa, a altura relativa vai de "
              f"{min(s.height_relative_mm for s in near):+.2f} a "
              f"{max(s.height_relative_mm for s in near):+.2f} mm e o deslocamento "
              f"de {min(s.offset_mm for s in near):.2f} a "
              f"{max(s.offset_mm for s in near):.2f} mm. "
              "Pares de alturas com sinais opostos e mesmo valor absoluto "
              "produzem curvas idênticas no modelo simétrico. Esses parâmetros "
              "não são identificados como medidas pela grade.", "",
              "O contorno laranja do mapa separa cenários que extrapolam 0 mm "
              "dentro ou fora da faixa nominal ADC de 0–5 V; não participou "
              "do ajuste das curvas.", "",
              "## Cenários mostrados nas curvas e resíduos", "",
              "| Cenário | Altura relativa (mm) | Deslocamento (mm) | RMSE 5–50 mm (V) |",
              "| --- | ---: | ---: | ---: |"]
    for label, s in representatives:
        lines.append(f"| {label} | {s.height_relative_mm:+.2f} | {s.offset_mm:.2f} | {s.rmse_v:.6f} |")
    lines += ["", "A tabela abaixo traz **observado, previsto e resíduo por lado e "
              "distância** para o menor RMSE. A tabela CSV de resíduos contém "
              "os mesmos valores para todos os cenários representativos. "
              "Resíduo = observado − previsto, em volts.", "",
              "| Lado | d (mm) | ΔV observado (V) | ΔV previsto (V) | Resíduo (V) |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for r in prediction_rows(results, best):
        if r["used_for_fit"]:
            lines.append(f"| {r['side']} | {r['distance_mm']} | {r['observed_v']:+.6f} | "
                         f"{r['predicted_v']:+.6f} | {r['residual_v']:+.6f} |")
    lines += ["", "## 0 mm nominal: tensão medida e extrapolação calculada", "",
              "Os valores de ΔV observado em 0 mm são **medições reais** da "
              "planilha; não são previsões fornecidas pelo experimentador. "
              "Somente os valores calculados pelo modelo nesse ponto são "
              "extrapolações fora do ajuste. O cálculo soma o ΔV do modelo à "
              "**referência sem ímã do mesmo lado** "
              "para obter a tensão total prevista. A faixa **0–5 V** é o limite "
              "nominal de leitura ADC inferido da conversão das leituras "
              "(aproximadamente `ADC × 5/1023`), **não** uma especificação "
              "confirmada de saída linear do AH49E. A alimentação e a faixa "
              "válida do sensor ainda precisam ser verificadas.", "",
              "| Cenário | Lado | ΔV medido (V) | ΔV calculado (V) | Saída calculada (V) | Dentro de 0–5 V? |",
              "| --- | --- | ---: | ---: | ---: | --- |"]
    zero_observed = {r.side: r.delta_v_mv / 1000 for r in results if r.distance_mm == 0}
    for label, s in representatives:
        for side in SIDES:
            value = s.zero_output_v[side]
            in_range = ADC_LOW_V <= value <= ADC_HIGH_V
            lines.append(f"| {label} | {side} | {zero_observed[side]:+.6f} | "
                         f"{s.zero_delta_v[side]:+.6f} | {value:.6f} | "
                         f"{'sim' if in_range else 'não'} |")
    count_in_range = sum(s.zero_within_adc_range for s in scenarios)
    valid_scenarios = [s for s in scenarios if s.zero_within_adc_range]
    valid_near = [s for s in near if s.zero_within_adc_range]
    lines += ["", f"Em toda a grade, **{count_in_range}/{len(scenarios)} cenários** "
              "preveem, em 0 mm, tensão dentro de 0–5 V nos dois lados. "
              f"Entre os {len(near)} cenários até 10% do menor RMSE, "
              f"**{len(valid_near)}** passam nessa checagem. "
              + (f"O menor RMSE entre os cenários que passam é "
                 f"**{min(s.rmse_v for s in valid_scenarios):.6f} V**. "
                 if valid_scenarios else "Nenhum cenário da grade passa nessa checagem. ") +
              "Esse teste de plausibilidade elétrica não usa 0 mm para ajustar "
              "parâmetros e não calibra o sensor. O 0 nominal não é a distância "
              "confirmada até o elemento sensível. O cenário de menor RMSE "
              "nas 14 médias extrapola para fora de 0–5 V nos dois lados; "
              "portanto, seu bom ajuste naquela faixa não valida a resposta "
              "elétrica em 0 mm.", "",
              "## Conclusões sob variação geométrica", "",
              "A aproximação horizontal, o Hall fixo e a inversão de sinal "
              "entre lados continuam representados em toda a grade. A forma "
              "da curva em ΔV pode ser semelhante para várias combinações "
              "de altura relativa e deslocamento; o fator efetivo também "
              "muda. Assim, um menor RMSE de grade **não mede** altura, zero, "
              "magnetização ou sensibilidade elétrica. O eixo vertical de "
              "leitura e a magnetização pela espessura permanecem hipóteses. "
              "ΔV não foi convertido para mT. A identidade dos polos e do "
              "ímã ensaiado permanece desconhecida.", "",
              f"Versões: Python {sys.version.split()[0]}, Magpylib {magpy.__version__}, "
              f"SciPy {scipy.__version__}. Da raiz do repositório: "
              "`.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/hall_geometry_sensitivity.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    sheets = _workbook_sheets(args.source)
    readings = load_readings(sheets)
    references, results = calculate(readings)
    verify_comparison(sheets["Comparação"], references, results)
    scenarios = run_grid(results)
    write_outputs(args.source, args.output, results, scenarios,
                  HEIGHTS_RELATIVE_MM, OFFSETS_MM)
    best = min(scenarios, key=lambda s: s.rmse_v)
    print(f"{len(readings)} leituras; {len(scenarios)} cenários; 14 médias por ajuste")
    print(f"Melhor na grade: altura relativa {best.height_relative_mm:+.2f} mm, "
          f"deslocamento {best.offset_mm:.2f} mm, RMSE {best.rmse_v:.6f} V")


if __name__ == "__main__":
    main()
