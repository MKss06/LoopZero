"""Compara ΔV com a aproximação horizontal do mesmo ímã virado."""

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
from scipy.spatial.transform import Rotation

from hall_analysis import OUTPUT, ROOT, SOURCE, Result, _workbook_sheets, calculate, load_readings, verify_comparison
from magnet_geometry import build_hall_setup, dimensions_for


SIDES = ("Lado 1", "Lado 2")
# O eixo sensível real do AH49E não está identificado pelo registro da montagem.
# Vetores nos eixos LOCAIS do sensor cuja normal aponta para +X global.
AXES_LOCAL = {
    "normal_x": (0.0, 0.0, 1.0),   # +X global: direção de aproximação
    "vertical_z": (-1.0, 0.0, 0.0),  # +Z global: vertical à superfície
    "longitudinal_y": (0.0, 1.0, 0.0),  # +Y global: comprimento do ímã
}
ZERO_FIELD_TOLERANCE_T = 1e-12
STEM = "comparacao-horizontal"


@dataclass(frozen=True)
class Fit:
    scale_v_per_t: float | None
    mae_v: float
    rmse_v: float
    count: int


@dataclass(frozen=True)
class Row:
    side: str
    distance_mm: int
    count: int
    observed_v: float
    used_for_fit: bool
    predictions_v: dict[str, float]
    residuals_v: dict[str, float]


def mounting_setup(side: str, distance_mm: int, sensor_height_mm: float, zero_offset_mm: float):
    """Sensor parado; ímã desloca-se em −X ao passar de 50 para 0 mm.

    Z=0 é a superfície. A altura e o deslocamento do Hall são parâmetros de
    cenário, não medições. O giro local de 180° em X leva a polarização junto.
    """
    if side not in SIDES or distance_mm < 0 or zero_offset_mm < 0:
        raise ValueError("Lado ou distância inesperada")
    _, width_m, thickness_m = dimensions_for()
    base = Rotation.from_euler("z", 90, degrees=True)  # X local -> +Y global
    flip = Rotation.from_euler("x", 0 if side == SIDES[0] else 180, degrees=True)
    return build_hall_setup(
        magnet_position_m=((width_m / 2) + (distance_mm + zero_offset_mm) / 1000,
                           0.0, thickness_m / 2),
        magnet_orientation=base * flip,
        sensor_position_m=(0.0, 0.0, sensor_height_mm / 1000),
        sensor_orientation=Rotation.from_euler("y", 90, degrees=True),
        polarization_t=(0.0, 0.0, 1.0),  # hipótese: através da espessura da mesma peça
        nominal_zero_to_sensitive_element_m=zero_offset_mm / 1000,
    )


def template(side: str, distance_mm: int, axis: str,
             sensor_height_mm: float, zero_offset_mm: float = 0.0) -> float:
    if axis not in AXES_LOCAL:
        raise ValueError(f"Eixo candidato inesperado: {axis}")
    setup = mounting_setup(side, distance_mm, sensor_height_mm, zero_offset_mm)
    field_local_t = np.asarray(magpy.getB(setup.magnet, setup.sensor), dtype=float)
    projected_t = float(np.dot(field_local_t, AXES_LOCAL[axis]))
    return 0.0 if abs(projected_t) < ZERO_FIELD_TOLERANCE_T else projected_t


def fit_scale(results: list[Result], axis: str,
              sensor_height_mm: float, zero_offset_mm: float = 0.0) -> Fit:
    if len(results) != 16 or sum(r.distance_mm == 0 for r in results) != 2:
        raise ValueError("Esperadas 16 médias, com 0 mm para cada lado")
    selected = [r for r in results if r.distance_mm >= 5]
    if len(selected) != 14 or any(r.distance_mm > 50 for r in selected):
        raise ValueError("Esperadas 14 médias de 5 a 50 mm")
    field = np.array([template(r.side, r.distance_mm, axis, sensor_height_mm, zero_offset_mm)
                      for r in selected])
    observed = np.array([r.delta_v_mv / 1000 for r in selected])
    denominator = float(np.dot(field, field))
    scale = None if denominator == 0 else float(np.dot(field, observed) / denominator)
    predicted = np.zeros_like(field) if scale is None else scale * field
    residual = observed - predicted
    return Fit(scale, float(np.mean(np.abs(residual))),
               float(np.sqrt(np.mean(np.square(residual)))), 14)


