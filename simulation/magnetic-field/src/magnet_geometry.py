"""Dimensões e montagem geométrica inicial, sem presumir propriedades magnéticas."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import magpylib as magpy
import numpy as np
from scipy.spatial.transform import Rotation


DATA_FILE = Path(__file__).resolve().parents[3] / "data" / "magnets" / "dimensions.csv"
MM_TO_M = Decimal("0.001")


@dataclass(frozen=True)
class MagnetDimensions:
    magnet_id: int
    length_mm: Decimal
    width_mm: Decimal
    thickness_mm: Decimal

    @property
    def dimension_m(self) -> tuple[float, float, float]:
        """Comprimento, largura e espessura nos eixos locais X, Y e Z."""
        return tuple(
            float(value * MM_TO_M)
            for value in (self.length_mm, self.width_mm, self.thickness_mm)
        )


def load_magnets(path: Path = DATA_FILE) -> tuple[MagnetDimensions, ...]:
    """Lê as medidas transcritas da tabela, preservando os decimais exatos."""
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        expected = ("magnet_id", "length_mm", "width_mm", "thickness_mm")
        if tuple(reader.fieldnames or ()) != expected:
            raise ValueError(f"Cabeçalhos inesperados em {path}")
        magnets = tuple(
            MagnetDimensions(
                magnet_id=int(row["magnet_id"]),
                length_mm=Decimal(row["length_mm"]),
                width_mm=Decimal(row["width_mm"]),
                thickness_mm=Decimal(row["thickness_mm"]),
            )
            for row in reader
        )
    if not magnets or len({m.magnet_id for m in magnets}) != len(magnets):
        raise ValueError("Tabela vazia ou com IDs duplicados")
    if any(min(m.length_mm, m.width_mm, m.thickness_mm) <= 0 for m in magnets):
        raise ValueError("Todas as dimensões devem ser positivas")
    return magnets


def dimensions_for(magnet_id: int | None = None) -> tuple[float, float, float]:
    """Retorna dimensões em metros; None seleciona a média representativa."""
    magnets = load_magnets()
    if magnet_id is not None:
        for magnet in magnets:
            if magnet.magnet_id == magnet_id:
                return magnet.dimension_m
        raise ValueError(f"Ímã {magnet_id} não consta na tabela")
    return tuple(float(mean * MM_TO_M) for mean in mean_dimensions_mm(magnets))


def mean_dimensions_mm(
    magnets: tuple[MagnetDimensions, ...] | None = None,
) -> tuple[Decimal, Decimal, Decimal]:
    """Média aritmética exata das três colunas, em milímetros."""
    if magnets is None:
        magnets = load_magnets()
    if not magnets:
        raise ValueError("Não há medidas para calcular a média")
    count = Decimal(len(magnets))
    return tuple(
        sum((getattr(m, field) for m in magnets), Decimal(0)) / count
        for field in ("length_mm", "width_mm", "thickness_mm")
    )


@dataclass(frozen=True)
class HallSetup:
    magnet: magpy.magnet.Cuboid
    sensor: magpy.Sensor
    approach_axis: np.ndarray
    hall_sensitive_axis_local: np.ndarray | None
    nominal_zero_to_sensitive_element_m: float | None

    def magnet_position_at(self, signed_displacement_m: float) -> np.ndarray:
        """Desloca uma pose fornecida; não converte distâncias nominais em distâncias reais."""
        return self.magnet.position + signed_displacement_m * self.approach_axis

    @property
    def hall_sensitive_axis_global(self) -> np.ndarray | None:
        """Eixo sensível no referencial global, se medido e informado."""
        if self.hall_sensitive_axis_local is None:
            return None
        return self.sensor.orientation.apply(self.hall_sensitive_axis_local)


def build_hall_setup(
    *,
    magnet_position_m: tuple[float, float, float],
    magnet_orientation: Rotation,
    sensor_position_m: tuple[float, float, float],
    sensor_orientation: Rotation,
    magnetization_a_per_m: tuple[float, float, float] | None = None,
    polarization_t: tuple[float, float, float] | None = None,
    hall_sensitive_axis_local: tuple[float, float, float] | None = None,
    nominal_zero_to_sensitive_element_m: float | None = None,
) -> HallSetup:
    """Cria a geometria B com poses explícitas; sem magnetização, não calcula campo.

    Convenção: Z global é vertical; X local do ímã é o lado maior e fica
    horizontal. O plano de referência do sensor é seu XY local. A aproximação
    segue o eixo normal ±Z local do sensor; o sinal do deslocamento é livre.
    Magnetização (A/m) ou polarização (T) é um vetor nos eixos locais do ímã.
    O eixo sensível do Hall, também local, e o deslocamento do zero nominal
    permanecem None até serem determinados. O Cuboid do ensaio usa sempre a
    média dos dez ímãs; nenhuma linha é atribuída à peça ensaiada.
    """
    if not isinstance(magnet_orientation, Rotation) or not isinstance(sensor_orientation, Rotation):
        raise TypeError("As orientações devem ser objetos scipy Rotation")
    if magnetization_a_per_m is not None and polarization_t is not None:
        raise ValueError("Informe magnetização ou polarização, não ambas")
    if not np.isclose(magnet_orientation.apply((1, 0, 0))[2], 0.0, atol=1e-8):
        raise ValueError("O eixo do comprimento do ímã deve ficar horizontal")
    sensitive_axis = None
    if hall_sensitive_axis_local is not None:
        sensitive_axis = np.asarray(hall_sensitive_axis_local, dtype=float)
        if sensitive_axis.shape != (3,) or not np.all(np.isfinite(sensitive_axis)):
            raise ValueError("O eixo sensível deve ter três componentes finitas")
        magnitude = np.linalg.norm(sensitive_axis)
        if magnitude == 0:
            raise ValueError("O eixo sensível não pode ser nulo")
        sensitive_axis = sensitive_axis / magnitude
    if nominal_zero_to_sensitive_element_m is not None and not math.isfinite(nominal_zero_to_sensitive_element_m):
        raise ValueError("O deslocamento do zero nominal deve ser finito")
    magnet = magpy.magnet.Cuboid(
        dimension=dimensions_for(),
        position=magnet_position_m,
        orientation=magnet_orientation,
        magnetization=magnetization_a_per_m,
        polarization=polarization_t,
    )
    sensor = magpy.Sensor(position=sensor_position_m, orientation=sensor_orientation)
    approach_axis = sensor_orientation.apply((0, 0, 1))
    return HallSetup(
        magnet=magnet,
        sensor=sensor,
        approach_axis=approach_axis,
        hall_sensitive_axis_local=sensitive_axis,
        nominal_zero_to_sensitive_element_m=nominal_zero_to_sensitive_element_m,
    )
