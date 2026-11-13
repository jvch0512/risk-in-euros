from __future__ import annotations
import html
from .model import Report


def eur(x: float) -> str:
    return f"€{x:,.0f}".replace(",", ".")


def markdown(r: Report) -> str:
    L = [f"# Cyber risk in euros: {r.organisation}", "",
         f"Monte Carlo, {r.iterations} iterations, seed {r.seed}. Inputs are estimates; the output is only as good as they are.", "",
         f"- Expected annual loss: **{eur(r.total_mean)}**",
         f"- Typical year (median): {eur(r.total_p50)}",
         f"- Bad year (1 in 10): {eur(r.total_p90)}",
         f"- Very bad year (1 in 20): {eur(r.total_p95)}", "",
         "| Scenario | Expected annual loss | 1 in 10 year | Years with no loss |", "|---|---|---|---|"]
    for s in r.scenarios:
        L.append(f"| {s.name} | {eur(s.mean)} | {eur(s.p90)} | {s.p_zero:.0%} |")
    rows = [(s.name, m) for s in r.scenarios for m in s.roi]
    if rows:
        L += ["", "## Control ROI (paired simulation)", "", "| Control | Scenario | Cost | Annual saving | Net | ROI |", "|---|---|---|---|---|---|"]
        for sn, m in sorted(rows, key=lambda x: -x[1]["net"]):
            roi = "n/a" if m["roi"] == float("inf") else f"{m['roi']:.1f}x"
            L.append(f"| {m['name']} | {sn} | {eur(m['cost'])} | {eur(m['annual_saving'])} | {eur(m['net'])} | {roi} |")
    return "\n".join(L) + "\n"


def page(r: Report) -> str:
    w, h, pad = 640, 260, 40
    mx = r.curve[-1][0] or 1
    pts = " ".join(f"{pad + (x / mx) * (w - 2 * pad):.1f},{h - pad - p * (h - 2 * pad):.1f}" for x, p in r.curve)
    rows = "".join(f"<tr><td>{html.escape(s.name)}</td><td>{eur(s.mean)}</td><td>{eur(s.p90)}</td></tr>" for s in r.scenarios)
    roi = "".join(f"<tr><td>{html.escape(m['name'])}</td><td>{html.escape(s.name)}</td><td>{eur(m['cost'])}</td><td>{eur(m['annual_saving'])}</td><td class=\"{'ok' if m['net'] > 0 else 'bad'}\">{eur(m['net'])}</td></tr>" for s in r.scenarios for m in s.roi)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>risk-in-euros</title><style>:root{{color-scheme:dark}}body{{margin:0;padding:28px;background:#0e1319;color:#e8eef5;font:14px/1.5 system-ui,sans-serif;max-width:900px}}h1{{margin:0 0 4px}}.sub{{color:#8b98a8}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid #2a3441}}th{{color:#8b98a8}}.big{{font-size:30px;font-weight:700;color:#4cc2ff}}td.ok{{color:#3fb950;font-weight:700}}td.bad{{color:#f85149;font-weight:700}}svg{{background:#161d26;border-radius:8px;width:100%;height:auto}}</style></head><body><h1>risk-in-euros</h1><p class="sub">FAIR-style Monte Carlo for the board, in euros. Python, standard library only. Synthetic example for {html.escape(r.organisation)}, {r.iterations} iterations.</p><p>Expected annual loss<br><span class="big">{eur(r.total_mean)}</span></p><p>Typical year {eur(r.total_p50)} &middot; 1 in 10 year {eur(r.total_p90)} &middot; 1 in 20 year {eur(r.total_p95)}</p><h2>Loss exceedance curve</h2><svg viewBox="0 0 {w} {h}" role="img" aria-label="Probability that annual loss exceeds a value"><polyline fill="none" stroke="#4cc2ff" stroke-width="2" points="{pts}"/><line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#2a3441"/><line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" stroke="#2a3441"/><text x="{pad}" y="{h-12}" fill="#8b98a8" font-size="11">€0</text><text x="{w-pad-60}" y="{h-12}" fill="#8b98a8" font-size="11">{eur(mx)}</text><text x="4" y="{pad+4}" fill="#8b98a8" font-size="11">100%</text><text x="4" y="{h-pad}" fill="#8b98a8" font-size="11">0%</text></svg><p class="sub">Vertical axis: probability that the annual loss is higher than the amount on the horizontal axis.</p><h2>Scenarios</h2><table><tr><th>Scenario</th><th>Expected annual loss</th><th>1 in 10 year</th></tr>{rows}</table><h2>Controls: is it worth the money?</h2><table><tr><th>Control</th><th>Scenario</th><th>Cost</th><th>Annual saving</th><th>Net</th></tr>{roi}</table></body></html>
"""
