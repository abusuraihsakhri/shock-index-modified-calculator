"""Tests for shock_index.py — Shock Index Calculator.

Run with: python -m pytest test_shock_index.py -v
"""
import pytest
from shock_index import (
    shock_index, modified_shock_index, age_adjusted_si,
    reverse_shock_index, map_from_bp, classify_si,
    classify_si_pediatric, pediatric_si_reference,
    calculate_shock_index, process_csv,
)


# ── Basic shock index ───────────────────────────────────────────────

class TestShockIndex:
    def test_normal_values(self):
        # HR=80, SBP=120: SI = 80/120 = 0.667
        assert abs(shock_index(80, 120) - 0.667) < 0.01

    def test_high_si(self):
        # HR=120, SBP=80: SI = 120/80 = 1.5
        assert abs(shock_index(120, 80) - 1.5) < 0.01

    def test_low_si(self):
        # HR=60, SBP=120: SI = 60/120 = 0.5
        assert abs(shock_index(60, 120) - 0.5) < 0.01

    def test_invalid_hr(self):
        with pytest.raises(ValueError):
            shock_index(0, 120)

    def test_invalid_sbp(self):
        with pytest.raises(ValueError):
            shock_index(80, 0)


# ── Modified shock index ────────────────────────────────────────────

class TestModifiedShockIndex:
    def test_normal_values(self):
        # HR=80, SBP=120, DBP=80: MAP=93.3, MSI=80/93.3=0.857
        result = modified_shock_index(80, 120, 80)
        expected_map = 80 + (120 - 80) / 3.0
        assert abs(result - 80 / expected_map) < 0.01

    def test_dbp_exceeds_sbp(self):
        with pytest.raises(ValueError):
            modified_shock_index(80, 80, 120)


# ── Age-adjusted SI ─────────────────────────────────────────────────

class TestAgeAdjustedSI:
    def test_age_50(self):
        # Age-SI = SI / (50/100) = SI / 0.5 = 2*SI
        assert abs(age_adjusted_si(0.6, 50) - 1.2) < 0.01

    def test_age_100(self):
        # Age-SI = SI / (100/100) = SI
        assert abs(age_adjusted_si(0.6, 100) - 0.6) < 0.01

    def test_invalid_age(self):
        with pytest.raises(ValueError):
            age_adjusted_si(0.6, 0)


# ── Reverse SI ──────────────────────────────────────────────────────

class TestReverseSI:
    def test_normal(self):
        # RSI = 120/80 = 1.5
        assert abs(reverse_shock_index(80, 120) - 1.5) < 0.01

    def test_concerning(self):
        # RSI = 80/120 = 0.667 (< 1.0 is concerning)
        assert abs(reverse_shock_index(120, 80) - 0.667) < 0.01


# ── MAP from BP ─────────────────────────────────────────────────────

class TestMAPFromBP:
    def test_standard(self):
        # MAP = 80 + (120-80)/3 = 93.33
        assert abs(map_from_bp(120, 80) - 93.33) < 0.1

    def test_equal_bp(self):
        # MAP = 100 + (100-100)/3 = 100
        assert map_from_bp(100, 100) == 100.0


# ── SI classification ───────────────────────────────────────────────

class TestClassifySI:
    def test_normal(self):
        result = classify_si(0.6)
        assert result["risk_level"] == "normal"

    def test_elevated(self):
        result = classify_si(0.8)
        assert result["risk_level"] == "elevated"

    def test_high(self):
        result = classify_si(0.95)
        assert result["risk_level"] == "high"

    def test_very_high(self):
        result = classify_si(1.1)
        assert result["risk_level"] == "very_high"

    def test_critical(self):
        result = classify_si(1.5)
        assert result["risk_level"] == "critical"

    def test_low(self):
        result = classify_si(0.4)
        assert result["risk_level"] == "low"


# ── Pediatric reference ─────────────────────────────────────────────

class TestPediatricReference:
    def test_infant(self):
        low, high = pediatric_si_reference(0.5)
        assert low == 0.7
        assert high == 1.2

    def test_school_age(self):
        low, high = pediatric_si_reference(8)
        assert low == 0.5
        assert high == 0.9

    def test_adult(self):
        low, high = pediatric_si_reference(30)
        assert low == 0.5
        assert high == 0.7

    def test_pediatric_classification_normal(self):
        result = classify_si_pediatric(0.9, 0.5)  # Infant, SI=0.9
        assert result["risk_level"] == "normal"

    def test_pediatric_classification_elevated(self):
        result = classify_si_pediatric(1.3, 0.5)  # Infant, SI=1.3
        assert result["risk_level"] == "elevated"


# ── Comprehensive assessment ────────────────────────────────────────

class TestCalculateShockIndex:
    def test_basic(self):
        result = calculate_shock_index(80, 120)
        assert "shock_index" in result
        assert "reverse_si" in result
        assert abs(result["shock_index"] - 0.667) < 0.01

    def test_with_dbp(self):
        result = calculate_shock_index(80, 120, dbp=80)
        assert "modified_si" in result
        assert "map_mmhg" in result

    def test_with_age(self):
        result = calculate_shock_index(80, 120, age=50)
        assert "age_adjusted_si" in result

    def test_with_pediatric_age(self):
        result = calculate_shock_index(100, 80, age=5)
        assert "pediatric_classification" in result

    def test_all_fields_present(self):
        result = calculate_shock_index(80, 120, dbp=80, age=50, sex="male")
        assert "shock_index" in result
        assert "modified_si" in result
        assert "age_adjusted_si" in result
        assert "sex" in result
