"""Confere a nova fonte, a deriva e a superposição de cinco ímãs."""

import sys
import csv
import tempfile
import unittest
from pathlib import Path

import magpylib as magpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compare_hall_mountings import AXES_LOCAL, mounting_setup  # noqa: E402
from hall_five_magnets import (  # noqa: E402
    ADC_TO_V, MAGNET_COUNT, SOURCE, STEM, comparison_rows, five_magnet_field_t,
    load_collection, write_outputs,
)
from hall_grid_analysis import MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM, PREVIOUS_SCALE_V_PER_T  # noqa: E402
from magnet_geometry import dimensions_for  # noqa: E402


class HallFiveMagnetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points, cls.refs = load_collection()
        cls.rows = comparison_rows(cls.points, cls.refs)

    def test_30_means_and_reference_drift(self):
        self.assertEqual(len(self.points), 30)
        self.assertEqual(sum(p.count for p in self.points), 1331)
        self.assertEqual((self.refs.initial_count, self.refs.final_count), (89, 42))
        self.assertAlmostEqual(self.refs.initial_adc, 535.6629213483)
        self.assertAlmostEqual(self.refs.final_adc, 533.0)
        self.assertAlmostEqual(self.refs.drift_v, -0.01301525585679355, places=11)
        for row in self.rows:
            self.assertAlmostEqual(row["delta_final_v"] - row["delta_initial_v"],
                                   -self.refs.drift_v)
            self.assertAlmostEqual(row["delta_middle_v"],
                                   (row["delta_initial_v"] + row["delta_final_v"]) / 2)
            self.assertAlmostEqual(row["mean_voltage_v"], row["mean_adc"] * ADC_TO_V)

    def test_five_cuboids_use_width_pitch_and_rigid_flip(self):
        width_m = dimensions_for()[1]
        for side in ("Lado 1", "Lado 2"):
            setup = mounting_setup(side, 5, MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM)
            manual = 0.0
            for index in range(MAGNET_COUNT):
                magnet = setup.magnet.copy()
                magnet.position = np.asarray(setup.magnet.position) + [index * width_m, 0, 0]
                manual += float(np.dot(magpy.getB(magnet, setup.sensor),
                                       AXES_LOCAL["vertical_z"]))
            self.assertAlmostEqual(five_magnet_field_t(side, 5, 0), manual, places=12)
        self.assertAlmostEqual(five_magnet_field_t("Lado 1", 5, 0),
                               -five_magnet_field_t("Lado 2", 5, 0), places=12)

    def test_photo_axis_sequence_and_lateral_y_displacement(self):
        width_m = dimensions_for()[1]
        for side in ("Lado 1", "Lado 2"):
            setup = mounting_setup(side, 20, MODEL_SENSOR_HEIGHT_MM, MODEL_ZERO_OFFSET_MM)
            centers = [np.asarray(setup.magnet.position) + [i * width_m, -0.01, 0]
                       for i in range(MAGNET_COUNT)]
            self.assertTrue(all(np.isclose(center[0], 0.02 + (i + 0.5) * width_m)
                                for i, center in enumerate(centers)))
            self.assertTrue(all(np.isclose(center[1], -0.01) for center in centers))
            for left, right in zip(centers, centers[1:]):
                self.assertAlmostEqual(right[0] - width_m / 2 -
                                       (left[0] + width_m / 2), 0.0, places=12)
            manual = 0.0
            for center in centers:
                magnet = setup.magnet.copy()
                magnet.position = center
                manual += float(np.dot(magpy.getB(magnet, setup.sensor),
                                       AXES_LOCAL["vertical_z"]))
            self.assertAlmostEqual(five_magnet_field_t(side, 20, 10), manual, places=12)

    def test_candidate_projection_preserves_observed_approach_signs(self):
        for side, expected_sign in (("Lado 1", 1), ("Lado 2", -1)):
            selected = [row for row in self.rows if row["side"] == side]
            self.assertEqual(len(selected), 15)
            self.assertTrue(all(expected_sign * row["model_delta_v"] > 0
                                for row in selected))
            for y_mm in (-10, 0, 10):
                far = next(row for row in selected if row["x_mm"] == 50 and
                           row["y_mm"] == y_mm)
                near = next(row for row in selected if row["x_mm"] == 5 and
                            row["y_mm"] == y_mm)
                self.assertGreater(expected_sign *
                                   (near["mean_voltage_v"] - far["mean_voltage_v"]), 0)

    def test_fixed_scale_and_reference_envelope(self):
        self.assertEqual(len(self.rows), 30)
        for row in self.rows:
            self.assertAlmostEqual(row["model_delta_v"],
                                   PREVIOUS_SCALE_V_PER_T * row["model_field_reference_t"])
            self.assertAlmostEqual(row["residual_initial_v"],
                                   row["delta_initial_v"] - row["model_delta_v"])
            self.assertAlmostEqual(row["residual_final_v"],
                                   row["delta_final_v"] - row["model_delta_v"])
            self.assertAlmostEqual(row["predicted_voltage_initial_v"],
                                   row["reference_initial_voltage_v"] + row["model_delta_v"])
            self.assertAlmostEqual(row["predicted_voltage_final_v"],
                                   row["reference_final_voltage_v"] + row["model_delta_v"])
            self.assertAlmostEqual(row["residual_initial_v"],
                                   row["mean_voltage_v"] - row["predicted_voltage_initial_v"])
            self.assertAlmostEqual(row["residual_final_v"] - row["residual_initial_v"],
                                   -self.refs.drift_v)
            self.assertGreaterEqual(row["distance_to_reference_band_v"], 0)
        self.assertEqual(sum(row["distance_to_reference_band_v"] < 1e-12
                             for row in self.rows), 3)

    def test_point_table_has_measured_and_predicted_voltage_for_30_positions(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            write_outputs(SOURCE, output, self.points, self.refs)
            with (output / f"{STEM}-ponto-a-ponto.csv").open(encoding="utf-8", newline="") as stream:
                exported = list(csv.DictReader(stream))
            self.assertEqual(len(exported), 30)
            self.assertEqual(len({(r["lado"], r["x_nominal_mm"], r["y_nominal_mm"])
                                  for r in exported}), 30)
            for row in exported:
                measured = float(row["tensao_media_medida_v"])
                for label in ("inicial", "final"):
                    predicted = float(row[f"tensao_total_prevista_ref_{label}_v"])
                    residual = float(row[f"residuo_ref_{label}_v"])
                    self.assertAlmostEqual(measured - predicted, residual, places=9)


if __name__ == "__main__":
    unittest.main()
