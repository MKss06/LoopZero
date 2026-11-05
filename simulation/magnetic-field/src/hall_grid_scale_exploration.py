"""Examina resíduos da grade e ajusta somente uma escala elétrica exploratória."""

from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from hall_grid_analysis import (
    OUTPUT, PREVIOUS_SCALE_V_PER_T, SIDES, SOURCE, X_MM, Y_MM,
    GridPoint, _matrix, comparison_rows, load_grid,
)


STEM = "mapeamento-hall-escala-exploratoria"


@dataclass(frozen=True)
class Metrics:
    count: int
    bias_v: float
    mae_v: float
    rmse_v: float


def metrics(rows: list[dict[str, object]], residual_key: str) -> Metrics:
    if not rows:
        raise ValueError("Métricas exigem ao menos uma posição")
    residuals = np.asarray([row[residual_key] for row in rows], dtype=float)
    return Metrics(len(rows), float(np.mean(residuals)), float(np.mean(np.abs(residuals))),
                   float(np.sqrt(np.mean(np.square(residuals)))))


def fit_common_scale(rows: list[dict[str, object]]) -> float:
    """Mínimos quadrados sem intercepto; cada média de posição tem peso igual."""
    if len(rows) != 30 or {(row["side"], row["x_mm"], row["y_mm"])
                           for row in rows} != {(side, x, y) for side in SIDES
                                               for x in X_MM for y in Y_MM}:
        raise ValueError("Esperadas as mesmas 30 posições da grade")
    field_t = np.asarray([row["bz_reference_mt"] / 1000 for row in rows], dtype=float)
    observed_v = np.asarray([row["delta_v_observed_v"] for row in rows], dtype=float)
    denominator = float(np.dot(field_t, field_t))
    if denominator <= 0 or not np.isfinite(denominator):
        raise ValueError("Campo de referência inválido para ajustar escala")
    return float(np.dot(field_t, observed_v) / denominator)


def compare_scales(points: list[GridPoint]) -> tuple[list[dict[str, object]], float]:
    fixed_rows = comparison_rows(points)
    fitted_scale = fit_common_scale(fixed_rows)
    rows = []
    for fixed in fixed_rows:
        field_t = fixed["bz_reference_mt"] / 1000
        fitted_v = fitted_scale * field_t
        observed_v = fixed["delta_v_observed_v"]
        rows.append({
            "side": fixed["side"], "x_mm": fixed["x_mm"], "y_mm": fixed["y_mm"],
            "count": fixed["count"], "observed_v": observed_v,
            "bz_reference_mt": fixed["bz_reference_mt"],
            "fixed_predicted_v": fixed["delta_v_model_v"],
            "fixed_residual_v": fixed["residual_v"],
            "fitted_predicted_v": fitted_v,
            "fitted_residual_v": observed_v - fitted_v,
        })
    return rows, fitted_scale


def plot_residuals(rows: list[dict[str, object]], target: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 8.2), layout="constrained")
    variants = (("fixed_residual_v", "Escala anterior"),
                ("fitted_residual_v", "Escala comum exploratória"))
    for column, (key, label) in enumerate(variants):
        limit = max(abs(float(row[key])) for row in rows)
        for index, side in enumerate(SIDES):
            ax = axes[index, column]
            image = ax.imshow(_matrix(rows, side, key), origin="lower", aspect="auto",
                              cmap="RdBu_r", vmin=-limit, vmax=limit)
            ax.set(xticks=range(len(Y_MM)), xticklabels=Y_MM,
                   yticks=range(len(X_MM)), yticklabels=X_MM,
                   xlabel="Y nominal (mm)", ylabel="X nominal (mm)",
                   title=f"{side} · {label}")
            fig.colorbar(image, ax=ax, shrink=0.8, label="ΔV medido − calculado (V)")
    fig.suptitle("Resíduos nas 30 posições · cores com escala própria por coluna · X discreto")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def _metric_row(label: str, group: list[dict[str, object]]) -> str:
    fixed = metrics(group, "fixed_residual_v")
    fitted = metrics(group, "fitted_residual_v")
    return (f"| {label} | {fixed.count} | {fixed.bias_v:+.6f} | {fixed.mae_v:.6f} | "
            f"{fixed.rmse_v:.6f} | {fitted.bias_v:+.6f} | {fitted.mae_v:.6f} | "
            f"{fitted.rmse_v:.6f} |")


