"""Verifica reprodução das agregações e detecção de divergências na planilha."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hall_analysis import SOURCE, _workbook_sheets, calculate, load_readings, verify_comparison  # noqa: E402


class HallAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheets = _workbook_sheets(SOURCE)
        cls.readings = load_readings(cls.sheets)
        cls.references, cls.results = calculate(cls.readings)

    def test_complete_groups_and_comparison(self):
        self.assertEqual(len(self.readings), 904)
        self.assertEqual(len(self.results), 16)
        self.assertEqual(sum(r.count for r in self.results), 831)
        self.assertEqual(self.references["Lado 1"][1], 51)
        self.assertEqual(self.references["Lado 2"][1], 22)
        verify_comparison(self.sheets["Comparação"], self.references, self.results)

    def test_changed_comparison_is_detected(self):
        altered = copy.deepcopy(self.sheets["Comparação"])
        altered[8]["C"] = "0"
        with self.assertRaisesRegex(ValueError, "ΔV divergente"):
            verify_comparison(altered, self.references, self.results)


if __name__ == "__main__":
    unittest.main()
