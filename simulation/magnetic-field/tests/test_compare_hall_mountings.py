"""Testes da trajetória horizontal, virada rígida e projeções candidatas."""

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compare_hall_mountings import (  # noqa: E402
    AXES_LOCAL, compare, fit_scale, mounting_setup, template, write_schematic,
)
from hall_analysis import SOURCE, _workbook_sheets, calculate, load_readings  # noqa: E402


class HorizontalComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = calculate(load_readings(_workbook_sheets(SOURCE)))[1]

    def test_fixed_hall_horizontal_approach_and_supported_face_flip(self):
        first_far = mounting_setup("Lado 1", 50, 2.24, 0)
        first_near = mounting_setup("Lado 1", 0, 2.24, 0)
        second = mounting_setup("Lado 2", 50, 2.24, 0)
        np.testing.assert_allclose(first_far.sensor.position, first_near.sensor.position)
        np.testing.assert_allclose(first_far.sensor.position, second.sensor.position)
        np.testing.assert_allclose(first_near.magnet.position - first_far.magnet.position,
                                   (-0.05, 0, 0), atol=1e-12)
        np.testing.assert_allclose(first_far.approach_axis, (1, 0, 0), atol=1e-12)
        for setup in (first_far, second):
            np.testing.assert_allclose(setup.magnet.orientation.apply((1, 0, 0)),
                                       (0, 1, 0), atol=1e-12)
            np.testing.assert_allclose(setup.magnet.polarization, (0, 0, 1))
            self.assertAlmostEqual(setup.magnet.position[2], 0.00448 / 2)
        np.testing.assert_allclose(first_far.magnet.orientation.apply((0, 0, 1)),
                                   -second.magnet.orientation.apply((0, 0, 1)), atol=1e-12)
        np.testing.assert_allclose(first_far.magnet.orientation.apply((0, 1, 0)),
                                   -second.magnet.orientation.apply((0, 1, 0)), atol=1e-12)

    def test_candidate_axes_and_height_dependence(self):
        setup = mounting_setup("Lado 1", 10, 2.24, 0)
        expected = {"normal_x": (1, 0, 0), "vertical_z": (0, 0, 1),
                    "longitudinal_y": (0, 1, 0)}
        for axis, global_axis in expected.items():
            np.testing.assert_allclose(setup.sensor.orientation.apply(AXES_LOCAL[axis]),
                                       global_axis, atol=1e-12)
        for distance in (0, 5, 20, 50):
            self.assertEqual(template("Lado 1", distance, "normal_x", 2.24), 0.0)
            self.assertEqual(template("Lado 1", distance, "longitudinal_y", 2.24), 0.0)
            self.assertAlmostEqual(template("Lado 1", distance, "vertical_z", 2.24),
                                   -template("Lado 2", distance, "vertical_z", 2.24), places=12)
        self.assertNotEqual(template("Lado 1", 10, "normal_x", 1.0), 0.0)

    def test_same_14_means_and_zero_excluded(self):
        fits = {axis: fit_scale(self.results, axis, 2.24) for axis in AXES_LOCAL}
        altered = [replace(r, delta_v_mv=r.delta_v_mv + 100000)
                   if r.distance_mm == 0 else r for r in self.results]
        for axis in AXES_LOCAL:
            self.assertEqual(fits[axis], fit_scale(altered, axis, 2.24))
            self.assertEqual(fits[axis].count, 14)
        self.assertIsNotNone(fits["vertical_z"].scale_v_per_t)
        self.assertIsNone(fits["normal_x"].scale_v_per_t)
        self.assertIsNone(fits["longitudinal_y"].scale_v_per_t)
        rows = compare(self.results, fits, 2.24, 0)
        self.assertEqual(sum(r.used_for_fit for r in rows), 14)
        for row in rows:
            for axis in AXES_LOCAL:
                self.assertAlmostEqual(row.residuals_v[axis],
                                       row.observed_v - row.predictions_v[axis])

    def test_schematic_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            content = write_schematic(Path(directory)).read_text(encoding="utf-8")
            self.assertIn("Hall fixo", content)
            self.assertIn("superfície", content)
            self.assertIn("50 → 0 mm, −X", content)
            self.assertIn("lado 2", content)


if __name__ == "__main__":
    unittest.main()
