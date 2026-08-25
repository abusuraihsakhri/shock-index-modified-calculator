#!/usr/bin/env python3
"""
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

def shock_index(hr, sbp):
    """Calculate Shock Index: SI = HR / SBP.

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg

    Reference: Allgöwer M, Buri C. Schockindex. Dtsch Med Wschr 1967.

    >>> shock_index(80, 120)
    0.667
    """
    if hr <= 0:
        raise ValueError(f"Heart rate must be positive, got {hr}")
    if sbp <= 0:
        raise ValueError(f"SBP must be positive, got {sbp}")
    return hr / sbp


def modified_shock_index(hr, sbp, dbp):
    """Calculate Modified Shock Index: MSI = HR / MAP.

    MAP = DBP + (SBP - DBP) / 3

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg
        dbp: diastolic blood pressure in mmHg

    Reference: Mutschler M, et al. Crit Care 2013;17:R120.
    """
    if hr <= 0:
        raise ValueError(f"Heart rate must be positive, got {hr}")
    if sbp <= 0:
        raise ValueError(f"SBP must be positive, got {sbp}")
    if dbp < 0:
        raise ValueError(f"DBP must be non-negative, got {dbp}")
    if dbp > sbp:
        raise ValueError(f"DBP ({dbp}) cannot exceed SBP ({sbp})")
    map_val = dbp + (sbp - dbp) / 3.0
    return hr / map_val


def age_adjusted_si(si, age):
    """Calculate age-adjusted Shock Index: Age-SI = SI / (age / 100).

    Useful for elderly patients where normal SI ranges shift.

    Parameters:
        si:  shock index value
        age: patient age in years

    Reference: Zarzaur BL, et al. J Trauma 2010;68:1238-1243.
    """
    if age <= 0:
        raise ValueError(f"Age must be positive, got {age}")
    return si / (age / 100.0)


def reverse_shock_index(hr, sbp):
    """Calculate Reverse Shock Index: RSI = SBP / HR.

    Inverse of SI; higher values are better.  RSI < 1.0 is concerning.

    Parameters:
        hr:  heart rate in bpm
        sbp: systolic blood pressure in mmHg
    """
    if hr <= 0:
        raise ValueError(f"Heart rate must be positive, got {hr}")
    if sbp <= 0:
        raise ValueError(f"SBP must be positive, got {sbp}")
    return sbp / hr


def map_from_bp(sbp, dbp):
    """Calculate Mean Arterial Pressure: MAP = DBP + (SBP - DBP) / 3."""
    return dbp + (sbp - dbp) / 3.0


# ── Classification ───────────────────────────────────────────────────

def classify_si(si_value):
    """Classify a Shock Index value.

    Returns a dict with risk level, description, and clinical action.
    """
    if si_value < SI_NORMAL_LOW:
        return {
            "risk_level": "low",
            "description": "Below normal range",
            "clinical_action": "Routine monitoring",
        }
    elif si_value <= SI_NORMAL_HIGH:
        return {
            "risk_level": "normal",
            "description": "Normal range (0.5-0.7)",
            "clinical_action": "Standard monitoring",
        }
    elif si_value <= SI_HEMORRHAGE:
        return {
            "risk_level": "elevated",
            "description": "Elevated (0.7-0.9)",
            "clinical_action": "Increased monitoring, assess for occult bleeding",
        }
    elif si_value <= SI_HIGH_MORTALITY:
        return {
            "risk_level": "high",
            "description": "Suggests significant hemorrhage or sepsis (>0.9)",
            "clinical_action": "Aggressive resuscitation, consider blood products",
        }
    elif si_value <= SI_CRITICAL:
        return {
            "risk_level": "very_high",
            "description": "High mortality risk (>1.0)",
            "clinical_action": "Activate massive transfusion protocol, surgical consult",
        }
    else:
        return {
            "risk_level": "critical",
            "description": "Critical, >50% mortality (>1.4)",
            "clinical_action": "Immediate life-saving intervention required",
        }


# ── Pediatric reference ranges ───────────────────────────────────────

def pediatric_si_reference(age_years):
    """Return age-appropriate SI reference range for pediatric patients.

    Children have higher baseline HR and lower SBP than adults.
    These are approximate reference ranges.

    Returns (low, high) tuple for normal SI range.
    """
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
    low, high = pediatric_si_reference(age_years)
    if si_value <= high:
        return {
            "risk_level": "normal",
            "description": f"Normal for age {age_years} (range {low}-{high})",
            "clinical_action": "Standard monitoring",
        }
    elif si_value <= high + 0.3:
        return {
            "risk_level": "elevated",
            "description": f"Elevated for age {age_years}",
            "clinical_action": "Close monitoring, assess volume status",
        }
    else:
        return {
            "risk_level": "high",
            "description": f"Significantly elevated for age {age_years}",
            "clinical_action": "Urgent evaluation for hemorrhage/shock",
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
        result["msi_classification"] = classify_si(msi)

    if age is not None and age > 0:
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
    """
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    results = []
    for row in rows:
        try:
            hr = float(row.get("hr") or row.get("heart_rate"))
            sbp = float(row.get("sbp"))
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
    extra = sorted(k for k in all_keys if k not in fieldnames)
    out_fields = fieldnames + extra

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(results)

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
