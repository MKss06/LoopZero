"""Verifica a grade geométrica, a exclusão de 0 mm e a faixa ADC nominal."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compare_hall_mountings import template  # noqa: E402
from hall_analysis import SOURCE, _workbook_sheets, calculate, load_readings  # noqa: E402
from hall_geometry_sensitivity import (  # noqa: E402
    fit_scenario, representative_scenarios, run_grid, sensor_height_mm,
    validate_outside_magnet,
)


class GeometrySensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        readings = load_readings(_workbook_sheets(SOURCE))
        cls.results = calculate(readings)[1]
        cls.readings = readings

    def test_relative_height_and_symmetric_scenarios(self):
        self.assertAlmostEqual(sensor_height_mm(0), 2.24)
        plus = fit_scenario(self.results, 1.0, 1.0)
        minus = fit_scenario(self.results, -1.0, 1.0)
        self.assertAlmostEqual(plus.scale_v_per_t, minus.scale_v_per_t, places=10)
        self.assertAlmostEqual(plus.rmse_v, minus.rmse_v, places=10)
        self.assertAlmostEqual(plus.zero_output_v["Lado 1"], minus.zero_output_v["Lado 1"], places=10)

    def test_zero_is_excluded_and_only_common_scale_is_fitted(self):
        synthetic = [replace(r, delta_v_mv=5000 * template(r.side, r.distance_mm,
                                                            "vertical_z", sensor_height_mm(0.5), 1.0))
                     for r in self.results]
        baseline = fit_scenario(synthetic, 0.5, 1.0)
        changed_zero = [replace(r, delta_v_mv=r.delta_v_mv + 100000)
                        if r.distance_mm == 0 else r for r in synthetic]
        changed = fit_scenario(changed_zero, 0.5, 1.0)
        self.assertAlmostEqual(baseline.scale_v_per_t, 5.0, places=10)
        self.assertLess(baseline.rmse_v, 1e-12)
        self.assertEqual(baseline.scale_v_per_t, changed.scale_v_per_t)
        self.assertEqual(baseline.rmse_v, changed.rmse_v)
        self.assertEqual(baseline.zero_output_v, changed.zero_output_v)

    def test_geometry_guard_and_grid(self):
        with self.assertRaises(ValueError):
            validate_outside_magnet(0.0, -0.1)
        with self.assertRaises(ValueError):
            validate_outside_magnet(float("nan"), 0.0)
        validate_outside_magnet(0.0, 0.0)  # ponto na fronteira, fora do interior
        scenarios = run_grid(self.results, (-1.0, 0.0, 1.0), (0.0, 1.0))
        self.assertEqual(len(scenarios), 6)
        self.assertTrue(all(s.rmse_v >= 0 for s in scenarios))
        self.assertIn("melhor na grade", [name for name, _ in representative_scenarios(scenarios)])

    def test_voltage_check_is_explicitly_adc_nominal(self):
        # As tensões transcritas são consistentes com uma conversão ADC 0–5 V,
        # mas isso não comprova a faixa linear de saída do próprio AH49E.
        self.assertLess(max(abs(r.voltage_v - r.adc * 5 / 1023) for r in self.readings), 0.0005)
        best = fit_scenario(self.results, 0.0, 1.5)
        self.assertFalse(best.zero_within_adc_range)
        self.assertGreater(best.zero_output_v["Lado 1"], 5.0)
        self.assertLess(best.zero_output_v["Lado 2"], 0.0)


if __name__ == "__main__":
    unittest.main()
