"""Verifica o cruzamento das fontes vigentes e a aritmética da comparação."""

import csv
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from compare_single_five_grid import (  # noqa: E402
    ADC_TO_V, RATIO_MARGIN, STEM, calculate, metrics, write_outputs,
)
from hall_grid_analysis import REVISED_SOURCE, SOURCE, load_grid  # noqa: E402


class CompareSingleFiveGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.meta = calculate()

    def test_vigente_usa_reteste_e_referencias_proprias(self):
        revised, _ = load_grid(REVISED_SOURCE)
        historical, _ = load_grid(SOURCE)
        revised_by_key = {(p.side, p.x_mm, p.y_mm): p for p in revised}
        old_by_key = {(p.side, p.x_mm, p.y_mm): p for p in historical}
        self.assertEqual(len(self.rows), 30)
        self.assertEqual(len({(r["lado"], r["x_nominal_mm"], r["y_nominal_mm"])
                              for r in self.rows}), 30)
        self.assertTrue(any(revised_by_key[key].mean_adc != old_by_key[key].mean_adc
                            for key in revised_by_key if key[1] == 5))
        for row in self.rows:
            key = (row["lado"], row["x_nominal_mm"], row["y_nominal_mm"])
            point = revised_by_key[key]
            self.assertAlmostEqual(row["tensao_medida_um_v"], point.mean_voltage_v)
            self.assertAlmostEqual(row["ref_um_aplicada_v"], point.reference_adc * ADC_TO_V)
            self.assertAlmostEqual(row["delta_um_medido_v"], point.delta_v_mv / 1000)
            if row["x_nominal_mm"] == 5:
                self.assertAlmostEqual(point.reference_adc, 534.3448275862)
            else:
                self.assertEqual(point, old_by_key[key])

    def test_drift_model_difference_and_residual_identities(self):
        self.assertAlmostEqual(self.meta["deriva_cinco_v"], -0.01301525585679355)
        for row in self.rows:
            self.assertAlmostEqual(row["delta_cinco_ref_fim_v"] -
                                   row["delta_cinco_ref_inicio_v"],
                                   -self.meta["deriva_cinco_v"])
            self.assertAlmostEqual(row["delta_um_medido_v"],
                                   row["tensao_medida_um_v"] - row["ref_um_aplicada_v"])
            self.assertAlmostEqual(row["delta_cinco_ref_inicio_v"],
                                   row["tensao_medida_cinco_v"] - row["ref_cinco_inicio_v"])
            self.assertAlmostEqual(row["delta_cinco_ref_fim_v"],
                                   row["tensao_medida_cinco_v"] - row["ref_cinco_fim_v"])
            self.assertAlmostEqual(row["residuo_diferenca_intermediaria_v"],
                                   row["residuo_cinco_intermediario_v"] - row["residuo_um_v"])
            self.assertAlmostEqual(row["diferenca_modelo_cinco_menos_um_v"],
                                   row["delta_cinco_modelo_escala_fixa_v"] -
                                   row["delta_um_modelo_escala_fixa_v"])

    def test_ratio_excludes_small_denominators(self):
        self.assertEqual(sum(r["razao_estado"] == "calculavel" for r in self.rows), 18)
        for row in self.rows:
            limit = RATIO_MARGIN * max(row["deriva_ref_um_modulo_v"],
                                       abs(row["deriva_ref_cinco_fim_menos_inicio_v"]))
            self.assertAlmostEqual(row["limiar_razao_v"], limit)
            if row["razao_estado"] == "calculavel":
                self.assertGreater(abs(row["delta_um_medido_v"]), limit)
                self.assertAlmostEqual(row["razao_cinco_sobre_um"],
                                       row["delta_cinco_intermediario_ilustrativo_v"] /
                                       row["delta_um_medido_v"])
            else:
                self.assertLessEqual(abs(row["delta_um_medido_v"]), limit)
                self.assertEqual(row["razao_cinco_sobre_um"], "")

    def test_export_and_metrics(self):
        mae, rmse = metrics(self.rows, "residuo_um_v")
        self.assertTrue(math.isfinite(mae) and math.isfinite(rmse))
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            write_outputs(self.rows, self.meta, target)
            with (target / f"{STEM}.csv").open(encoding="utf-8", newline="") as stream:
                exported = list(csv.DictReader(stream))
            self.assertEqual(len(exported), 30)
            self.assertEqual(sum(r["razao_estado"] == "calculavel" for r in exported), 18)
            for suffix in (".md", "-medido.png", "-modelo.png", "-residuos.png"):
                self.assertTrue((target / f"{STEM}{suffix}").is_file())


if __name__ == "__main__":
    unittest.main()
