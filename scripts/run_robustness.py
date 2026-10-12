"""Generate deterministic coronagraph robustness evidence and an SVG summary."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coronagraph_robustness import (  # noqa: E402
    jitter_sensitivity,
    quadrature_convergence,
    recovery_dict,
)


def _svg(rows: list[dict[str, float]]) -> str:
    width, height = 720, 420
    x0, y0, plot_w, plot_h = 75, 35, 600, 320
    grouped: dict[float, list[dict[str, float]]] = {}
    for row in rows:
        grouped.setdefault(row["coupling"], []).append(row)
    all_y = [r["contrast"] for r in rows]
    lo, hi = min(all_y), max(all_y)
    import math
    ylo, yhi = math.log10(lo), math.log10(hi)
    colours = ["#0f766e", "#7c3aed", "#c2410c"]
    lines = []
    for colour, (coupling, values) in zip(colours, sorted(grouped.items()), strict=True):
        points = []
        max_x = max(v["jitter_mas_rms"] for v in values)
        for value in values:
            x = x0 + plot_w * value["jitter_mas_rms"] / max_x
            y = y0 + plot_h * (yhi - math.log10(value["contrast"])) / (yhi - ylo)
            points.append(f"{x:.1f},{y:.1f}")
        lines.append(f'<polyline fill="none" stroke="{colour}" stroke-width="3" points="{" ".join(points)}"/>')
        lines.append(f'<text x="{x0 + 12}" y="{y0 + 22 + 20 * len(lines)//2}" fill="{colour}" font-size="13">k={coupling:.0e}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Synthetic pointing-jitter leakage sensitivity</title><desc id="desc">Model contrast increases quadratically with RMS jitter for three illustrative coupling coefficients.</desc>
<rect width="100%" height="100%" fill="#fafafa"/><line x1="{x0}" y1="{y0+plot_h}" x2="{x0+plot_w}" y2="{y0+plot_h}" stroke="#111827"/><line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0+plot_h}" stroke="#111827"/>
{''.join(lines)}
<text x="360" y="405" text-anchor="middle" font-family="sans-serif" font-size="14">RMS pointing jitter (mas)</text><text transform="translate(18 220) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="14">Model intensity contrast (log scale)</text>
<text x="{x0}" y="20" font-family="sans-serif" font-size="12">Synthetic model prediction; not measured Roman CGI performance</text></svg>'''


def main() -> None:
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    convergence = quadrature_convergence()
    jitter = jitter_sensitivity()
    recovery = recovery_dict()
    payload = {
        "schema": "coronagraph-robustness/1",
        "provenance": "deterministic reduced-order model and synthetic Poisson/Gaussian recovery",
        "is_observation": False,
        "analyses": {
            "broadband_quadrature_convergence": convergence,
            "pointing_jitter_sensitivity": jitter,
            "synthetic_count_recovery": recovery,
        },
    }
    (output / "coronagraph_robustness.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with (output / "jitter_sensitivity.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(jitter[0]))
        writer.writeheader()
        writer.writerows(jitter)
    (output / "jitter_sensitivity.svg").write_text(_svg(jitter), encoding="utf-8")
    print(json.dumps({"output": str(output), "recovery": recovery, "finest_grid": convergence[-1]}, indent=2))


if __name__ == "__main__":
    main()
