"""Verificações dos dados e da geometria, sem simular medições."""

import sys
import unittest
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from magnet_geometry import (  # noqa: E402
    build_hall_setup,
    dimensions_for,
    load_magnets,
    mean_dimensions_mm,
)


class MagnetGeometryTests(unittest.TestCase):
    def test_ten_records_and_exact_means(self):
        magnets = load_magnets()
        self.assertEqual([m.magnet_id for m in magnets], list(range(1, 11)))
        self.assertEqual(
            [(m.length_mm, m.width_mm, m.thickness_mm) for m in magnets],
            [
                tuple(map(Decimal, values))
                for values in (
                    ("19.0", "9.0", "4.0"),
                    ("19.0", "10.0", "4.5"),
                    ("19.0", "9.5", "4.1"),
                    ("20.0", "9.7", "4.3"),
                    ("19.5", "9.0", "5.0"),
                    ("19.6", "9.3", "4.5"),
                    ("19.5", "9.2", "4.7"),
                    ("19.7", "9.1", "5.0"),
                    ("19.3", "9.7", "4.1"),
                    ("19.1", "9.5", "4.6"),
                )
            ],
        )
        self.assertEqual(
            mean_dimensions_mm(magnets),
            (Decimal("19.37"), Decimal("9.40"), Decimal("4.48")),
        )

    def test_conversion_to_meters_and_row_selection(self):
        np.testing.assert_allclose(dimensions_for(), (0.01937, 0.00940, 0.00448))
        np.testing.assert_allclose(dimensions_for(4), (0.0200, 0.0097, 0.0043))
        with self.assertRaises(ValueError):
            dimensions_for(11)

    def test_csv_matches_original_workbook_and_mass_is_derived(self):
        source = Path(__file__).resolve().parents[3] / "data" / "magnets" / "dimensoes-imas-original.xlsx"
        ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        with ZipFile(source) as workbook:
            sheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        cells = {cell.attrib["r"]: cell for cell in sheet.iter(f"{ns}c")}

        def number(address):
            return Decimal(cells[address].find(f"{ns}v").text)

        for row_number, magnet in enumerate(load_magnets(), start=4):
            self.assertEqual(number(f"A{row_number}"), magnet.magnet_id)
            self.assertEqual(
                (number(f"B{row_number}"), number(f"C{row_number}"), number(f"D{row_number}")),
                (magnet.length_mm, magnet.width_mm, magnet.thickness_mm),
            )
            expected_mass_g = magnet.length_mm * magnet.width_mm * magnet.thickness_mm * Decimal("7.5") / 1000
            self.assertEqual(number(f"E{row_number}"), expected_mass_g)
        self.assertEqual(cells["E4"].find(f"{ns}f").text, "B4*C4*D4*7.5/1000")

    def test_sensor_normal_controls_approach_not_dimension_order(self):
        # Poses sintéticas para testar a transformação; não são dados do ensaio.
        setup = build_hall_setup(
            magnet_position_m=(0.1, 0.2, 0.3),
            magnet_orientation=Rotation.identity(),
            sensor_position_m=(0.0, 0.0, 0.0),
            sensor_orientation=Rotation.from_euler("y", 90, degrees=True),
        )
        np.testing.assert_allclose(setup.magnet.dimension, dimensions_for())
        np.testing.assert_allclose(setup.magnet.position, (0.1, 0.2, 0.3))
        np.testing.assert_allclose(setup.sensor.position, (0.0, 0.0, 0.0))
        np.testing.assert_allclose(setup.approach_axis, (1.0, 0.0, 0.0), atol=1e-15)
        np.testing.assert_allclose(setup.magnet_position_at(-0.01), (0.09, 0.2, 0.3))
        self.assertIsNone(setup.magnet.magnetization)
        self.assertIsNone(setup.hall_sensitive_axis_local)
        self.assertIsNone(setup.hall_sensitive_axis_global)
        self.assertIsNone(setup.nominal_zero_to_sensitive_element_m)

    def test_optional_sensor_parameters_remain_explicit(self):
        setup = build_hall_setup(
            magnet_position_m=(0.1, 0.2, 0.3),
            magnet_orientation=Rotation.identity(),
            sensor_position_m=(0.0, 0.0, 0.0),
            sensor_orientation=Rotation.from_euler("y", 90, degrees=True),
            hall_sensitive_axis_local=(0, 0, 2),
            nominal_zero_to_sensitive_element_m=0.002,
        )
        np.testing.assert_allclose(setup.hall_sensitive_axis_global, (1, 0, 0), atol=1e-15)
        self.assertEqual(setup.nominal_zero_to_sensitive_element_m, 0.002)

    def test_long_axis_must_remain_horizontal(self):
        with self.assertRaises(ValueError):
            build_hall_setup(
                magnet_position_m=(0.0, 0.0, 0.0),
                magnet_orientation=Rotation.from_euler("y", 90, degrees=True),
                sensor_position_m=(0.0, 0.0, 0.0),
                sensor_orientation=Rotation.identity(),
            )


if __name__ == "__main__":
    unittest.main()
