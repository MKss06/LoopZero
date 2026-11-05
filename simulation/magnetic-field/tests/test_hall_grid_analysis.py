"""Checa a aritmética da grade e a reutilização do cenário horizontal."""

import copy
import csv
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hall_analysis import _workbook_sheets  # noqa: E402
from hall_grid_analysis import (  # noqa: E402
    PREVIOUS_SCALE_V_PER_T, SOURCE, comparison_rows, load_grid,
    model_reference_field_t,
)


class HallGridAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.points, cls.references = load_grid()

    def test_all_30_positions_and_cached_arithmetic(self):
        self.assertEqual(len(self.points), 30)
        self.assertEqual(sum(point.count for point in self.points), 1342)
        self.assertEqual(sum(start + end for start, end, _ in self.references.values()), 126)
        self.assertEqual(len({(point.side, point.x_mm, point.y_mm)
                              for point in self.points}), 30)

    def test_changed_cached_field_is_detected(self):
        altered = copy.deepcopy(_workbook_sheets(SOURCE))
        altered["Médias por posição"][2]["K"] = "0"
        with patch("hall_grid_analysis._workbook_sheets", return_value=altered):
            with self.assertRaisesRegex(ValueError, "campo linha 2"):
                load_grid()

    def test_central_model_uses_previous_scale_and_rigid_flip(self):
        rows = comparison_rows(self.points)
        self.assertEqual(len(rows), 30)
        field_one = model_reference_field_t("Lado 1", 5, 0)
        field_two = model_reference_field_t("Lado 2", 5, 0)
        self.assertAlmostEqual(field_one, -field_two, places=12)
        self.assertAlmostEqual(model_reference_field_t("Lado 1", 5, -10),
                               model_reference_field_t("Lado 1", 5, 10), places=12)
        central = next(row for row in rows if (row["side"], row["x_mm"], row["y_mm"])
                       == ("Lado 1", 5, 0))
        self.assertAlmostEqual(central["delta_v_model_v"],
                               PREVIOUS_SCALE_V_PER_T * field_one, places=12)
        with (SOURCE.parents[2] / "processed" / "hall-sensor" /
              "comparacao-horizontal.csv").open(newline="", encoding="utf-8") as stream:
            prior = next(row for row in csv.DictReader(stream)
                         if row["lado"] == "Lado 1" and row["distancia_nominal_mm"] == "5")
        self.assertAlmostEqual(central["delta_v_model_v"],
                               float(prior["vertical_z_previsto_v"]), delta=1e-7)


if __name__ == "__main__":
    unittest.main()
