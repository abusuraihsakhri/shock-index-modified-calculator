#!/usr/bin/env python3
"""
Shock Index Calculator
======================

Calculates multiple shock index variants for trauma triage and
occult hypoperfusion assessment:

  - Shock Index (SI)        = HR / SBP
  - Modified Shock Index (MSI) = HR / MAP  (MAP = DBP + (SBP-DBP)/3)
  - Age Shock Index (Age-SI) = age (years) × SI
  - Reverse SI               = SBP / HR

Interpretation:
    SI and MSI are adjunctive hemodynamic measures, not diagnostic tests.
    Thresholds differ across populations and must not prescribe treatment.

Pediatric adjustments:
    Children have higher baseline HR and lower SBP, so adult SI
    thresholds do not directly apply.  Age-specific reference ranges
    are provided.

Stdlib only — no external dependencies.
"""

import argparse
import csv
import json
import math
import sys


# ── Clinical thresholds ──────────────────────────────────────────────

SI_NORMAL_LOW = 0.5
SI_NORMAL_HIGH = 0.7
SI_HEMORRHAGE = 0.9
SI_HIGH_MORTALITY = 1.0
SI_CRITICAL = 1.4


# ── Core calculations ────────────────────────────────────────────────

def _validate_number(value, label, *, positive=False):
    """Reject booleans, non-numeric, non-finite, and invalid measurements."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    try:
        if not math.isfinite(value):
            raise ValueError(f"{label} must be finite")
    except (TypeError, OverflowError, ValueError):
        raise ValueError(f"{label} must be finite") from None
    if positive and value <= 0:
        raise ValueError(f"{label} must be positive, got {value}")
    return value


def _finite_result(value, label):
    if not math.isfinite(value):
        raise ValueError(f"{label} is outside the finite numeric range")
    return value


def shock_index(hr, sbp):
    """Calculate Shock Index: SI = HR / SBP.

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg

    Reference: Allgöwer M, Buri C. Schockindex. Dtsch Med Wschr 1967.

    >>> round(shock_index(80, 120), 3)
    0.667
    """
    _validate_number(hr, "Heart rate", positive=True)
    _validate_number(sbp, "SBP", positive=True)
    return _finite_result(hr / sbp, "Shock index")


def modified_shock_index(hr, sbp, dbp):
    """Calculate Modified Shock Index: MSI = HR / MAP.

    MAP = DBP + (SBP - DBP) / 3

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg
        dbp: diastolic blood pressure in mmHg

    Reference: Mutschler M, et al. Crit Care 2013;17:R120.
    """
    _validate_number(hr, "Heart rate", positive=True)
    map_val = map_from_bp(sbp, dbp)
    return _finite_result(hr / map_val, "Modified shock index")


def age_adjusted_si(si, age):
    """Calculate Age Shock Index: Age-SI = age (years) * SI.

    This is the published age x SI definition; do not apply the
    earlier inverse-age formula. Use only as a contextual measure.

    Parameters:
        si:  shock index value
        age: patient age in years

    Reference: Zarzaur BL, et al. J Surg Res 2008;147:229-236.
    """
    _validate_number(si, "Shock index", positive=True)
    _validate_number(age, "Age", positive=True)
    return _finite_result(si * age, "Age shock index")


def reverse_shock_index(hr, sbp):
    """Calculate Reverse Shock Index: RSI = SBP / HR.

    Inverse of SI; higher values are better.  RSI < 1.0 is concerning.

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg
    """
    _validate_number(hr, "Heart rate", positive=True)
    _validate_number(sbp, "SBP", positive=True)
    return _finite_result(sbp / hr, "Reverse shock index")


def map_from_bp(sbp, dbp):
    """Calculate Mean Arterial Pressure: MAP = DBP + (SBP - DBP) / 3.

    Parameters:
        sbp: systolic blood pressure in mmHg (must be positive)
        dbp: diastolic blood pressure in mmHg (must be non-negative and <= sbp)

    Raises:
        ValueError: if inputs are invalid
    """
    _validate_number(sbp, "SBP", positive=True)
    _validate_number(dbp, "DBP")
    if dbp < 0:
        raise ValueError(f"DBP must be non-negative, got {dbp}")
    if dbp > sbp:
        raise ValueError(f"DBP ({dbp}) cannot exceed SBP ({sbp})")
    return _finite_result(dbp + (sbp - dbp) / 3.0, "Mean arterial pressure")


# ── Classification ───────────────────────────────────────────────────

def classify_si(si_value):
    """Classify a Shock Index value.

    Returns a dict with risk level, description, and clinical action.
    """
    _validate_number(si_value, "Shock index", positive=True)
    if si_value < SI_NORMAL_LOW:
        return {
            "risk_level": "low",
            "description": "Below normal range",
            "clinical_action": "Interpret with other vital signs and clinical context",
        }
    elif si_value <= SI_NORMAL_HIGH:
        return {
            "risk_level": "normal",
            "description": "Normal range (0.5-0.7)",
            "clinical_action": "Interpret with other vital signs and clinical context",
        }
    elif si_value <= SI_HEMORRHAGE:
        return {
            "risk_level": "elevated",
            "description": "Elevated (0.7-0.9)",
            "clinical_action": "Assess the underlying clinical context",
        }
    elif si_value <= SI_HIGH_MORTALITY:
        return {
            "risk_level": "high",
            "description": "Elevated SI (>0.9); possible association with adverse outcomes",
            "clinical_action": "Prompt clinical assessment may be warranted",
        }
    elif si_value <= SI_CRITICAL:
        return {
            "risk_level": "very_high",
            "description": "Marked SI elevation (>1.0); clinical interpretation required",
            "clinical_action": "Urgent clinical assessment may be warranted",
        }
    else:
        return {
            "risk_level": "critical",
            "description": "Markedly elevated SI (>1.4); risk is population-dependent",
            "clinical_action": "Urgent clinical assessment may be warranted",
        }


def classify_msi(msi_value):
    """Describe MSI with published research cutoffs, not SI thresholds.

    Values <0.7 or >1.3 have been associated with increased risk in
    selected ED cohorts; they are not universal clinical decision rules.
    """
    _validate_number(msi_value, "Modified shock index", positive=True)
    if msi_value < 0.7:
        return {
            "risk_level": "outside_studied_interval",
            "description": "MSI <0.7 in observational ED cohorts",
            "clinical_action": "Interpret with clinical context; not a treatment trigger",
        }
    if msi_value > 1.3:
        return {
            "risk_level": "outside_studied_interval",
            "description": "MSI >1.3 in observational ED cohorts",
            "clinical_action": "Interpret with clinical context; not a treatment trigger",
        }
    return {
        "risk_level": "within_studied_interval",
        "description": "MSI within 0.7–1.3 in observational ED cohorts",
        "clinical_action": "Does not exclude shock or other illness",
    }


# ── Pediatric reference ranges ───────────────────────────────────────

def pediatric_si_reference(age_years):
    """Return age-appropriate SI reference range for pediatric patients.

    Children have higher baseline HR and lower SBP than adults.
    These are approximate reference ranges.

    Returns (low, high) tuple for normal SI range.
    """
    _validate_number(age_years, "Age")
    if age_years < 0:
        raise ValueError(f"Age must be non-negative, got {age_years}")
    if age_years < 1:
        return (0.7, 1.2)   # Infants: HR 100-160, SBP 60-90
    elif age_years < 3:
        return (0.7, 1.1)   # Toddlers: HR 90-150, SBP 70-100
    elif age_years < 6:
        return (0.6, 1.0)   # Preschool: HR 80-140, SBP 80-110
    elif age_years < 12:
        return (0.5, 0.9)   # School age: HR 70-120, SBP 85-120
    elif age_years < 18:
        return (0.5, 0.8)   # Adolescents: HR 60-100, SBP 90-130
    else:
        return (SI_NORMAL_LOW, SI_NORMAL_HIGH)  # Adults


def classify_si_pediatric(si_value, age_years):
    """Classify SI using age-appropriate pediatric thresholds."""
    _validate_number(si_value, "Shock index", positive=True)
    low, high = pediatric_si_reference(age_years)
    if si_value < low:
        return {
            "risk_level": "below_exploratory_range",
            "description": f"Below exploratory range for age {age_years} ({low}-{high})",
            "clinical_action": "Interpret cautiously; pediatric ranges are exploratory",
        }
    if si_value <= high:
        return {
            "risk_level": "normal",
            "description": f"Normal for age {age_years} (range {low}-{high})",
            "clinical_action": "Interpret cautiously; pediatric ranges are exploratory",
        }
    elif si_value <= high + 0.3:
        return {
            "risk_level": "elevated",
            "description": f"Elevated for age {age_years}",
            "clinical_action": "Consider comprehensive clinical assessment",
        }
    else:
        return {
            "risk_level": "high",
            "description": f"Significantly elevated for age {age_years}",
            "clinical_action": "Consider comprehensive clinical assessment",
        }


# ── Comprehensive assessment ─────────────────────────────────────────

def calculate_shock_index(hr, sbp, dbp=None, age=None, sex=None):
    """Calculate all shock index variants and return a comprehensive assessment.

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg
        dbp: diastolic blood pressure in mmHg (optional, needed for MSI)
        age: patient age in years (optional, for age-adjusted SI)
        sex: patient sex (optional, for documentation)

    Returns a dict with all calculated values and classifications.
    """
    si = shock_index(hr, sbp)
    rsi = reverse_shock_index(hr, sbp)

    result = {
        "hr_bpm": hr,
        "sbp_mmhg": sbp,
        "shock_index": round(si, 3),
        "reverse_si": round(rsi, 3),
        "si_classification": classify_si(si),
    }

    if dbp is not None:
        map_val = map_from_bp(sbp, dbp)
        msi = modified_shock_index(hr, sbp, dbp)
        result["dbp_mmhg"] = dbp
        result["map_mmhg"] = round(map_val, 1)
        result["modified_si"] = round(msi, 3)
        result["msi_classification"] = classify_msi(msi)

    if age is not None:
        aasi = age_adjusted_si(si, age)
        result["age"] = age
        result["age_adjusted_si"] = round(aasi, 3)

        if age < 18:
            result["pediatric_classification"] = classify_si_pediatric(si, age)

    if sex is not None:
        result["sex"] = sex

    return result


# ── CSV batch processing ─────────────────────────────────────────────

def process_csv(input_path, output_path):
    """Process a CSV file of vital signs and compute shock indices.

    Expected columns: hr (or heart_rate), sbp. Optional: dbp, age, sex.

    Raises:
        FileNotFoundError: if input_path does not exist
        ValueError: if required columns are missing
    """
    import os
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if not fieldnames:
        raise ValueError("CSV file is empty or has no header row")
    if any(not name for name in fieldnames) or len(set(fieldnames)) != len(fieldnames):
        raise ValueError("CSV headers must be non-empty and unique")

    # Validate required columns exist (hr or heart_rate, and sbp)
    has_hr = "hr" in fieldnames or "heart_rate" in fieldnames
    has_sbp = "sbp" in fieldnames
    if not has_hr or not has_sbp:
        raise ValueError(
            f"CSV must contain 'hr' (or 'heart_rate') and 'sbp' columns. Found: {fieldnames}"
        )

    results = []
    for row in rows:
        try:
            if None in row:
                raise ValueError("Row has more columns than the CSV header")
            hr_raw = row.get("hr") or row.get("heart_rate")
            sbp_raw = row.get("sbp")
            if not hr_raw or not sbp_raw:
                raise ValueError("Missing required 'hr' or 'sbp' value in row")
            hr = float(hr_raw)
            sbp = float(sbp_raw)
            dbp = row.get("dbp")
            age = row.get("age")
            sex = row.get("sex")

            res = calculate_shock_index(
                hr, sbp,
                dbp=float(dbp) if dbp else None,
                age=float(age) if age else None,
                sex=sex,
            )
            # Flatten for CSV
            flat = {
                "shock_index": res["shock_index"],
                "reverse_si": res["reverse_si"],
                "si_risk_level": res["si_classification"]["risk_level"],
                "si_description": res["si_classification"]["description"],
            }
            if "modified_si" in res:
                flat["modified_si"] = res["modified_si"]
                flat["map_mmhg"] = res["map_mmhg"]
            if "age_adjusted_si" in res:
                flat["age_adjusted_si"] = res["age_adjusted_si"]
        except (ValueError, TypeError, KeyError) as e:
            flat = {"error": str(e)}

        merged = {**row, **{k: str(v) for k, v in flat.items()}}
        results.append(merged)

    all_keys = set()
    for r in results:
        all_keys.update(r.keys())
    extra = sorted(k for k in all_keys if k not in fieldnames and k is not None)
    out_fields = fieldnames + (extra or ["shock_index", "reverse_si", "si_risk_level"])
    def safe_cell(value):
        """Prevent spreadsheet formula execution in exported CSV cells."""
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writerow({key: safe_cell(key) for key in out_fields})
        for row in results:
            writer.writerow({key: safe_cell(row.get(key, "")) for key in out_fields})

    return results


# ── CLI ──────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Shock Index (SI) & Modified Shock Index (MSI) Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single calculation
    single = subparsers.add_parser("single", help="Single patient calculation")
    single.add_argument("--hr", type=float, required=True, help="Heart rate (bpm)")
    single.add_argument("--sbp", type=float, required=True, help="Systolic BP (mmHg)")
    single.add_argument("--dbp", type=float, default=None, help="Diastolic BP (mmHg)")
    single.add_argument("--age", type=float, default=None, help="Age (years)")
    single.add_argument("--sex", default=None, help="Sex (male/female)")

    # Batch processing
    batch = subparsers.add_parser("batch", help="Batch process CSV")
    batch.add_argument("-i", "--input", required=True, help="Input CSV path")
    batch.add_argument("-o", "--output", default="results.csv", help="Output CSV path")

    args = parser.parse_args(argv)

    if args.command == "single":
        res = calculate_shock_index(
            args.hr, args.sbp,
            dbp=args.dbp, age=args.age, sex=args.sex,
        )
        print(json.dumps(res, indent=2))
        return 0

    if args.command == "batch":
        results = process_csv(args.input, args.output)
        print(f"Processed {len(results)} records -> {args.output}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