def write_outputs(source: Path, output: Path, points: list[GridPoint]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows, fitted_scale = compare_scales(points)
    with (output / f"{STEM}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "x_nominal_mm", "y_nominal_mm", "n", "delta_v_medido_v",
                         "bz_magpylib_referencia_1t_mt_nao_medido",
                         "delta_v_modelo_escala_anterior_v", "residuo_anterior_v",
                         "delta_v_modelo_escala_comum_exploratoria_v",
                         "residuo_escala_comum_exploratoria_v"))
        for row in rows:
            writer.writerow((row["side"], row["x_mm"], row["y_mm"], row["count"],
                             *(f"{row[key]:.9f}" for key in (
                                 "observed_v", "bz_reference_mt", "fixed_predicted_v",
                                 "fixed_residual_v", "fitted_predicted_v", "fitted_residual_v"))))
    plot_residuals(rows, output / f"{STEM}.png")
    previous = metrics(rows, "fixed_residual_v")
    exploratory = metrics(rows, "fitted_residual_v")
    reduction = 100 * (previous.rmse_v - exploratory.rmse_v) / previous.rmse_v
    by_key = {(row["side"], row["x_mm"], row["y_mm"]): row for row in rows}
    asymmetry = []
    for side in SIDES:
        for x_mm in X_MM:
            negative = by_key[(side, x_mm, -10)]
            positive = by_key[(side, x_mm, 10)]
            asymmetry.append((side, x_mm,
                              float(positive["observed_v"] - negative["observed_v"]),
                              float(positive["fixed_predicted_v"] - negative["fixed_predicted_v"])))
    largest = max(asymmetry, key=lambda item: abs(item[2]))
    lines = [
        "# Resíduos da grade Hall e escala comum exploratória", "",
        "**Análise histórica:** os seis valores X=5 mm usados aqui foram "
        "substituídos pelo [reteste vigente](mapeamento-hall-x5-revisado.md). "
        "A escala ajustada nesta página é mantida como referência anterior; "
        "seu erro nesta mesma grade não representa os dados corrigidos.", "",
        f"Fonte preservada: [grade Hall original](../../experiments/hall-sensor/mapeamento_hall_grade.xlsx) "
        f"(SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`). "
        "Foram usadas as **30 médias** já conferidas em [mapeamento-hall-horizontal.md]"
        "(mapeamento-hall-horizontal.md). Cada posição tem peso igual. "
        "As médias de blocos da planilha, referências sem ímã e conversão ADC–V "
        "não foram alteradas.", "",
        "## Escalas comparadas", "",
        f"A escala fixa é **{PREVIOUS_SCALE_V_PER_T:+.6f} V/T de campo de "
        "referência**, publicada para as 14 médias de 5–50 mm da coleta "
        "anterior. O ajuste exploratório de **uma única escala para os dois "
        "lados** usa `s = Σ(Bz_ref × ΔV) / Σ(Bz_ref²)`, sem intercepto, "
        f"nas 30 posições da nova grade: **{fitted_scale:+.6f} V/T de "
        "referência**. Somente essa escala foi ajustada. A geometria, "
        "polarização local +Z de 1 T como referência matemática, eixo "
        "candidato `vertical_z`, altura relativa de 0 mm e deslocamento "
        "nominal–físico de 0 mm permaneceram os mesmos. A escala combina "
        "magnetização real, sensibilidade elétrica e erros geométricos; "
        "não é magnetização medida.", "",
        "| Conjunto | Posições | Viés anterior (V) | MAE anterior (V) | RMSE anterior (V) | Viés exploratório (V) | MAE exploratório (V) | RMSE exploratório (V) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        _metric_row("Ambos os lados", rows),
    ]
    for side in SIDES:
        lines.append(_metric_row(side, [row for row in rows if row["side"] == side]))
    lines += ["", f"A redução do RMSE conjunto é **{reduction:.1f}%** dentro "
              "das mesmas posições usadas para o ajuste exploratório; "
              "não é validação em dados independentes. MAE, RMSE e viés "
              "continuam em volts medidos; nenhuma sensibilidade Hall "
              "individual foi inferida.", "",
              f"[Mapas de resíduos por lado]({STEM}.png) · "
              f"[Tabela completa por lado, X e Y]({STEM}.csv). "
              "Resíduo = ΔV medido − ΔV calculado. Cada coluna do gráfico "
              "tem escala de cor própria para revelar a estrutura espacial; "
              "compare valores pela legenda, não apenas pela cor. Os valores "
              "de X são posições discretas, sem espaçamento gráfico "
              "proporcional aos milímetros.", "",
              "## Resíduos por distância X", "",
              "| Lado e X nominal | Posições | Viés anterior (V) | MAE anterior (V) | RMSE anterior (V) | Viés exploratório (V) | MAE exploratório (V) | RMSE exploratório (V) |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for side in SIDES:
        for x_mm in X_MM:
            lines.append(_metric_row(f"{side}, X={x_mm} mm",
                                     [row for row in rows if row["side"] == side
                                      and row["x_mm"] == x_mm]))
    lines += ["", "## Resíduos por posição lateral Y", "",
              "| Lado e Y nominal | Posições | Viés anterior (V) | MAE anterior (V) | RMSE anterior (V) | Viés exploratório (V) | MAE exploratório (V) | RMSE exploratório (V) |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for side in SIDES:
        for y_mm in Y_MM:
            lines.append(_metric_row(f"{side}, Y={y_mm:+d} mm",
                                     [row for row in rows if row["side"] == side
                                      and row["y_mm"] == y_mm]))
    lines += ["", "## Padrões e limites", "",
              "Com a escala anterior, o modelo tende a superestimar o "
              "módulo de ΔV nos dois lados: viés negativo no lado 1 e "
              "positivo no lado 2. A tabela por X mostra em quais distâncias "
              "isso se concentra: em X=5 mm, o MAE anterior é 0,287 V no "
              "lado 1 e 0,263 V no lado 2. Com a escala exploratória, "
              "ainda é 0,081 V e 0,065 V, respectivamente. Em X=20 mm, "
              "o MAE do lado 2 sobe de 0,007 V para 0,013 V. Assim, a "
              "melhora global não elimina a estrutura por distância. "
              "A tabela por Y mostra a estrutura lateral, que uma escala "
              "uniforme não desloca nem torna assimétrica.", "",
              f"A maior diferença observada entre Y=+10 e Y=−10 mm ocorre em "
              f"**{largest[0]}, X={largest[1]} mm**: **{largest[2]:+.6f} V** "
              f"(modelo simétrico: {largest[3]:+.6f} V). A hipótese geométrica "
              "adotada produz a mesma previsão em ±10 mm. Essa assimetria "
              "observada não pode ser eliminada por um fator comum de escala; "
              "pode indicar deslocamento lateral, orientação ou diferença "
              "entre as condições de coleta, sem identificar qual delas.", "",
              "A planilha não contém as leituras seriais individuais nem "
              "coordenadas físicas verificadas do elemento Hall. O eixo "
              "sensível e o sinal do chip na montagem, a altura relativa, "
              "o zero físico e a magnetização do ímã permanecem incertos. "
              "O campo em mT da grade usa **14 mV/mT típicos do SS49E "
              "Honeywell**, sem calibração individual; esta comparação de "
              "resíduos permanece em ΔV (V). Não se conclui que a escala "
              "exploratória seja propriedade física da peça ou do sensor.", "",
              "Reproduza com `.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/hall_grid_scale_exploration.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    points, _ = load_grid(args.source)
    write_outputs(args.source, args.output, points)
    print("30 posições; escala comum exploratória e resíduos por lado, X e Y")


if __name__ == "__main__":
    main()
