"""Compara o reteste X=5 com a grade histórica sem reajustar o modelo."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hall_grid_analysis import (
    OUTPUT, PREVIOUS_SCALE_V_PER_T, REVISED_SOURCE, SIDES, SOURCE, X_MM, Y_MM,
    GridPoint, _matrix, comparison_rows, load_grid,
)


# Escala fixa da primeira comparação horizontal, ajustada às 14 médias de distância.
FIXED_SCALE_V_PER_T = PREVIOUS_SCALE_V_PER_T
# Ajustada somente à grade ANTERIOR de 30 posições, mantida como histórico.
HISTORICAL_EXPLORATORY_SCALE_V_PER_T = -6.831328
STEM = "mapeamento-hall-x5-revisado"


def compare_version(points: list[GridPoint]) -> list[dict[str, object]]:
    base = comparison_rows(points)
    rows = []
    for point, row in zip(points, base):
        field_t = row["bz_reference_mt"] / 1000
        historical_v = HISTORICAL_EXPLORATORY_SCALE_V_PER_T * field_t
        rows.append({
            "side": point.side, "x_mm": point.x_mm, "y_mm": point.y_mm,
            "count": point.count, "mean_adc": point.mean_adc,
            "reference_adc": point.reference_adc,
            "mean_voltage_v": point.mean_voltage_v,
            "observed_v": point.delta_v_mv / 1000,
            "estimated_mt": point.estimated_field_mt,
            "bz_reference_mt": row["bz_reference_mt"],
            "fixed_predicted_v": row["delta_v_model_v"],
            "fixed_residual_v": row["residual_v"],
            "historical_predicted_v": historical_v,
            "historical_residual_v": point.delta_v_mv / 1000 - historical_v,
        })
    return rows


def error_metrics(rows: list[dict[str, object]], residual_key: str) -> tuple[float, float]:
    residuals = np.asarray([row[residual_key] for row in rows], dtype=float)
    if residuals.size == 0:
        raise ValueError("Métricas exigem posições")
    return float(np.mean(np.abs(residuals))), float(np.sqrt(np.mean(residuals**2)))


def plot_maps(rows: list[dict[str, object]], target: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.6), layout="constrained")
    max_signal = max(abs(float(row[key])) for row in rows
                     for key in ("observed_v", "fixed_predicted_v"))
    max_residual = max(abs(float(row["fixed_residual_v"])) for row in rows)
    for index, side in enumerate(SIDES):
        for column, (key, label) in enumerate((
            ("observed_v", "ΔV medido revisado (V)"),
            ("fixed_predicted_v", "Modelo · escala fixa (V)"),
            ("fixed_residual_v", "Medido − modelo (V)"),
        )):
            ax = axes[index, column]
            limit = max_residual if column == 2 else max_signal
            image = ax.imshow(_matrix(rows, side, key), origin="lower", aspect="auto",
                              cmap="RdBu_r", vmin=-limit, vmax=limit)
            ax.set(xticks=range(len(Y_MM)), xticklabels=Y_MM,
                   yticks=range(len(X_MM)), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)",
                   title=f"{side}: {label}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="V")
    fig.suptitle("Grade revisada: reteste X=5 vigente · escala fixa sem reajuste · X discreto")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def plot_x5_history(old: list[dict[str, object]], new: list[dict[str, object]], target: Path) -> None:
    old_by_key = {(row["side"], row["x_mm"], row["y_mm"]): row for row in old}
    new_by_key = {(row["side"], row["x_mm"], row["y_mm"]): row for row in new}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), layout="constrained", sharey=True)
    for side, ax in zip(SIDES, axes):
        previous = [old_by_key[(side, 5, y)]["observed_v"] for y in Y_MM]
        revised = [new_by_key[(side, 5, y)]["observed_v"] for y in Y_MM]
        model = [new_by_key[(side, 5, y)]["fixed_predicted_v"] for y in Y_MM]
        ax.plot(Y_MM, previous, "o--", label="Medição anterior · substituída")
        ax.plot(Y_MM, revised, "s-", label="Reteste · vigente")
        ax.plot(Y_MM, model, "x:", label="Modelo · escala fixa −12,320751 V/T")
        ax.set(xlabel="Y nominal (mm)", title=f"{side}, X=5 mm")
        ax.axhline(0, color="#555", linewidth=0.8)
        ax.grid(alpha=0.23)
    axes[0].set_ylabel("ΔV (V)")
    axes[0].legend(fontsize=8)
    fig.suptitle("Histórico dos seis pontos X=5 mm · sem novo ajuste")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_outputs(source: Path, output: Path, old_points: list[GridPoint],
                  revised_points: list[GridPoint]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    old_rows = compare_version(old_points)
    new_rows = compare_version(revised_points)
    old_by_key = {(r["side"], r["x_mm"], r["y_mm"]): r for r in old_rows}
    new_by_key = {(r["side"], r["x_mm"], r["y_mm"]): r for r in new_rows}
    if set(old_by_key) != set(new_by_key) or len(new_rows) != 30:
        raise ValueError("Grades histórica e revisada incompatíveis")
    with (output / f"{STEM}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm", "estado", "n",
                         "media_adc", "referencia_aplicada_adc", "tensao_media_v",
                         "delta_v_medido_v", "campo_estimado_mt_ss49e_tipico_sem_calibracao_individual",
                         "bz_magpylib_referencia_1t_mt_nao_medido",
                         "delta_v_modelo_escala_fixa_v", "residuo_escala_fixa_v",
                         "delta_v_modelo_escala_exploratoria_historica_v", "residuo_escala_exploratoria_historica_v"))
        for row in new_rows:
            writer.writerow((row["side"], row["x_mm"], row["y_mm"],
                             "vigente_reteste_x5" if row["x_mm"] == 5 else "mantido",
                             row["count"], *(f"{row[key]:.9f}" for key in (
                                 "mean_adc", "reference_adc", "mean_voltage_v", "observed_v",
                                 "estimated_mt", "bz_reference_mt", "fixed_predicted_v",
                                 "fixed_residual_v", "historical_predicted_v",
                                 "historical_residual_v"))))
    with (output / f"{STEM}-historico.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm", "estado", "arquivo_fonte",
                         "n", "media_adc", "referencia_aplicada_adc", "tensao_media_v",
                         "delta_v_medido_v", "campo_estimado_mt_ss49e_tipico_sem_calibracao_individual",
                         "residuo_escala_fixa_v"))
        for side in SIDES:
            for y_mm in Y_MM:
                for status, filename, row in (
                    ("substituido", SOURCE.name, old_by_key[(side, 5, y_mm)]),
                    ("vigente_reteste", source.name, new_by_key[(side, 5, y_mm)]),
                ):
                    writer.writerow((side, 5, y_mm, status, filename, row["count"],
                                     *(f"{row[key]:.9f}" for key in (
                                         "mean_adc", "reference_adc", "mean_voltage_v",
                                         "observed_v", "estimated_mt", "fixed_residual_v"))))
    plot_maps(new_rows, output / f"{STEM}.png")
    plot_x5_history(old_rows, new_rows, output / f"{STEM}-historico.png")

    def metric_line(label: str, selected_old: list[dict[str, object]],
                    selected_new: list[dict[str, object]], key: str) -> str:
        before = error_metrics(selected_old, key)
        after = error_metrics(selected_new, key)
        return (f"| {label} | {len(selected_new)} | {before[0]:.6f} | {after[0]:.6f} | "
                f"{before[1]:.6f} | {after[1]:.6f} |")

    lines = [
        "# Grade Hall revisada: reteste de X=5 mm", "",
        f"Fonte vigente preservada: [mapeamento_hall_grade_revisado_x5.xlsx]"
        f"(../../experiments/hall-sensor/{source.name}) "
        f"(SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`). "
        "A [planilha anterior](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) "
        "e seus [mapas históricos](mapeamento-hall-horizontal.md) também "
        "permanecem preservados. **As seis posições X=5 mm anteriores foram "
        "substituídas pelo reteste; as outras 24 posições não mudaram.** "
        f"A grade vigente resume **{sum(p.count for p in revised_points)} "
        "amostras com ímã** em 30 médias de blocos. A planilha não contém "
        "a ordem temporal das leituras seriais.", "",
        "## Conferência e referência do reteste", "",
        "A aba `Reteste X5` contém a distribuição de códigos ADC do novo "
        "bloco, as médias e contagens anteriores, e a referência específica "
        "do reteste. As frequências dos códigos reproduzem as seis contagens "
        "e médias novas. Foram conferidos também ΔV, `ADC × 5/1023 V`, "
        "a conversão por 14 mV/mT e as seis células X=5 da aba `Mapa`. "
        "A referência reteste usa **29** leituras iniciais (média "
        "**533,689655 ADC**) e **25** finais (média **535,000000 ADC**); "
        "a média simples aplicada aos dois lados em X=5 é **534,344828 ADC**. "
        "Para X≥10 mm permanecem as referências antigas próprias de cada "
        "lado. As planilhas não foram editadas.", "",
        f"[CSV vigente de 30 posições]({STEM}.csv) · "
        f"[Histórico dos seis pontos, com estado substituído/vigente]({STEM}-historico.csv) · "
        f"[Mapas vigentes]({STEM}.png) · "
        f"[Gráfico antes/depois em X=5]({STEM}-historico.png). "
        "O campo em mT segue **14 mV/mT típicos do SS49E Honeywell**, "
        "sem calibração individual; os resíduos são analisados em volts.", "",
        "## Comparação com escalas já publicadas", "",
        "**Primeira comparação, sem reajuste:** a escala fixa do modelo "
        f"horizontal, **{FIXED_SCALE_V_PER_T:+.6f} V/T de referência**, "
        "ajustada à primeira coleta de 14 médias, é aplicada à grade "
        "revisada. Para rastrear a análise anterior da grade, também "
        f"mostramos a escala **{HISTORICAL_EXPLORATORY_SCALE_V_PER_T:+.6f} V/T**, "
        "exploratoriamente ajustada às 30 posições **anteriores**, sem novo "
        "ajuste ao reteste. A geometria horizontal, a virada "
        "rígida, a polarização local +Z de referência, a componente candidata "
        "`vertical_z`, a altura relativa de 0 mm e o deslocamento nominal "
        "de 0 mm foram mantidos. Nenhuma geometria ou orientação foi ajustada.", "",
        "| Escala e conjunto | Posições | MAE antes (V) | MAE revisado (V) | RMSE antes (V) | RMSE revisado (V) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for scale_name, key in (("fixa −12,320751", "fixed_residual_v"),
                            ("exploratória histórica −6,831328", "historical_residual_v")):
        lines.append(metric_line(f"{scale_name}, ambos", old_rows, new_rows, key))
        for side in SIDES:
            old_side = [row for row in old_rows if row["side"] == side]
            new_side = [row for row in new_rows if row["side"] == side]
            lines.append(metric_line(f"{scale_name}, {side}", old_side, new_side, key))
        old_x5 = [row for row in old_rows if row["x_mm"] == 5]
        new_x5 = [row for row in new_rows if row["x_mm"] == 5]
        lines.append(metric_line(f"{scale_name}, só X=5", old_x5, new_x5, key))
    fixed_old_rmse = error_metrics(old_rows, "fixed_residual_v")[1]
    fixed_new_rmse = error_metrics(new_rows, "fixed_residual_v")[1]
    historical_old_rmse = error_metrics(old_rows, "historical_residual_v")[1]
    historical_new_rmse = error_metrics(new_rows, "historical_residual_v")[1]
    lines += ["", f"Com o reteste, o RMSE da escala fixa de "
              f"−12,320751 V/T passa de **{fixed_old_rmse:.6f}** para "
              f"**{fixed_new_rmse:.6f} V**. A escala exploratória histórica "
              f"de −6,831328 V/T passa de **{historical_old_rmse:.6f}** para "
              f"**{historical_new_rmse:.6f} V**. A vantagem numérica da "
              "escala exploratória anterior diminui muito após a troca dos "
              "seis pontos; ela ainda tem RMSE ligeiramente menor na grade "
              "revisada, sem ter sido ajustada a ela. Essas métricas não identificam "
              "a montagem física nem autorizam escolher magnetização.", "",
              "## Seis posições substituídas", "",
              "ΔV é a tensão medida menos a referência aplicada da respectiva "
              "série. O resíduo usa a escala fixa de −12,320751 V/T "
              "em ambas as versões; portanto, a mudança de erro reflete "
              "somente os dados substituídos e a nova referência do reteste.", "",
              "| Lado | Y (mm) | ΔV anterior (V; substituído) | ΔV reteste (V; vigente) | Modelo sem reajuste (V) | Resíduo anterior (V) | Resíduo reteste (V) |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for side in SIDES:
        for y_mm in Y_MM:
            old = old_by_key[(side, 5, y_mm)]
            new = new_by_key[(side, 5, y_mm)]
            lines.append(f"| {side} | {y_mm:+d} | {old['observed_v']:+.6f} | "
                         f"{new['observed_v']:+.6f} | {new['fixed_predicted_v']:+.6f} | "
                         f"{old['fixed_residual_v']:+.6f} | "
                         f"{new['fixed_residual_v']:+.6f} |")
    lines += ["", "## Limites", "",
              "O reteste corrige as coordenadas declaradas de X=5 mm, mas "
              "a planilha não fornece posição física do elemento Hall, "
              "orientação sensível confirmada, magnetização medida ou "
              "distâncias físicas verificadas. A comparação mantém a "
              "hipótese de Y lateral ao comprimento; seu sinal e origem "
              "físicos não foram confirmados. As escalas elétricas não são "
              "magnetizações medidas. Os dados anteriores continuam úteis "
              "para histórico, mas **não entram na grade vigente**. "
              "Nenhuma nova escala foi ajustada **neste relatório**. Uma "
              "[análise exploratória posterior](mapeamento-hall-x5-escala-exploratoria.md) "
              "ajusta uma escala comum à grade revisada e identifica "
              "separadamente os erros avaliados nos próprios pontos.", "",
              "Reproduza com `.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/hall_grid_x5_revision.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REVISED_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    old_points, _ = load_grid(SOURCE)
    revised_points, _ = load_grid(args.source)
    write_outputs(args.source, args.output, old_points, revised_points)
    print("30 posições vigentes; seis retestadas em X=5; comparação sem novo ajuste")


if __name__ == "__main__":
    main()