def compare(results: list[Result], fits: dict[str, Fit],
            sensor_height_mm: float, zero_offset_mm: float) -> list[Row]:
    rows = []
    for r in results:
        observed = r.delta_v_mv / 1000
        predictions = {axis: (0.0 if fit.scale_v_per_t is None else
                              fit.scale_v_per_t * template(r.side, r.distance_mm, axis,
                                                           sensor_height_mm, zero_offset_mm))
                       for axis, fit in fits.items()}
        rows.append(Row(r.side, r.distance_mm, r.count, observed, r.distance_mm >= 5,
                        predictions, {axis: observed - value for axis, value in predictions.items()}))
    return rows


def write_schematic(output: Path) -> Path:
    """Salva esquema dos eixos ANTES de qualquer ajuste ou leitura da planilha."""
    output.mkdir(parents=True, exist_ok=True)
    target = output / "esquema-montagem-horizontal.svg"
    target.write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="980" height="415" viewBox="0 0 980 415">
<style>text{font:17px sans-serif;fill:#1b2430}.small{font:14px sans-serif}.surface{stroke:#666;stroke-width:4}.arrow{stroke:#087e8b;stroke-width:4;marker-end:url(#head)}.magnet{fill:#dbe8f5;stroke:#174b75;stroke-width:3}.hall{fill:#202734}</style>
<defs><marker id="head" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0 0 L9 3 L0 6 Z" fill="#087e8b"/></marker></defs>
<text x="30" y="30">Corte X–Z: esquema condicional, não fotografia nem cotas medidas</text>
<line class="surface" x1="35" y1="305" x2="945" y2="305"/><text x="750" y="332">superfície: Z = 0</text>
<rect class="hall" x="184" y="243" width="14" height="37"/><text x="47" y="180">Hall fixo</text><text x="35" y="201" class="small">elemento preto</text>
<rect class="magnet" x="585" y="220" width="240" height="85"/><text x="648" y="264">ímã, lado 1</text>
<line class="arrow" x1="566" y1="252" x2="260" y2="252"/><text x="360" y="235">50 → 0 mm, −X</text>
<line class="arrow" x1="85" y1="285" x2="150" y2="285"/><text x="75" y="270">+X</text>
<line class="arrow" x1="85" y1="285" x2="85" y2="210"/><text x="94" y="220">+Z</text>
<text x="435" y="354" class="small">+Y: comprimento horizontal, perpendicular a esta vista</text>
<text x="535" y="92">lado 2: giro de 180° em torno de Y / comprimento</text>
<path d="M665 110 C765 85 830 120 810 168" fill="none" class="arrow"/>
<text x="29" y="383" class="small">Altura do Hall, zero físico e eixo sensível: hipóteses; polarização local +Z gira com a peça.</text>
</svg>''', encoding="utf-8")
    return target


def plot_fit(rows: list[Row], fits: dict[str, Fit], target: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 7), sharex="col",
                             gridspec_kw={"height_ratios": (2, 1)}, layout="constrained")
    colors = {"Lado 1": "#1764a3", "Lado 2": "#c95b24"}
    for col, axis in enumerate(AXES_LOCAL):
        top, bottom = axes[:, col]
        for side in SIDES:
            series = sorted((r for r in rows if r.side == side and r.used_for_fit),
                            key=lambda r: r.distance_mm)
            x = [r.distance_mm for r in series]
            top.plot(x, [r.predictions_v[axis] for r in series], color=colors[side],
                     label=f"{side}: modelo")
            top.scatter(x, [r.observed_v for r in series], color=colors[side], s=22,
                        label=f"{side}: observado", zorder=3)
            bottom.scatter(x, [r.residuals_v[axis] for r in series], color=colors[side], s=22)
        top.set(title=f"{axis} · MAE {fits[axis].mae_v:.4f} V", ylabel="ΔV (V)")
        bottom.set(xlabel="Distância nominal (mm)", ylabel="Resíduo (V)")
        bottom.set_xticks((5, 10, 15, 20, 30, 40, 50))
        for plot_axis in (top, bottom):
            plot_axis.axhline(0, color="#555", linewidth=0.8)
            plot_axis.grid(alpha=0.23)
    axes[0, 0].legend(fontsize=8, ncol=2)
    fig.suptitle("Aproximação horizontal · projeções candidatas do Hall")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def plot_zero(rows: list[Row], target: Path) -> None:
    zero = {r.side: r for r in rows if not r.used_for_fit}
    fig, ax = plt.subplots(figsize=(9, 4.5), layout="constrained")
    x = np.arange(2)
    ax.scatter(x - 0.27, [zero[s].observed_v for s in SIDES],
               color="#222", s=60, label="Hall: medido")
    for shift, axis, color in ((-0.09, "normal_x", "#1764a3"),
                               (0.09, "vertical_z", "#c95b24"),
                               (0.27, "longitudinal_y", "#558b2f")):
        ax.scatter(x + shift, [zero[s].predictions_v[axis] for s in SIDES],
                   color=color, marker="x", s=75, label=f"Modelo calculado: {axis}")
    ax.set(xticks=x, xticklabels=SIDES, ylabel="ΔV (V)",
           title="0 mm nominal · fora do ajuste")
    ax.axhline(0, color="#555", linewidth=0.8)
    ax.grid(axis="y", alpha=0.23)
    ax.legend()
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_results(source: Path, output: Path, rows: list[Row], fits: dict[str, Fit],
                  sensor_height_mm: float, zero_offset_mm: float) -> None:
    with (output / f"{STEM}.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "distancia_nominal_mm", "n", "usado_no_ajuste",
                         "delta_v_observado_v", *(f"{axis}_previsto_v" for axis in AXES_LOCAL),
                         *(f"{axis}_residuo_v" for axis in AXES_LOCAL)))
        for r in rows:
            writer.writerow((r.side, r.distance_mm, r.count, "sim" if r.used_for_fit else "nao",
                             f"{r.observed_v:.9f}",
                             *(f"{r.predictions_v[axis]:.9f}" for axis in AXES_LOCAL),
                             *(f"{r.residuals_v[axis]:.9f}" for axis in AXES_LOCAL)))
    plot_fit(rows, fits, output / f"{STEM}.png")
    plot_zero(rows, output / f"{STEM}-zero.png")
    try:
        label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = str(source)
    lines = [
        "# Hall × Magpylib: aproximação horizontal e virada do mesmo ímã", "",
        "O [esquema dos eixos](esquema-montagem-horizontal.svg) é gerado **antes do ajuste**. "
        "Ele fixa Z como vertical da superfície, +X como eixo horizontal do Hall em "
        "direção ao ímã, e +Y como direção horizontal do comprimento. A seta de "
        "aproximação vai em −X quando a distância nominal cai de 50 a 0 mm.", "",
        "## Observado e assumido", "",
        "**Informado:** elemento Hall preto fixo na ponta do módulo, voltado para o "
        "ímã; aproximação horizontal; para o lado 2, a mesma peça foi virada "
        "para que a face antes apoiada ficasse para cima. Não há fotografia "
        "incorporada neste repositório; a geometria abaixo usa essa descrição. "
        "A identificação ‘lado 1 = Sul; lado 2 = Norte’ é provisória, dependente "
        "da resposta do AH49E e da orientação da face marcada, não uma medida de polos.", "",
        "**Hipóteses de cálculo:** comprimento local X → +Y global, largura local Y "
        "→ −X global, espessura local Z → +Z global no lado 1. O lado 2 é uma "
        "rotação rígida de 180° em torno do comprimento local X (global Y): "
        "o vetor de polarização local `(0,0,+1)` T permanece o mesmo dentro da "
        "peça e passa de +Z para −Z global. É uma referência matemática para a "
        "hipótese de magnetização **através da espessura**, não uma medição. "
        "Nenhuma face é chamada de Norte ou Sul pelo modelo. A descrição textual "
        "não estabelece se o comprimento estava paralelo ou transversal à "
        "trajetória; este cenário escolhe comprimento transversal (+Y). "
        "Uma aproximação pela extremidade largura × espessura exigiria outra pose.", "",
        "O Hall ideal está parado em `x=y=0`; seu plano frontal normal aponta "
        "para +X. O ímã se aproxima pela face lateral local +Y no lado 1 e "
        "local −Y no lado 2: ambas são faces comprimento × espessura, não a "
        "face maior horizontal. A face local −Z apoiada no lado 1 passa a +Z "
        "global (para cima) após a virada. Isto **não** implica que ela ficou "
        "voltada ao Hall, que está na direção horizontal da peça.", "",
        f"A altura do elemento Hall foi fixada provisoriamente em **{sensor_height_mm:.3f} mm** "
        "acima da superfície; a altura do centro do ímã é metade da espessura "
        "média, **2,240 mm**. "
        f"O deslocamento entre a marca nominal e o elemento sensível foi fixado em "
        f"**{zero_offset_mm:.3f} mm**. Esses valores não foram medidos. "
        "O alinhamento em Y também é assumido. A face próxima tem coordenada "
        "`x = d + deslocamento`; em 0 mm a superfície do cuboide alcança o "
        "plano x do Hall no modelo, sem afirmar contato físico no ensaio.", "",
        "**Projeções candidatas do campo:** `normal_x` (+X global, normal da "
        "frente do módulo), `vertical_z` (+Z global) e `longitudinal_y` (+Y "
        "global). O eixo sensível e o sinal de resposta reais do AH49E não foram "
        "extraídos da montagem; cada projeção é uma hipótese separada.", "",
        f"Fonte: `{label}` (SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`). "
        "As 904 leituras foram agregadas por lado e distância e conferidas "
        "contra a aba `Comparação`. Dimensões médias: 19,37 × 9,40 × 4,48 mm "
        "= `(0.01937, 0.00940, 0.00448)` m. Nenhum dos dez ímãs foi "
        "identificado como a peça do ensaio.", "",
        "## Ajuste das 14 médias de 5 a 50 mm", "",
        "Para cada projeção com campo não nulo, um único fator efetivo é ajustado "
        "aos dois lados por mínimos quadrados não ponderados, sem intercepto. "
        "O fator mistura polarização real, sensibilidade elétrica e geometria; "
        "não é magnetização medida nem calibração. Com template nulo, a escala "
        "é **não identificável**, e o resíduo exibido é o próprio ΔV observado.", "",
        "| Projeção candidata | Escala efetiva (V/T de referência) | MAE (V) | RMSE (V) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for axis, fit in fits.items():
        scale = "não identificável" if fit.scale_v_per_t is None else f"{fit.scale_v_per_t:.6f}"
        lines.append(f"| `{axis}` | {scale} | {fit.mae_v:.6f} | {fit.rmse_v:.6f} |")
    lines += ["", "O sinal da escala ajustada depende da escolha arbitrária de +Z "
              "local para a polarização de referência e do sentido positivo "
              "escolhido para a projeção. Escala negativa não identifica um "
              "polo magnético nem o sinal físico do AH49E.", "",
              "## Observação, previsão e resíduo (V)", "",
              f"[Gráfico de 5–50 mm]({STEM}.png) · [CSV com todas as projeções]({STEM}.csv). "
              "Resíduo = ΔV observado − previsto.", "",
              "| Lado | d (mm) | ΔV obs. | X previsto | X res. | Z previsto | Z res. | Y previsto | Y res. |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        if r.used_for_fit:
            values = [r.observed_v, r.predictions_v["normal_x"], r.residuals_v["normal_x"],
                      r.predictions_v["vertical_z"], r.residuals_v["vertical_z"],
                      r.predictions_v["longitudinal_y"], r.residuals_v["longitudinal_y"]]
            lines.append(f"| {r.side} | {r.distance_mm} | " + " | ".join(f"{v:+.6f}" for v in values) + " |")
    lines += ["", "## 0 mm nominal: medição real e cálculo separado", "",
              "As leituras Hall em 0 mm são **medições reais** transcritas na "
              "planilha. Somente os valores **calculados pelo modelo** nesse "
              "ponto são extrapolados a partir do ajuste de 5–50 mm; não foram "
              "fornecidos como previsões pelo experimentador. "
              f"[Gráfico de 0 mm]({STEM}-zero.png). Valores em volts; cálculos "
              "sensíveis à altura e à definição do zero.", "",
              "| Lado | ΔV obs. | X previsto | X res. | Z previsto | Z res. | Y previsto | Y res. |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        if not r.used_for_fit:
            values = [r.observed_v, r.predictions_v["normal_x"], r.residuals_v["normal_x"],
                      r.predictions_v["vertical_z"], r.residuals_v["vertical_z"],
                      r.predictions_v["longitudinal_y"], r.residuals_v["longitudinal_y"]]
            lines.append(f"| {r.side} | " + " | ".join(f"{v:+.6f}" for v in values) + " |")
    lines += ["", "## O que os resíduos permitem concluir", "",
              "Os resíduos comparam formas de curva **dentro das hipóteses** de "
              "altura, alinhamento e projeção. Um erro menor não identifica "
              "o eixo sensível, a magnetização ou um polo real: outras alturas, "
              "orientações e deslocamentos podem alterar as curvas. ΔV não foi "
              "convertido para mT. A direção/sinal de magnetização, o eixo e "
              "sinal de resposta do Hall, a altura do elemento sensível e o "
              "zero geométrico permanecem pendentes.", "",
              "Os ajustes desta página usam exclusivamente a trajetória "
              "horizontal, com o Hall fixo e a mesma peça virada rigidamente. "
              "Não identificam a montagem completa nem um campo calibrado em mT.", "",
              f"Versões: Python {sys.version.split()[0]}, Magpylib {magpy.__version__}, "
              f"SciPy {scipy.__version__}. Reproduza com "
              "`.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/compare_hall_mountings.py`.", ""]
    (output / f"{STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--sensor-height-mm", type=float, default=2.24,
                        help="Altura suposta do elemento Hall em relação à superfície")
    parser.add_argument("--zero-offset-mm", type=float, default=0.0,
                        help="Deslocamento suposto entre zero nominal e elemento Hall")
    args = parser.parse_args()
    if not np.isfinite(args.sensor_height_mm) or not np.isfinite(args.zero_offset_mm):
        parser.error("Altura e deslocamento devem ser finitos")
    if args.zero_offset_mm < 0:
        parser.error("O deslocamento deve ser não negativo")
    write_schematic(args.output)  # requisito: esquema antes do ajuste
    sheets = _workbook_sheets(args.source)
    readings = load_readings(sheets)
    references, results = calculate(readings)
    verify_comparison(sheets["Comparação"], references, results)
    fits = {axis: fit_scale(results, axis, args.sensor_height_mm, args.zero_offset_mm)
            for axis in AXES_LOCAL}
    rows = compare(results, fits, args.sensor_height_mm, args.zero_offset_mm)
    write_results(args.source, args.output, rows, fits,
                  args.sensor_height_mm, args.zero_offset_mm)
    print(f"{len(readings)} leituras; 14 médias de 5 a 50 mm; 0 mm fora")
    for axis, fit in fits.items():
        scale = "não identificável" if fit.scale_v_per_t is None else f"{fit.scale_v_per_t:.6f} V/T"
        print(f"{axis}: escala {scale}; MAE {fit.mae_v:.6f} V; RMSE {fit.rmse_v:.6f} V")


if __name__ == "__main__":
    main()
