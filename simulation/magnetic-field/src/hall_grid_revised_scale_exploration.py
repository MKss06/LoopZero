"""Ajusta uma escala comum à grade Hall vigente, sem mudar o modelo horizontal."""

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
    OUTPUT, PREVIOUS_SCALE_V_PER_T, REVISED_SOURCE, SIDES, X_MM, Y_MM,
    GridPoint, _matrix, load_grid,
)
from hall_grid_scale_exploration import compare_scales, metrics


STEM = "mapeamento-hall-x5-escala-exploratoria"


def plot_maps(rows: list[dict[str, object]], target: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.5), layout="constrained")
    limit = max(abs(float(row[key])) for row in rows for key in
                ("observed_v", "fixed_predicted_v", "fitted_predicted_v"))
    columns = (("observed_v", "ΔV medido (V)"),
               ("fixed_predicted_v", "Modelo · escala fixa (V)"),
               ("fitted_predicted_v", "Modelo · escala exploratória (V)"))
    for index, side in enumerate(SIDES):
        for column, (key, title) in enumerate(columns):
            ax = axes[index, column]
            image = ax.imshow(_matrix(rows, side, key), origin="lower", aspect="auto",
                              cmap="RdBu_r", vmin=-limit, vmax=limit)
            ax.set(xticks=range(len(Y_MM)), xticklabels=Y_MM,
                   yticks=range(len(X_MM)), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)",
                   title=f"{side} · {title}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="V")
    fig.suptitle("Grade vigente · valores medidos e calculados · cores em escala comum")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def plot_residuals(rows: list[dict[str, object]], target: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 8), layout="constrained")
    limit = max(abs(float(row[key])) for row in rows
                for key in ("fixed_residual_v", "fitted_residual_v"))
    for index, side in enumerate(SIDES):
        for column, (key, title) in enumerate((
            ("fixed_residual_v", "Escala fixa −12,320751 V/T"),
            ("fitted_residual_v", "Escala exploratória · ajuste nos 30 pontos"),
        )):
            ax = axes[index, column]
            image = ax.imshow(_matrix(rows, side, key), origin="lower", aspect="auto",
                              cmap="RdBu_r", vmin=-limit, vmax=limit)
            ax.set(xticks=range(len(Y_MM)), xticklabels=Y_MM,
                   yticks=range(len(X_MM)), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)",
                   title=f"{side} · {title}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="Medido − modelo (V)")
    fig.suptitle("Resíduos da grade vigente · mesma escala de cor nos quatro mapas")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def metric_row(label: str, rows: list[dict[str, object]]) -> str:
    fixed = metrics(rows, "fixed_residual_v")
    fitted = metrics(rows, "fitted_residual_v")
    return (f"| {label} | {fixed.count} | {fixed.mae_v:.6f} | {fixed.rmse_v:.6f} | "
            f"{fitted.mae_v:.6f} | {fitted.rmse_v:.6f} |")


