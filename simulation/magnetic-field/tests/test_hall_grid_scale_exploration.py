"""Verifica o ajuste de uma escala comum e os resíduos espaciais."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hall_grid_analysis import PREVIOUS_SCALE_V_PER_T, load_grid  # noqa: E402
from hall_grid_scale_exploration import compare_scales, metrics  # noqa: E402


class GridScaleExplorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points = load_grid()[0]
        cls.rows, cls.fitted_scale = compare_scales(cls.points)

    def test_one_common_scale_minimizes_sse_without_intercept(self):
        self.assertEqual(len(self.rows), 30)
        field = np.array([row["bz_reference_mt"] / 1000 for row in self.rows])
        observed = np.array([row["observed_v"] for row in self.rows])
        expected = float(np.dot(field, observed) / np.dot(field, field))
        self.assertAlmostEqual(self.fitted_scale, expected, places=12)
        self.assertAlmostEqual(float(np.dot(field,
                                            [row["fitted_residual_v"] for row in self.rows])),
                               0.0, places=12)
        self.assertLess(metrics(self.rows, "fitted_residual_v").rmse_v,
                        metrics(self.rows, "fixed_residual_v").rmse_v)
        for row in self.rows:
            self.assertAlmostEqual(row["fixed_predicted_v"],
                                   PREVIOUS_SCALE_V_PER_T * row["bz_reference_mt"] / 1000)
            self.assertAlmostEqual(row["fitted_predicted_v"],
                                   self.fitted_scale * row["bz_reference_mt"] / 1000)

    def test_lateral_asymmetry_survives_scale_change(self):
        by_key = {(row["side"], row["x_mm"], row["y_mm"]): row for row in self.rows}
        negative = by_key[("Lado 1", 5, -10)]
        positive = by_key[("Lado 1", 5, 10)]
        self.assertAlmostEqual(positive["fixed_predicted_v"], negative["fixed_predicted_v"])
        self.assertAlmostEqual(positive["fitted_predicted_v"], negative["fitted_predicted_v"])
        self.assertGreater(positive["observed_v"] - negative["observed_v"], 0.1)

    def test_exploratory_fit_does_not_replace_previous_scale(self):
        modified = [replace(point, delta_v_mv=point.delta_v_mv + 140)
                    if (point.side, point.x_mm, point.y_mm) == ("Lado 1", 5, 0)
                    else point for point in self.points]
        rows, fitted_scale = compare_scales(modified)
        self.assertNotEqual(fitted_scale, self.fitted_scale)
        original = next(row for row in self.rows if (row["side"], row["x_mm"], row["y_mm"])
                        == ("Lado 1", 5, 0))
        changed = next(row for row in rows if (row["side"], row["x_mm"], row["y_mm"])
                       == ("Lado 1", 5, 0))
        self.assertAlmostEqual(changed["fixed_predicted_v"], original["fixed_predicted_v"])


if __name__ == "__main__":
    unittest.main()
