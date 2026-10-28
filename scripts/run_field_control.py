"""Run seeded reduced-order EFC/probe diagnostics (not Roman performance)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.field_control_diagnostics import (  # noqa: E402
    synthetic_efc_sensitivity, synthetic_probe_recovery,
)


def main() -> None:
    payload = {"schema": "field-control-diagnostics/1", "is_observation": False,
               "provenance": "seeded synthetic linearized complex-field model",
               "efc": synthetic_efc_sensitivity(), "probe": synthetic_probe_recovery()}
    output = ROOT / "results" / "field_control_diagnostics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(output), "probe": payload["probe"],
                      "efc_mismatch": payload["efc"]["jacobian_mismatch"]}, indent=2))


if __name__ == "__main__":
    main()