def write_outputs(source: Path, output: Path, points: list[GridPoint]) -> float:
    output.mkdir(parents=True, exist_ok=True)
    rows, fitted_scale = compare_scales(points)
    if len(rows) != 30 or len({(row["side"], row["x_mm"], row["y_mm"])
                               for row in rows}) != 30:
        raise ValueError("A grade vigente precisa ter 30 posições únicas")
    with (output / f"{STEM}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm", "n",
                         "delta_v_medido_v", "bz_magpylib_referencia_1t_mt_nao_medido",
                         "delta_v_modelo_escala_fixa_v", "residuo_escala_fixa_v",
                         "delta_v_modelo_escala_exploratoria_ajustada_nestes_30_pontos_v",
                         "residuo_escala_exploratoria_ajustada_nestes_30_pontos_v"))
        for row in rows:
            writer.writerow((row["side"], row["x_mm"], row["y_mm"], row["count"],
                             *(f"{row[key]:.9f}" for key in (
                                 "observed_v", "bz_reference_mt", "fixed_predicted_v",
                                 "fixed_residual_v", "fitted_predicted_v", "fitted_residual_v"))))
    plot_maps(rows, output / f"{STEM}-mapas.png")
    plot_residuals(rows, output / f"{STEM}-residuos.png")

    fixed = metrics(rows, "fixed_residual_v")
    fitted = metrics(rows, "fitted_residual_v")
    largest = {side: max((row for row in rows if row["side"] == side),
                         key=lambda row: abs(float(row["fitted_residual_v"])))
               for side in SIDES}
    lines = [
        "# Escala elétrica comum na grade Hall vigente", "",
        f"Fonte: [planilha revisada](../../experiments/hall-sensor/{source.name}) "
        f"(SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`). "
        "Usamos as **30 médias vigentes**, inclusive os seis retestes de X=5 mm; "
        "os valores substituídos não entram no ajuste. "
        "A [grade anterior e seu ajuste exploratório](mapeamento-hall-escala-exploratoria.md) "
        "permanecem históricos. As referências sem ímã são as conferidas na "
        "[revisão de X=5](mapeamento-hall-x5-revisado.md).", "",
        "## Método e métricas", "",
        "Cada posição tem peso igual. A componente candidata do campo calculada "
        "pelo Magpylib usa o mesmo modelo horizontal: Hall fixo, aproximação "
        "horizontal, virada rígida da mesma peça, polarização local +Z de "
        "referência (1 T matemático), projeção candidata `vertical_z`, "
        "altura relativa 0 mm e deslocamento nominal–físico 0 mm. "
        "Não foram ajustados geometria, orientação, eixo sensível ou referências. "
        "A escala é obtida por mínimos quadrados sem intercepto: "
        "`s = Σ(B_ref · ΔV) / Σ(B_ref²)`, com `B_ref` em T e `ΔV` em V, "
        "somando os **dois lados**.", "",
        f"Escala fixa anterior: **{PREVIOUS_SCALE_V_PER_T:+.6f} V/T**. "
        f"Nova escala **exploratória, ajustada nestes mesmos 30 pontos**: "
        f"**{fitted_scale:+.6f} V/T**. Ela não é magnetização medida nem "
        "sensibilidade Hall calibrada; a avaliação a seguir é feita no "
        "próprio conjunto do ajuste e não é validação independente.", "",
        "| Conjunto | Posições | MAE fixa (V) | RMSE fixa (V) | MAE exploratória (V) | RMSE exploratória (V) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        metric_row("Ambos os lados", rows),
    ]
    for side in SIDES:
        lines.append(metric_row(side, [row for row in rows if row["side"] == side]))
    lines += ["", f"No conjunto usado, o RMSE cai de {fixed.rmse_v:.6f} "
              f"para {fitted.rmse_v:.6f} V ({100*(fixed.rmse_v-fitted.rmse_v)/fixed.rmse_v:.1f}%). "
              "Essa redução descreve somente o ajuste interno.", "",
              f"[Tabela com os 30 resíduos por lado, X e Y]({STEM}.csv) · "
              f"[Mapas de ΔV medido e calculado]({STEM}-mapas.png) · "
              f"[Mapas de resíduos]({STEM}-residuos.png). "
              "Resíduo = ΔV medido − ΔV calculado, em volts. Os mapas usam "
              "a mesma escala de cor entre as variantes; as linhas X são "
              "posições discretas.", "",
              "## Resíduos por lado e X nominal", "",
              "| Lado e X | Posições | MAE fixa (V) | RMSE fixa (V) | MAE exploratória (V) | RMSE exploratória (V) |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for side in SIDES:
        for x in X_MM:
            lines.append(metric_row(f"{side}, X={x} mm",
                                    [row for row in rows if row["side"] == side
                                     and row["x_mm"] == x]))
    lines += ["", "## Resíduos por lado e Y nominal", "",
              "| Lado e Y | Posições | MAE fixa (V) | RMSE fixa (V) | MAE exploratória (V) | RMSE exploratória (V) |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for side in SIDES:
        for y in Y_MM:
            lines.append(metric_row(f"{side}, Y={y:+d} mm",
                                    [row for row in rows if row["side"] == side
                                     and row["y_mm"] == y]))
    lines += ["", "## Estrutura dos resíduos e limites", ""]
    for side in SIDES:
        row = largest[side]
        lines.append(f"- {side}: maior resíduo absoluto após o ajuste em "
                     f"X={row['x_mm']} mm, Y={row['y_mm']:+d} mm: "
                     f"{row['fitted_residual_v']:+.6f} V.")
    lines += ["", "O modelo prevê valores iguais em Y=−10 e +10 mm para "
              "o mesmo lado e X; diferenças medidas entre essas posições, "
              "bem como padrões por distância, não podem ser removidos por "
              "uma escala multiplicativa comum. Os resíduos não identificam "
              "por si só a causa geométrica ou instrumental. A posição física "
              "do elemento Hall, seu eixo sensível, a magnetização da peça "
              "e a relação entre distância nominal e física continuam "
              "indeterminados. A conversão opcional de ΔV em mT usa "
              "14 mV/mT típicos do SS49E, sem calibração individual; este "
              "ajuste permanece integralmente em volts.", "",
              "Reproduza com `.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/hall_grid_revised_scale_exploration.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")
    return fitted_scale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REVISED_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    points, _ = load_grid(args.source)
    scale = write_outputs(args.source, args.output, points)
    print(f"30 posições vigentes; escala exploratória comum {scale:+.6f} V/T")


if __name__ == "__main__":
    main()
