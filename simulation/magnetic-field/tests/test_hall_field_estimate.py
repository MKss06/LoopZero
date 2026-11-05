"""Verifica a conversão condicional e a comparação com o modelo horizontal."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hall_analysis import (  # noqa: E402
    SOURCE, _workbook_sheets, calculate, estimated_field_mt, load_readings,
)
from hall_field_estimate import comparison_rows  # noqa: E402


class HallFieldEstimateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = calculate(load_readings(_workbook_sheets(SOURCE)))[1]

    def test_side_references_and_nominal_zero_are_included(self):
        rows, _ = comparison_rows(self.results)
        self.assertEqual(len(rows), 16)
        self.assertEqual(sum(row["used_for_fit"] for row in rows), 14)
        for result, row in zip(self.results, rows):
            self.assertEqual((row["side"], row["distance_mm"]),
                             (result.side, result.distance_mm))
            self.assertAlmostEqual(row["reference_v"], result.reference_voltage_v)
            self.assertAlmostEqual(row["delta_v_v"],
                                   result.mean_voltage_v - result.reference_voltage_v)
            self.assertAlmostEqual(row["estimated_mt"], result.delta_v_mv / 14)
            self.assertAlmostEqual(row["residual_mt"],
                                   row["estimated_mt"] - row["model_scaled_mt"])
        self.assertAlmostEqual(estimated_field_mt(14), 1)
        self.assertAlmostEqual(estimated_field_mt(-14), -1)

    def test_zero_does_not_change_fitted_model(self):
        initial, amplitude = comparison_rows(self.results)
        changed = [replace(result, delta_v_mv=result.delta_v_mv + 1400)
                   if result.distance_mm == 0 else result for result in self.results]
        revised, revised_amplitude = comparison_rows(changed)
        self.assertAlmostEqual(amplitude, revised_amplitude)
        for before, after in zip(initial, revised):
            self.assertAlmostEqual(before["model_scaled_mt"], after["model_scaled_mt"])
            if before["distance_mm"] == 0:
                self.assertAlmostEqual(after["estimated_mt"] - before["estimated_mt"], 100)
            else:
                self.assertAlmostEqual(before["estimated_mt"], after["estimated_mt"])


if __name__ == "__main__":
    unittest.main()
