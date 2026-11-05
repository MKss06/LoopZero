"""Compara estimativa condicional em mT com o modelo Hall horizontal."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from compare_hall_mountings import fit_scale, template
from hall_analysis import (
    ASSUMED_SENSITIVITY_MV_PER_MT, OUTPUT, ROOT, SOURCE, Result,
    _workbook_sheets, calculate, estimated_field_mt, load_readings,
    verify_comparison,
)


AXIS = "vertical_z"  # candidato, não orientação sensível medida
HEIGHT_MM = 2.24  # coincide com o centro do ímã; hipótese, não medida
OFFSET_MM = 0.0  # distância física = nominal + deslocamento; hipótese
POLARIZATION_REFERENCE_T = 1.0  # template Magpylib, não polarização medida
STEM = "comparacao-campo-estimado-horizontal"
HONEYWELL_DATASHEET = (
    "https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/"
    "products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/"
    "documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf"
)


def comparison_rows(results: list[Result], height_mm: float = HEIGHT_MM,
                    offset_mm: float = OFFSET_MM) -> tuple[list[dict[str, object]], float]:
    """Ajusta só a escala comum nos 14 pontos e deixa 0 mm fora do ajuste."""
    fit = fit_scale(results, AXIS, height_mm, offset_mm)
    if fit.scale_v_per_t is None:
        raise ValueError("A componente Z não permite ajustar a escala")
    # 14 mV/mT equivale numericamente a 14 V/T. O quociente abaixo é
    # amplitude efetiva sob uma hipótese elétrica, não magnetização medida.
    effective_amplitude = fit.scale_v_per_t / ASSUMED_SENSITIVITY_MV_PER_MT
    rows = []
    for result in results:
        b_reference_mt = template(result.side, result.distance_mm, AXIS,
                                  height_mm, offset_mm) * 1000
        b_estimated_mt = estimated_field_mt(result.delta_v_mv)
        b_model_mt = effective_amplitude * b_reference_mt
        rows.append({
            "side": result.side,
            "distance_mm": result.distance_mm,
            "count": result.count,
            "used_for_fit": result.distance_mm >= 5,
            "reference_v": result.reference_voltage_v,
            "delta_v_v": result.delta_v_mv / 1000,
            "estimated_mt": b_estimated_mt,
            "model_reference_mt": b_reference_mt,
            "model_scaled_mt": b_model_mt,
            "residual_mt": b_estimated_mt - b_model_mt,
        })
    return rows, effective_amplitude


def plot_comparison(rows: list[dict[str, object]], target: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    colors = {"Lado 1": "#1764a3", "Lado 2": "#c95b24"}
    for side in colors:
        series = [row for row in rows if row["side"] == side and row["used_for_fit"]]
        x = [row["distance_mm"] for row in series]
        axes[0].scatter(x, [row["estimated_mt"] for row in series], color=colors[side],
                        label=f"{side}: estimativa de ΔV", zorder=3)
        axes[0].plot(x, [row["model_scaled_mt"] for row in series], color=colors[side],
                     label=f"{side}: modelo Z escalado")
        zero = next(row for row in rows if row["side"] == side and row["distance_mm"] == 0)
        index = 0 if side == "Lado 1" else 1
        axes[1].scatter(index - 0.1, zero["estimated_mt"], color=colors[side], s=65,
                        label="Estimativa de medição" if index == 0 else None)
        axes[1].scatter(index + 0.1, zero["model_scaled_mt"], color=colors[side],
                        marker="x", s=85, label="Cálculo extrapolado" if index == 0 else None)
    axes[0].set(xlabel="Distância nominal (mm)", ylabel="Campo condicional (mT)",
                title="5–50 mm: 14 médias usadas na escala")
    axes[0].legend(fontsize=8)
    axes[1].set(xticks=(0, 1), xticklabels=("Lado 1", "Lado 2"),
                ylabel="Campo condicional (mT)", title="0 mm nominal: fora do ajuste")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.axhline(0, color="#555", linewidth=0.8)
        ax.grid(alpha=0.23)
    fig.suptitle("14 mV/mT: sensibilidade típica SS49E Honeywell assumida; kit Elegoo 49E não calibrado")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def write_outputs(source: Path, output: Path, results: list[Result]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows, effective_amplitude = comparison_rows(results)
    csv_path = output / f"{STEM}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow((
            "lado", "distancia_nominal_mm", "n", "usado_no_ajuste",
            "referencia_sem_ima_v", "delta_v_medido_v",
            "campo_estimado_mt_ss49e_tipico_14mv_por_mt_nao_calibrado",
            "bz_magpylib_referencia_1t_mt_nao_medido",
            "bz_modelo_escala_efetiva_mt_nao_calibrado",
            "residuo_estimativa_menos_modelo_mt_nao_calibrado",
        ))
        for row in rows:
            writer.writerow((row["side"], row["distance_mm"], row["count"],
                             "sim" if row["used_for_fit"] else "nao",
                             *(f"{row[key]:.9f}" for key in (
                                 "reference_v", "delta_v_v", "estimated_mt",
                                 "model_reference_mt", "model_scaled_mt", "residual_mt"))))
    plot_comparison(rows, output / f"{STEM}.png")
    fit_rows = [row for row in rows if row["used_for_fit"]]
    mae_mt = sum(abs(row["residual_mt"]) for row in fit_rows) / len(fit_rows)
    rmse_mt = (sum(row["residual_mt"] ** 2 for row in fit_rows) / len(fit_rows)) ** 0.5
    try:
        source_label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source_label = str(source)
    lines = [
        "# Estimativa condicional de campo × Magpylib horizontal", "",
        "O experimentador identificou o sensor como Honeywell SS49E do kit "
        "Elegoo de 37 sensores. **14 mV/mT é a sensibilidade típica adotada "
        "da ficha Honeywell; esta unidade não foi calibrada individualmente.** "
        "A ficha técnica Honeywell indica 1,4 mV/G a 25 °C, que equivale a "
        f"14 mV/mT: [fonte]({HONEYWELL_DATASHEET}). O campo abaixo é "
        "**estimado a partir de tensões**, não medido por um instrumento "
        "calibrado. Sinais em mT seguem a convenção de ΔV; o sentido físico "
        "depende do eixo sensível e da resposta elétrica reais.", "",
        f"Fonte experimental preservada: `{source_label}` "
        f"(SHA-256 `{hashlib.sha256(source.read_bytes()).hexdigest()}`). "
        "As 904 leituras e as referências sem ímã por lado foram conferidas "
        "contra a aba `Comparação`. `B_estimado = ΔV (mV) / 14`. "
        "As [tensões e curvas originais](resumo.md) continuam em V/mV.", "",
        "## Hipóteses do cálculo", "",
        "O [modelo horizontal](comparacao-horizontal.md) mantém o Hall fixo, "
        "o ímã em movimento em −X e a virada rígida entre lados. O comprimento "
        "está em +Y, a espessura em Z e a magnetização atravessando a "
        f"espessura é hipótese provisória. A polarização local de +{POLARIZATION_REFERENCE_T:g} T é "
        "somente a referência numérica usada pelo Magpylib, não uma medida.", "",
        "A componente escolhida é **Bz global**, candidato para o eixo sensível "
        "do Hall, que permanece desconhecido. O Hall é colocado na mesma "
        "altura do centro do ímã (altura relativa 0 mm) e o deslocamento "
        "físico − nominal é 0 mm. Assim, a lacuna física no cenário é "
        "`distância nominal + 0 mm`. Altura e deslocamento são hipóteses, "
        "não cotas medidas. A [análise de sensibilidade geométrica]"
        "(sensibilidade-geometrica-horizontal.md) mostra outras combinações.", "",
        "Nas 14 médias de 5–50 mm foi ajustada apenas uma escala elétrica "
        "comum aos lados, sem intercepto. Dividi-la pelos 14 V/T assumidos "
        f"resulta em um fator efetivo assinado de **{effective_amplitude:+.6f}** "
        "para a componente de referência de 1 T. Esse fator mistura "
        "magnetização, sensibilidade real, orientação e geometria. Não é "
        "magnetização medida nem calibração do sensor. "
        f"MAE = **{mae_mt:.3f} mT** e RMSE = **{rmse_mt:.3f} mT** apenas na "
        "escala condicional de 14 mV/mT, para os pontos de ajuste.", "",
        f"[Gráfico]({STEM}.png) · [Tabela CSV completa]({STEM}.csv). "
        "A componente bruta Magpylib é mostrada separadamente da versão "
        "com escala efetiva; nenhuma das duas é campo medido. Resíduo = "
        "estimativa de ΔV − modelo escalado.", "",
        "| Lado | d nominal (mm) | ΔV medido (V) | Campo estimado (mT; SS49E típico, não calibrado) | Bz Magpylib, 1 T ref. (mT; não medido) | Bz escalado (mT; não calibrado) | Resíduo (mT) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in fit_rows:
        lines.append(f"| {row['side']} | {row['distance_mm']} | {row['delta_v_v']:+.6f} | "
                     f"{row['estimated_mt']:+.3f} | {row['model_reference_mt']:+.3f} | "
                     f"{row['model_scaled_mt']:+.3f} | {row['residual_mt']:+.3f} |")
    lines += ["", "## 0 mm nominal: medição real e cálculo separado", "",
              "As tensões em 0 mm são medições reais da planilha. O campo "
              "estimado vem dessas medições e da sensibilidade típica assumida; "
              "o valor Magpylib nesse ponto é extrapolação **calculada**, fora "
              "do ajuste de 5–50 mm. Não foi uma previsão fornecida pelo "
              "experimentador. Os módulos estimados de 119,4 e 107,3 mT "
              "ultrapassam a faixa magnética típica de ±100 mT indicada na "
              "ficha do SS49E Honeywell; a extrapolação linear do chip do kit "
              "nessa posição não está validada.", "",
              "| Lado | ΔV medido (V) | Campo estimado (mT; SS49E típico, não calibrado) | Bz Magpylib, 1 T ref. (mT; não medido) | Bz escalado extrapolado (mT; não calibrado) |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for row in rows:
        if not row["used_for_fit"]:
            lines.append(f"| {row['side']} | {row['delta_v_v']:+.6f} | "
                         f"{row['estimated_mt']:+.3f} | {row['model_reference_mt']:+.3f} | "
                         f"{row['model_scaled_mt']:+.3f} |")
    lines += ["", "A concordância em 5–50 mm caracteriza somente a forma "
              "das curvas sob este cenário. A divergência em 0 mm indica que "
              "a extrapolação geométrica e a resposta elétrica não estão "
              "resolvidas. A conversão por 14 não acrescenta uma medição "
              "independente: os resíduos em mT são os resíduos em mV "
              "divididos por 14. Eixo sensível e sinal do Hall, magnetização, "
              "altura relativa e deslocamento do zero ainda precisam ser "
              "determinados.", "",
              "Reproduza com `.\\.venv\\Scripts\\python.exe "
              "simulation/magnetic-field/src/hall_field_estimate.py`.", ""]
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
    write_outputs(args.source, args.output, results)
    print(f"{len(readings)} leituras verificadas; campo estimado e modelo horizontal em {args.output}")


if __name__ == "__main__":
    main()
