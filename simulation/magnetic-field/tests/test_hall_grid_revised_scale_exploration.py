"""Verifica o ajuste comum na grade vigente, sem mudar a simulação."""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hall_grid_analysis import PREVIOUS_SCALE_V_PER_T, REVISED_SOURCE, X_MM, Y_MM, load_grid  # noqa: E402
from hall_grid_scale_exploration import compare_scales, metrics  # noqa: E402


class RevisedScaleExplorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = load_grid(REVISED_SOURCE)[0]
        cls.rows, cls.scale = compare_scales(cls.points)

    def test_one_scale_for_both_sides_and_no_intercept(self):
        self.assertEqual(len(self.rows), 30)
        self.assertEqual({(r["side"], r["x_mm"], r["y_mm"]) for r in self.rows},
                         {(side, x, y) for side in ("Lado 1", "Lado 2")
                          for x in X_MM for y in Y_MM})
        field_t = np.array([r["bz_reference_mt"] / 1000 for r in self.rows])
        measured_v = np.array([r["observed_v"] for r in self.rows])
        self.assertAlmostEqual(self.scale, float(np.dot(field_t, measured_v) /
                                                 np.dot(field_t, field_t)), places=12)
        self.assertAlmostEqual(self.scale, -9.413388434008342, places=8)
        self.assertAlmostEqual(float(np.dot(field_t,
                                            [r["fitted_residual_v"] for r in self.rows])),
                               0.0, places=12)
        for row in self.rows:
            self.assertAlmostEqual(row["fixed_predicted_v"],
                                   PREVIOUS_SCALE_V_PER_T * row["bz_reference_mt"] / 1000)
            self.assertAlmostEqual(row["fitted_predicted_v"],
                                   self.scale * row["bz_reference_mt"] / 1000)

    def test_reported_metrics_and_remaining_spatial_structure(self):
        fixed = metrics(self.rows, "fixed_residual_v")
        fitted = metrics(self.rows, "fitted_residual_v")
        self.assertAlmostEqual(fixed.rmse_v, 0.08103291179943305, places=10)
        self.assertAlmostEqual(fitted.rmse_v, 0.04748429264230596, places=10)
        self.assertLess(fitted.mae_v, fixed.mae_v)
        by_key = {(r["side"], r["x_mm"], r["y_mm"]): r for r in self.rows}
        for side in ("Lado 1", "Lado 2"):
            self.assertAlmostEqual(by_key[(side, 5, -10)]["fitted_predicted_v"],
                                   by_key[(side, 5, 10)]["fitted_predicted_v"])
        self.assertNotAlmostEqual(by_key[("Lado 1", 5, -10)]["observed_v"],
                                  by_key[("Lado 1", 5, 10)]["observed_v"], places=5)


if __name__ == "__main__":
    unittest.main()
