"""Reproduz as tensões Hall e uma estimativa condicional de campo."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data" / "experiments" / "hall-sensor" / "loopzero_hall_tensao_distancia.xlsx"
OUTPUT = ROOT / "data" / "processed" / "hall-sensor"
MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
SIDES = ("Lado 1", "Lado 2")
DISTANCES_MM = (0, 5, 10, 15, 20, 30, 40, 50)
ASSUMED_SENSITIVITY_MV_PER_MT = 14.0  # SS49E Honeywell típico; chip Elegoo 49E não calibrado
FIELD_COLUMN = "campo_estimado_mt_ss49e_tipico_14mv_por_mt_nao_calibrado"


def estimated_field_mt(delta_v_mv: float) -> float:
    """Conversão provisória de ΔV em mV, com sinal definido pela tensão."""
    return delta_v_mv / ASSUMED_SENSITIVITY_MV_PER_MT


@dataclass(frozen=True)
class Reading:
    side: str
    distance_mm: int | None
    sample: int
    adc: int
    voltage_v: float
    condition: str


@dataclass(frozen=True)
class Result:
    side: str
    distance_mm: int
    count: int
    mean_voltage_v: float
    reference_voltage_v: float
    delta_v_mv: float


def _workbook_sheets(source: Path) -> dict[str, dict[int, dict[str, str]]]:
    """Lê valores armazenados no XLSX com a biblioteca padrão, sem recalcular fórmulas."""
    with ZipFile(source) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(item.text or "" for item in entry.iter(f"{MAIN_NS}t"))
                for entry in strings.findall(f"{MAIN_NS}si")
            ]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheets = {}
        for sheet in workbook.iter(f"{MAIN_NS}sheet"):
            target = targets[sheet.attrib[f"{REL_NS}id"]].lstrip("/")
            part = target if target.startswith("xl/") else f"xl/{target}"
            xml = ET.fromstring(archive.read(part))
            rows = {}
            for row in xml.iter(f"{MAIN_NS}row"):
                values = {}
                for cell in row.findall(f"{MAIN_NS}c"):
                    value = cell.find(f"{MAIN_NS}v")
                    inline = cell.find(f"{MAIN_NS}is")
                    content = value.text if value is not None else None
                    if cell.attrib.get("t") == "s" and content is not None:
                        content = shared[int(content)]
                    elif inline is not None:
                        content = "".join(item.text or "" for item in inline.iter(f"{MAIN_NS}t"))
                    if content is not None:
                        column = "".join(char for char in cell.attrib["r"] if char.isalpha())
                        values[column] = content
                rows[int(row.attrib["r"])] = values
            sheets[sheet.attrib["name"]] = rows
    return sheets


def load_readings(sheets: dict[str, dict[int, dict[str, str]]]) -> list[Reading]:
    if "Leituras" not in sheets or "Comparação" not in sheets:
        raise ValueError("A planilha deve conter as abas Leituras e Comparação")
    readings = []
    for row_number, row in sorted(sheets["Leituras"].items()):
        if row_number == 1:
            continue
        if not row.get("D") or not row.get("E"):
            raise ValueError(f"Leitura incompleta na linha {row_number}")
        condition = row.get("F", "")
        distance = int(row["B"]) if row.get("B") else None
        if row.get("A") not in SIDES or condition not in ("Com ímã", "Sem ímã"):
            raise ValueError(f"Lado ou condição inesperado na linha {row_number}")
        if (condition == "Sem ímã") != (distance is None):
            raise ValueError(f"Distância incompatível com a condição na linha {row_number}")
        if distance is not None and distance not in DISTANCES_MM:
            raise ValueError(f"Distância inesperada na linha {row_number}")
        readings.append(
            Reading(row["A"], distance, int(row["C"]), int(row["D"]), float(row["E"]), condition)
        )
    if len(readings) != 904:
        raise ValueError(f"Esperadas 904 leituras; encontradas {len(readings)}")
    return readings


def calculate(readings: list[Reading]) -> tuple[dict[str, tuple[float, int]], list[Result]]:
    groups: dict[tuple[str, str, int | None], list[float]] = defaultdict(list)
    for reading in readings:
        groups[(reading.side, reading.condition, reading.distance_mm)].append(reading.voltage_v)
    references = {}
    results = []
    for side in SIDES:
        baseline = groups[(side, "Sem ímã", None)]
        if not baseline:
            raise ValueError(f"Falta referência sem ímã para {side}")
        reference = fmean(baseline)
        references[side] = (reference, len(baseline))
        for distance in DISTANCES_MM:
            voltages = groups[(side, "Com ímã", distance)]
            if not voltages:
                raise ValueError(f"Faltam leituras de {side} em {distance} mm")
            mean = fmean(voltages)
            results.append(Result(side, distance, len(voltages), mean, reference, (mean - reference) * 1000))
    return references, results


def verify_comparison(
    rows: dict[int, dict[str, str]], references: dict[str, tuple[float, int]], results: list[Result]
) -> None:
    """Confere os valores armazenados na aba Comparação com os cálculos independentes."""
    by_key = {(r.side, r.distance_mm): r for r in results}
    for side, row_number in (("Lado 1", 5), ("Lado 2", 6)):
        if not math.isclose(references[side][0], float(rows[row_number]["B"]), abs_tol=1e-10):
            raise ValueError(f"Referência divergente para {side}")
    for row_number, distance in enumerate(DISTANCES_MM, start=8):
        row = rows[row_number]
        if int(row["A"]) != distance:
            raise ValueError(f"Distância divergente na linha {row_number} da aba Comparação")
        for side, mean_col, delta_col, count_col in (
            ("Lado 1", "B", "C", "D"),
            ("Lado 2", "E", "F", "G"),
        ):
            result = by_key[(side, distance)]
            if result.count != int(row[count_col]):
                raise ValueError(f"Contagem divergente: {side}, {distance} mm")
            if not math.isclose(result.mean_voltage_v, float(row[mean_col]), abs_tol=1e-9):
                raise ValueError(f"Média divergente: {side}, {distance} mm")
            if not math.isclose(result.delta_v_mv, float(row[delta_col]), abs_tol=1e-6):
                raise ValueError(f"ΔV divergente: {side}, {distance} mm")


def _plot(results: list[Result], output: Path, *, delta: bool) -> None:
    fig, ax = plt.subplots(figsize=(8.2, 4.8), layout="constrained")
    colors = {"Lado 1": "#1764a3", "Lado 2": "#c95b24"}
    for side in SIDES:
        series = [result for result in results if result.side == side]
        y = [result.delta_v_mv if delta else result.mean_voltage_v for result in series]
        ax.plot(DISTANCES_MM, y, marker="o", linewidth=2, markersize=5, label=side, color=colors[side])
        if not delta:
            ax.axhline(series[0].reference_voltage_v, color=colors[side], linestyle="--", alpha=0.55)
    if delta:
        ax.axhline(0, color="#555555", linewidth=0.8)
    ax.set(xlabel="Distância nominal (mm)",
           ylabel="ΔV em relação à referência do mesmo lado (mV)" if delta else "Tensão Hall média (V)",
           title="Diferença de tensão Hall por distância" if delta else "Tensão Hall por distância")
    ax.set_xticks(DISTANCES_MM)
    ax.grid(alpha=0.25)
    ax.legend(title="Lado da coleta")
    fig.savefig(output, dpi=180)
    plt.close(fig)


def write_outputs(
    source: Path, output: Path, readings: list[Reading],
    references: dict[str, tuple[float, int]], results: list[Result]
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with (output / "medias-por-distancia.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lado", "distancia_nominal_mm", "n", "tensao_media_v", "referencia_sem_ima_v", "delta_v_mv", FIELD_COLUMN))
        for result in results:
            writer.writerow((result.side, result.distance_mm, result.count,
                             f"{result.mean_voltage_v:.12f}", f"{result.reference_voltage_v:.12f}",
                             f"{result.delta_v_mv:.9f}", f"{estimated_field_mt(result.delta_v_mv):.9f}"))
    _plot(results, output / "tensao-distancia.png", delta=False)
    _plot(results, output / "delta-v-distancia.png", delta=True)
    sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    try:
        source_label = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source_label = str(source)
    by_key = {(r.side, r.distance_mm): r for r in results}
    lines = [
        "# Análise de tensão do sensor Hall",
        "",
        f"Fonte preservada: `{source_label}` (SHA-256 `{sha256}`).",
        f"Reproduzida com Python {sys.version.split()[0]} e Matplotlib {mpl.__version__}.",
        "",
        f"Foram analisadas **{len(readings)} leituras**: 831 com ímã e 73 referências sem ímã. "
        "As médias, contagens e ΔV conferem com a aba `Comparação`.",
        "",
        "Estimativa condicional: `B_estimado (mT) = ΔV (mV) / 14`, usando a referência sem ímã "
        "do mesmo lado. O experimentador identificou o sensor como Honeywell "
        "SS49E do kit Elegoo de 37 sensores. **14 mV/mT é a sensibilidade típica "
        "do fabricante (1,4 mV/G a 25 °C); a unidade não foi calibrada "
        "individualmente.** O sinal do campo estimado segue o sinal elétrico de ΔV; "
        "seu sentido físico depende do eixo e da resposta real do Hall. "
        "[Ficha técnica Honeywell](https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/magnetic-sensors/linear-and-angle-sensor-ics/common/documents/sps-siot-ss39et-ss49e-ss59et-product-sheet-005850-3-en-ciid-50359.pdf).", "",
        "| Lado | Referência sem ímã (V) | n referência | ΔV medido em 0 mm nominal (mV) | Campo estimado em 0 mm nominal (mT; SS49E típico, não calibrado) | ΔV medido em 50 mm (mV) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for side in SIDES:
        reference, count = references[side]
        lines.append(f"| {side} | {reference:.6f} | {count} | "
                     f"{by_key[(side, 0)].delta_v_mv:+.3f} | "
                     f"{estimated_field_mt(by_key[(side, 0)].delta_v_mv):+.3f} | "
                     f"{by_key[(side, 50)].delta_v_mv:+.3f} |")
    lines += [
        "",
        "As curvas mostram **tensões medidas**, inclusive em 0 mm nominal; 0 mm não é "
        "uma distância confirmada até o elemento sensível. Para o lado 2, o mesmo "
        "ímã foi virado: a face antes apoiada ficou para cima, enquanto o Hall "
        "permaneceu fixo e a aproximação foi horizontal. Essa face superior não "
        "é automaticamente a face voltada ao Hall. "
        "A planilha foi transcrita de mensagens, com linhas incompletas e leituras anteriores omitidas "
        "conforme suas notas; portanto, não representa o fluxo integral do instrumento.",
        "",
        "ΔV = média de tensão com ímã − referência sem ímã do mesmo lado. "
        "O campo em mT é apenas uma estimativa sob a sensibilidade típica assumida; "
        "não é campo medido por instrumento calibrado. Nenhuma magnetização foi "
        "ajustada a estes dados.",
        "",
        "Os 16 grupos e todas as contagens, médias e diferenças estão na "
        "[tabela de médias](medias-por-distancia.csv). Veja as curvas de "
        "[tensão](tensao-distancia.png) e [ΔV](delta-v-distancia.png), mantidas em volts "
        "e milivolts. A [comparação da estimativa de campo com o modelo horizontal]"
        "(comparacao-campo-estimado-horizontal.md) é calculada separadamente.",
        "",
        "Para reproduzir, na raiz do repositório, execute "
        "`.\\.venv\\Scripts\\python.exe simulation/magnetic-field/src/hall_analysis.py` "
        "no PowerShell, ou `python simulation/magnetic-field/src/hall_analysis.py` com o ambiente ativado.",
        "",
    ]
    (output / "resumo.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE, help="Planilha recebida")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Pasta para resultados derivados")
    args = parser.parse_args()
    sheets = _workbook_sheets(args.source)
    readings = load_readings(sheets)
    references, results = calculate(readings)
    verify_comparison(sheets["Comparação"], references, results)
    write_outputs(args.source, args.output, readings, references, results)
    print(f"Conferidas {len(readings)} leituras e {len(results)} médias; resultados em {args.output}")


if __name__ == "__main__":
    main()
