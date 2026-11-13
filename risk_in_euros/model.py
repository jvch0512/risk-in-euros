"""FAIR-style Monte Carlo risk quantification. Standard library only, deterministic with a seed."""
from __future__ import annotations
import json, math, random
from dataclasses import dataclass, field


class ModelError(ValueError):
    pass


@dataclass
class Mitigation:
    name: str
    cost: float
    freq_reduction: float = 0.0   # fraction of event frequency removed, 0..1
    loss_reduction: float = 0.0   # fraction of loss per event removed, 0..1


@dataclass
class Scenario:
    name: str
    freq: tuple[float, float, float]   # events per year: min, most likely, max
    loss: tuple[float, float, float]   # EUR per event: min, most likely, max
    mitigations: list[Mitigation] = field(default_factory=list)


def _triple(v, where):
    if not isinstance(v, (list, tuple)) or len(v) != 3 or not all(isinstance(x, (int, float)) for x in v):
        raise ModelError(f"{where} must be [min, most likely, max]")
    lo, ml, hi = map(float, v)
    if lo < 0 or not lo <= ml <= hi or hi == 0:
        raise ModelError(f"{where} needs 0 <= min <= most likely <= max and max > 0")
    return lo, ml, hi


def parse(text: str) -> tuple[str, list[Scenario]]:
    try:
        d = json.loads(text)
    except json.JSONDecodeError as e:
        raise ModelError(f"not valid JSON: {e.msg}") from None
    if not isinstance(d, dict) or not isinstance(d.get("scenarios"), list) or not d["scenarios"]:
        raise ModelError("scenarios must be a non-empty list")
    out = []
    for i, s in enumerate(d["scenarios"]):
        w = f"scenarios[{i}]"
        if not isinstance(s, dict):
            raise ModelError(f"{w} must be an object")
        ms = []
        for j, m in enumerate(s.get("mitigations", [])):
            fr, lr = m.get("freqReduction", 0), m.get("lossReduction", 0)
            if not (0 <= fr <= 1 and 0 <= lr <= 1) or m.get("cost", -1) < 0:
                raise ModelError(f"{w}.mitigations[{j}] needs cost >= 0 and reductions between 0 and 1")
            ms.append(Mitigation(str(m.get("name", f"control {j+1}")), float(m["cost"]), float(fr), float(lr)))
        out.append(Scenario(str(s.get("name", f"scenario {i+1}")), _triple(s.get("frequency"), w + ".frequency"), _triple(s.get("loss"), w + ".loss"), ms))
    return str(d.get("organisation", "(unnamed)")), out


def pert(rng: random.Random, lo: float, ml: float, hi: float) -> float:
    """Modified PERT (lambda 4): smooth, bounded, peaks at the most likely value."""
    if hi == lo:
        return lo
    a = 1 + 4 * (ml - lo) / (hi - lo)
    b = 1 + 4 * (hi - ml) / (hi - lo)
    return lo + rng.betavariate(a, b) * (hi - lo)


def poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 30:  # normal approximation keeps it fast for very frequent events
        return max(0, round(rng.gauss(lam, math.sqrt(lam))))
    l, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= l:
            return k
        k += 1


def simulate(sc: Scenario, n: int, seed: int, fr: float = 0.0, lr: float = 0.0) -> list[float]:
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        lam = pert(rng, *sc.freq) * (1 - fr)
        total = 0.0
        for _ in range(poisson(rng, lam)):
            total += pert(rng, *sc.loss) * (1 - lr)
        out.append(total)
    return out


def pct(sorted_v: list[float], p: float) -> float:
    return sorted_v[min(len(sorted_v) - 1, int(p * len(sorted_v)))]


@dataclass
class Result:
    name: str
    mean: float
    p50: float
    p90: float
    p95: float
    p_zero: float
    roi: list[dict]


@dataclass
class Report:
    organisation: str
    iterations: int
    seed: int
    total_mean: float
    total_p50: float
    total_p90: float
    total_p95: float
    scenarios: list[Result]
    curve: list[tuple[float, float]]  # (loss, probability of exceeding it)


def run(text: str, n: int = 10000, seed: int = 1) -> Report:
    if n < 1000:
        raise ModelError("iterations must be at least 1000")
    org, scs = parse(text)
    sims = [simulate(s, n, seed + i) for i, s in enumerate(scs)]
    totals = sorted(sum(col) for col in zip(*sims))
    results = []
    for i, (s, v) in enumerate(zip(scs, sims)):
        sv = sorted(v)
        mean = sum(v) / n
        roi = []
        for m in s.mitigations:
            after = simulate(s, n, seed + i, m.freq_reduction, m.loss_reduction)  # same seed: paired comparison
            saving = mean - sum(after) / n
            roi.append({"name": m.name, "cost": m.cost, "annual_saving": saving, "net": saving - m.cost, "roi": (saving - m.cost) / m.cost if m.cost else math.inf})
        results.append(Result(s.name, mean, pct(sv, .5), pct(sv, .9), pct(sv, .95), sum(1 for x in v if x == 0) / n, roi))
    results.sort(key=lambda r: -r.mean)
    top = totals[-1] or 1.0
    curve = [(top * k / 40, sum(1 for x in totals if x > top * k / 40) / n) for k in range(41)]
    return Report(org, n, seed, sum(totals) / n, pct(totals, .5), pct(totals, .9), pct(totals, .95), results, curve)
