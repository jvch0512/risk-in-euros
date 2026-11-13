from __future__ import annotations
import argparse, sys
from .model import ModelError, run
from .report import markdown, page


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="risk-in-euros", description="Cyber risk in euros: Monte Carlo, loss exceedance, control ROI. Offline.")
    p.add_argument("input", help="scenarios JSON")
    p.add_argument("--iterations", type=int, default=10000)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--html", action="store_true", help="HTML report on stdout")
    p.add_argument("--budget", type=float, help="exit 1 if the 1-in-10 year loss exceeds this amount")
    a = p.parse_args(argv)
    try:
        with open(a.input, encoding="utf-8") as f:
            rep = run(f.read(), a.iterations, a.seed)
    except (ModelError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    sys.stdout.write(page(rep) if a.html else markdown(rep))
    return 1 if a.budget is not None and rep.total_p90 > a.budget else 0


if __name__ == "__main__":
    sys.exit(main())
