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
=======================

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

Core library is stdlib only — no external dependencies required.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`shock_index(hr, sbp)`**: Calculate Shock Index: SI = HR / SBP.

Parameters:
    hr:  heart rate in bpm
    sbp: systolic blood pressure in mmHg

Reference: Allgöwer M, Buri C. Schockindex. Dtsch Med Wschr 1967.

>>> shock_index(80, 120)
0.667

- **`modified_shock_index(hr, sbp, dbp)`**: Calculate Modified Shock Index: MSI = HR / MAP.

MAP = DBP + (SBP - DBP) / 3

Parameters:
    hr:  heart rate in bpm
    sbp: systolic blood pressure in mmHg
    dbp: diastolic blood pressure in mmHg

Reference: Mutschler M, et al. Crit Care 2013;17:R120.

- **`age_adjusted_si(si, age)`**: Calculate age-adjusted Shock Index: Age-SI = SI / (age / 100).

Useful for elderly patients where normal SI ranges shift.

Parameters:
    si:  shock index value
    age: patient age in years

Reference: Zarzaur BL, et al. J Trauma 2010;68:1238-1243.

- **`reverse_shock_index(hr, sbp)`**: Calculate Reverse Shock Index: RSI = SBP / HR.

Inverse of SI; higher values are better.  RSI < 1.0 is concerning.

Parameters:
    hr:  heart rate in bpm
    sbp: systolic blood pressure in mmHg

- **`map_from_bp(sbp, dbp)`**: Calculate Mean Arterial Pressure: MAP = DBP + (SBP - DBP) / 3.

---

## 💻 CLI Quickstart & Usage

### 1. Single Patient Calculation
```bash
python cli.py single --hr 80 --sbp 120
python cli.py single --hr 80 --sbp 120 --dbp 80 --age 50 --sex male
```

### 2. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 3. Audit Commands
```bash
python cli.py audit --task-id TASK-001
python cli.py chat "Explain shock index"
python cli.py verify-audit
```

### Parameter Reference
- `--hr`: Heart rate in bpm (required for single calculation)
- `--sbp`: Systolic blood pressure in mmHg (required for single calculation)
- `--dbp`: Diastolic blood pressure in mmHg (optional)
- `--age`: Patient age in years (optional)
- `--sex`: Patient sex (optional)
- `-i/--input`: Input CSV file path (for batch mode)
- `-o/--output`: Output CSV file path (for batch mode, default: results.csv)

### Input CSV Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `hr` (or `heart_rate`) | Heart rate in bpm | Required |
| `sbp` | Systolic blood pressure in mmHg | Required |
| `dbp` | Diastolic blood pressure in mmHg | Optional |
| `age` | Patient age in years | Optional |
| `sex` | Patient sex | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Notes
- The audit trail uses HMAC-SHA256 with a secret key. Set the `AUDIT_SECRET_KEY` environment variable in production to ensure audit trail persistence across restarts.
- Without `AUDIT_SECRET_KEY` set, a random key is generated at startup (suitable for development/testing only).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Run specific test files:

```bash
pytest test_shock_index.py -v
pytest tests/ -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t shock-index-modified-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key shock-index-modified-calculator
```

Or using Docker Compose:

```bash
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## 📁 Project Structure

```
shock-index-modified-calculator/
├── shock_index.py          # Core calculation library (stdlib only)
├── cli.py                  # Command-line interface
├── simulator.py            # High-throughput simulation
├── enrichment.py           # Enrichment scoring engines
├── agents/                 # Enterprise agent framework
│   ├── base.py            # Security, PHI guard, audit trail
│   ├── models.py          # Pydantic data models
│   ├── supervisor.py      # Supervisor orchestrator
│   ├── workers.py         # Specialized worker agents
│   ├── api.py             # FastAPI REST server
│   ├── llm_factory.py     # LLM provider factory
│   ├── learning.py        # Bayesian calibration engine
│   ├── metrics.py         # Prometheus metrics
│   └── streamer.py        # WebSocket telemetry
├── web/                   # Operations console (HTML)
├── tests/                 # Test suite
├── test_shock_index.py    # Core library tests
├── sample.csv             # Sample input data
├── Dockerfile             # Container build
├── docker-compose.yml     # Container orchestration
└── openapi_spec.json      # OpenAPI specification
```
