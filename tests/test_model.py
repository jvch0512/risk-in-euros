import json, os, random, unittest
from risk_in_euros import model, report
from risk_in_euros.cli import main

SAMPLE = open(os.path.join(os.path.dirname(__file__), "..", "examples", "scenarios.json"), encoding="utf-8").read()


def one(freq, loss, mits=None):
    return json.dumps({"scenarios": [{"name": "s", "frequency": freq, "loss": loss, "mitigations": mits or []}]})


class T(unittest.TestCase):
    def test_deterministic_with_seed(self):
        a, b = model.run(SAMPLE, 2000, 5), model.run(SAMPLE, 2000, 5)
        self.assertEqual(a.total_mean, b.total_mean)
        self.assertNotEqual(a.total_mean, model.run(SAMPLE, 2000, 6).total_mean)

    def test_known_expectation(self):
        # fixed frequency 2/year, fixed loss 1000: expected annual loss is 2000
        r = model.run(one([2, 2, 2], [1000, 1000, 1000]), 20000, 3)
        self.assertAlmostEqual(r.total_mean, 2000, delta=60)

    def test_percentiles_are_ordered(self):
        r = model.run(SAMPLE, 5000, 1)
        self.assertLessEqual(r.total_p50, r.total_p90)
        self.assertLessEqual(r.total_p90, r.total_p95)

    def test_exceedance_curve_is_non_increasing(self):
        c = model.run(SAMPLE, 5000, 1).curve
        self.assertTrue(all(c[i][1] >= c[i + 1][1] for i in range(len(c) - 1)))
        self.assertAlmostEqual(c[0][1], 1 - model.run(SAMPLE, 5000, 1).scenarios[0].p_zero, delta=1.0)

    def test_mitigation_reduces_loss_and_roi_uses_paired_runs(self):
        r = model.run(one([1, 1, 1], [1000, 1000, 1000], [{"name": "c", "cost": 100, "lossReduction": 0.5}]), 10000, 1)
        m = r.scenarios[0].roi[0]
        self.assertAlmostEqual(m["annual_saving"], 500, delta=40)
        self.assertGreater(m["net"], 0)

    def test_pert_stays_in_bounds_and_peaks_near_mode(self):
        rng = random.Random(1)
        xs = [model.pert(rng, 10, 20, 100) for _ in range(5000)]
        self.assertTrue(all(10 <= x <= 100 for x in xs))
        self.assertLess(sorted(xs)[2500], 40)

    def test_invalid_input(self):
        for bad in ["x", "{}", one([3, 2, 1], [1, 2, 3]), one([1, 2], [1, 2, 3]), one([1, 1, 1], [1, 1, 1], [{"name": "c", "cost": 1, "lossReduction": 2}])]:
            with self.assertRaises(model.ModelError):
                model.parse(bad)
        with self.assertRaises(model.ModelError):
            model.run(SAMPLE, 10, 1)

    def test_markdown_and_html(self):
        r = model.run(SAMPLE, 3000, 1)
        self.assertIn("Expected annual loss", report.markdown(r))
        self.assertIn("<svg", report.page(r))

    def test_html_escapes_names(self):
        r = model.run(one([1, 1, 1], [1, 1, 1]).replace('"s"', '"<img src=x>"'), 1000, 1)
        self.assertNotIn("<img src=x>", report.page(r))

    def test_cli_budget_exit_code(self):
        path = os.path.join(os.path.dirname(__file__), "..", "examples", "scenarios.json")
        self.assertEqual(main([path, "--iterations", "2000", "--budget", "1"]), 1)
        self.assertEqual(main([path, "--iterations", "2000", "--budget", "1e12"]), 0)
        self.assertEqual(main(["missing.json"]), 2)


if __name__ == "__main__":
    unittest.main()
