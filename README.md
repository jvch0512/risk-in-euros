# risk-in-euros

Boards do not act on "high risk". They act on euros. risk-in-euros turns a handful of scenario estimates into expected annual loss, a "1 in 10 year" loss, a loss exceedance curve and the return on each control, using a FAIR-style Monte Carlo simulation.

**Live demo:** https://jvch0512.github.io/risk-in-euros/ (a report on a synthetic company)

Python 3.10+, standard library only, deterministic with a seed.

## Use

```bash
python -m risk_in_euros examples/scenarios.json                 # markdown report
python -m risk_in_euros examples/scenarios.json --html > r.html # shareable page with the curve
python -m risk_in_euros scenarios.json --iterations 50000 --seed 7
python -m risk_in_euros scenarios.json --budget 1500000         # exit 1 if the 1-in-10 year loss exceeds the budget
```

Each scenario gives a frequency (events per year) and a loss per event, both as `[min, most likely, max]`, plus optional controls with a cost and the fraction of frequency or loss they remove. See [examples/scenarios.json](examples/scenarios.json) and [docs/sample-report.md](docs/sample-report.md).

## How it works

- Each iteration samples a yearly event rate and a loss per event from modified PERT distributions (bounded, peaked at your most likely value), draws the number of events from a Poisson distribution and adds up the losses.
- Totals are sorted to read percentiles and the exceedance curve: the probability that a year costs more than X.
- Control ROI re-runs the same scenario with the same random seed and the control's reductions. Sharing the seed makes the comparison paired, so the saving is not noise.

## Limits

- Garbage in, garbage out. The model does not make estimates better, it makes them explicit, comparable and challengeable. Calibrate ranges with incident history, insurer data and industry reports.
- Scenarios are independent: no correlation between events, no tail dependence. Treat the total as indicative.
- It is not the complete FAIR taxonomy: frequency and loss magnitude are estimated directly, not decomposed into threat event frequency, vulnerability and loss types.

## Where it fits

Board and audit committee reporting, budget justification for security, insurance and risk-transfer decisions, vCISO engagements. A paid deliverable: a workshop to calibrate scenarios, then a quarterly refresh.

## Tests

```bash
python -m unittest discover -s tests   # 10 tests: determinism, a closed-form expectation, percentile order, curve monotonicity, paired ROI, validation
```

MIT.
