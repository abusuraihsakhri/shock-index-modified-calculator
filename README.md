# Shock Index Calculator

Shock Index (SI) and variants for trauma triage and occult hypoperfusion assessment.

## Formulas Implemented

| Index | Formula | Clinical Use |
|-------|---------|-------------|
| **Shock Index (SI)** | HR / SBP | Primary hemorrhage screening |
| **Modified SI (MSI)** | HR / MAP | MAP-adjusted assessment |
| **Age-adjusted SI** | SI / (age/100) | Elderly patient adjustment |
| **Reverse SI** | SBP / HR | Inverse (higher = better) |

## Clinical Thresholds

| SI Value | Risk Level | Clinical Action |
|----------|-----------|----------------|
| 0.5-0.7 | Normal | Standard monitoring |
| 0.7-0.9 | Elevated | Assess for occult bleeding |
| > 0.9 | High | Aggressive resuscitation |
| > 1.0 | Very High | Massive transfusion protocol |
| > 1.4 | Critical | Immediate life-saving intervention |

## Pediatric Reference Ranges

| Age Group | Normal SI Range |
|-----------|----------------|
| < 1 year | 0.7-1.2 |
| 1-3 years | 0.7-1.1 |
| 3-6 years | 0.6-1.0 |
| 6-12 years | 0.5-0.9 |
| 12-18 years | 0.5-0.8 |

## Quick Start

```bash
# Single calculation
python cli.py single --hr 100 --sbp 100 --dbp 60 --age 45

# With all parameters
python cli.py single --hr 120 --sbp 80 --dbp 50 --age 70 --sex male

# Batch CSV processing
python cli.py batch -i sample.csv -o results.csv
```

## Python API

```python
from shock_index import shock_index, modified_shock_index, calculate_shock_index

# Basic shock index
si = shock_index(hr=100, sbp=100)  # 1.0

# Full assessment
result = calculate_shock_index(hr=100, sbp=100, dbp=60, age=45)
print(result['shock_index'])           # 1.0
print(result['modified_si'])           # 1.08
print(result['si_classification'])     # {'risk_level': 'very_high', ...}
```

## Dependencies

Python standard library only. No external packages required.

## License

MIT License.
