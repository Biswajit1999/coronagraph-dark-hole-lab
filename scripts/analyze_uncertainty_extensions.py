"""Generate seeded synthetic diagnostic tables; no observational data are loaded."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.uncertainty_extensions import example_summary  # noqa: E402


def main() -> None:
    result = example_summary()
    dest = ROOT / 'results' / 'uncertainty_extensions'
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'summary.json').write_text(json.dumps({
        'provenance': 'seeded synthetic reduced-order calculations; NOT Roman CGI measurements',
        'quadrature': result['quadrature'], 'jitter': result['jitter'],
        'allocation': {k: v for k, v in result['allocation'].items() if k != 'rows'},
    }, indent=2) + '\n')
    for name, rows in (('quadrature.csv', result['quadrature']),
                       ('exposure_allocation.csv', result['allocation']['rows'])):
        with (dest / name).open('w', newline='') as fh:
            writer=csv.DictWriter(fh,fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    print(json.dumps({'jitter':result['jitter'],
                      'allocation':{k:v for k,v in result['allocation'].items() if k!='rows'},
                      'last_quadrature':result['quadrature'][-1]},indent=2))

if __name__=='__main__': main()
