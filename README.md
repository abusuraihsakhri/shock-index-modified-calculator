# Shock Index Modified Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Shock Index Calculator
======================

Calculates multiple shock index variants for trauma triage and
occult hypoperfusion assessment:

  - Shock Index (SI)        = HR / SBP
  - Modified Shock Index (MSI) = HR / MAP  (MAP = DBP + (SBP-DBP)/3)
  - Age-adjusted SI          = SI / (age / 100)
  - Reverse SI               = SBP / HR

Clinical significance:
    SI 0.5-0.7 : Normal
    SI > 0.9   : Suggests significant hemorrhage or sepsis
    SI > 1.0   : High mortality risk, consider massive transfusion protocol
    SI > 1.4   : Critical, >50% mortality

Pediatric adjustments:
    Children have higher baseline HR and lower SBP, so adult SI
    thresholds do not directly apply.  Age-specific reference ranges
    are provided.

Stdlib only — no external dependencies.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`shock_index()`**: Calculate Shock Index: SI = HR / SBP.

Parameters:
    hr:  heart rate in bpm
    sbp: systolic blood pressure in mmHg

Reference: Allgöwer M, Buri C. Schockindex. Dtsch Med Wschr 1967.

>>> shock_index(80, 120)
0.667
- **`modified_shock_index()`**: Calculate Modified Shock Index: MSI = HR / MAP.

MAP = DBP + (SBP - DBP) / 3

Parameters:
    hr:  heart rate in bpm
    sbp: systolic blood pressure in mmHg
    dbp: diastolic blood pressure in mmHg

Reference: Mutschler M, et al. Crit Care 2013;17:R120.
- **`age_adjusted_si()`**: Calculate age-adjusted Shock Index: Age-SI = SI / (age / 100).

Useful for elderly patients where normal SI ranges shift.

Parameters:
    si:  shock index value
    age: patient age in years

Reference: Zarzaur BL, et al. J Trauma 2010;68:1238-1243.
- **`reverse_shock_index()`**: Calculate Reverse Shock Index: RSI = SBP / HR.

Inverse of SI; higher values are better.  RSI < 1.0 is concerning.

Parameters:
    hr:  heart rate in bpm
    sbp: systolic blood pressure in mmHg
- **`map_from_bp()`**: Calculate Mean Arterial Pressure: MAP = DBP + (SBP - DBP) / 3.

---

## 📐 Mathematical Formulation & Logic

```text
  Calculates multiple shock index variants for trauma triage and
  """Calculate Shock Index: SI = HR / SBP.
  """Calculate Modified Shock Index: MSI = HR / MAP.
  """Calculate age-adjusted Shock Index: Age-SI = SI / (age / 100).
  """Calculate Reverse Shock Index: RSI = SBP / HR.
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --hr <value> --sbp <value> --dbp <value> --age <value>
```

### Parameter Reference
- `--hr`: Specifies input measurement or parameter value.
- `--sbp`: Specifies input measurement or parameter value.
- `--dbp`: Specifies input measurement or parameter value.
- `--age`: Specifies input measurement or parameter value.
- `--sex`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t shock-index-modified-calculator .
docker run -p 8000:8000 shock-index-modified-calculator
```
