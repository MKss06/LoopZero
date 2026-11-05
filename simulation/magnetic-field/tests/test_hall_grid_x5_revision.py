"""Confere a substituição X=5, o histórico e as escalas transportadas."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hall_grid_analysis import REVISED_SOURCE, SOURCE, load_grid  # noqa: E402
from hall_grid_x5_revision import (  # noqa: E402
    FIXED_SCALE_V_PER_T, compare_version, error_metrics,
)


class GridX5RevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = load_grid(SOURCE)[0]
        cls.revised = load_grid(REVISED_SOURCE)[0]

    def test_only_six_x5_positions_are_replaced(self):
        old = {(p.side, p.x_mm, p.y_mm): p for p in self.old}
        revised = {(p.side, p.x_mm, p.y_mm): p for p in self.revised}
        self.assertEqual(set(old), set(revised))
        changed = {key for key in old if old[key] != revised[key]}
        self.assertEqual(changed, {(side, 5, y) for side in ("Lado 1", "Lado 2")
                                   for y in (-10, 0, 10)})
        self.assertEqual(sum(p.count for p in self.revised), 1313)
        self.assertAlmostEqual(revised[("Lado 1", 5, 0)].reference_adc,
                               revised[("Lado 2", 5, 0)].reference_adc)
        self.assertAlmostEqual(revised[("Lado 1", 5, 0)].delta_v_mv, 778.3732767047559)

    def test_transport_fixed_scale_without_refitting(self):
        before = compare_version(self.old)
        after = compare_version(self.revised)
        before_by_key = {(r["side"], r["x_mm"], r["y_mm"]): r for r in before}
        for row in after:
            self.assertAlmostEqual(row["fixed_predicted_v"],
                                   FIXED_SCALE_V_PER_T * row["bz_reference_mt"] / 1000)
            key = (row["side"], row["x_mm"], row["y_mm"])
            self.assertAlmostEqual(row["fixed_predicted_v"],
                                   before_by_key[key]["fixed_predicted_v"])
            if row["x_mm"] != 5:
                self.assertEqual(row, before_by_key[key])
        self.assertLess(error_metrics(after, "fixed_residual_v")[1],
                        error_metrics(before, "fixed_residual_v")[1])
        self.assertGreater(error_metrics(after, "historical_residual_v")[1],
                           error_metrics(before, "historical_residual_v")[1])


if __name__ == "__main__":
    unittest.main()
