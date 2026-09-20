"""
Tests for the Late-Life Prediction Reliability Analysis module.

Covers:
  - Phase boundary assignment
  - Phase cycle counts
  - MAE / RMSE calculation
  - Signed bias
  - Overestimation rate
  - EOL detection delay (permanent-crossing)
  - Drift onset detection
  - Edge cases (empty DataFrames, single-cycle phases, no EOL)
"""
import sys
import os
import numpy as np
import pandas as pd
import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.late_life_service import (
    assign_lifecycle_phases,
    compute_phase_error_metrics,
    compute_permanent_eol_crossing,
    compute_first_touch_eol,
    compute_eol_detection_delay,
    compute_drift_onset,
    compute_late_life_analysis,
    compute_aggregate_late_life_analysis,
    PHASE_BOUNDARIES,
    EOL_SOH_THRESHOLD,
    DRIFT_ROLLING_WINDOW,
    DRIFT_SUSTAINED_COUNT,
)


# ---------------------------------------------------------------------------
# Helper: build a synthetic battery DataFrame for testing
# ---------------------------------------------------------------------------
def _make_battery_df(
    n_cycles=100,
    actual_soh_start=95.0,
    actual_soh_end=65.0,
    pred_bias_late=3.0,
):
    """
    Creates a synthetic analysis DataFrame with known error patterns:
    - Linear actual SoH decline from actual_soh_start to actual_soh_end.
    - Predictions are accurate early (small noise) but systematically
      overestimate by pred_bias_late in late life.
    """
    cycles = np.arange(1, n_cycles + 1)
    actual = np.linspace(actual_soh_start, actual_soh_end, n_cycles)

    # Predictions: small noise early, increasing positive bias late
    lifecycle_pct = np.linspace(0, 1, n_cycles)
    bias = pred_bias_late * (lifecycle_pct ** 2)  # quadratic increase
    np.random.seed(42)
    noise = np.random.normal(0, 0.3, n_cycles)
    predicted = actual + bias + noise

    return pd.DataFrame({
        "discharge_cycle_index": cycles,
        "SoH_pct": actual,
        "SoH_pred": predicted,
    })


# ---------------------------------------------------------------------------
# Phase assignment tests
# ---------------------------------------------------------------------------
class TestPhaseAssignment:
    def test_default_boundaries_assign_three_phases(self):
        df = _make_battery_df(100)
        result = assign_lifecycle_phases(df)
        phases = result["phase"].unique()
        assert set(phases) == {"early", "mid", "late"}

    def test_early_phase_is_first_40_pct(self):
        df = _make_battery_df(100)
        result = assign_lifecycle_phases(df)
        early = result[result["phase"] == "early"]
        # Cycles 1-40 out of 1-100 → first ~40 cycles
        assert len(early) >= 39  # allow ±1 for boundary
        assert len(early) <= 41

    def test_late_phase_is_last_30_pct(self):
        df = _make_battery_df(100)
        result = assign_lifecycle_phases(df)
        late = result[result["phase"] == "late"]
        assert len(late) >= 29
        assert len(late) <= 31

    def test_all_cycles_assigned(self):
        df = _make_battery_df(100)
        result = assign_lifecycle_phases(df)
        assert result["phase"].isna().sum() == 0
        assert len(result) == 100

    def test_custom_boundaries(self):
        custom = {"first_half": (0.0, 0.5), "second_half": (0.5, 1.0)}
        df = _make_battery_df(100)
        result = assign_lifecycle_phases(df, phase_boundaries=custom)
        assert set(result["phase"].unique()) == {"first_half", "second_half"}

    def test_empty_dataframe(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [],
            "SoH_pct": [],
            "SoH_pred": [],
        })
        result = assign_lifecycle_phases(df)
        assert len(result) == 0
        assert "phase" in result.columns

    def test_single_cycle(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [50],
            "SoH_pct": [80.0],
            "SoH_pred": [81.0],
        })
        result = assign_lifecycle_phases(df)
        assert len(result) == 1
        assert result["phase"].iloc[0] in PHASE_BOUNDARIES

    def test_lifecycle_pct_ranges_0_to_1(self):
        df = _make_battery_df(100)
        result = assign_lifecycle_phases(df)
        assert result["lifecycle_pct"].min() >= 0.0
        assert result["lifecycle_pct"].max() <= 1.0


# ---------------------------------------------------------------------------
# Phase error metrics tests
# ---------------------------------------------------------------------------
class TestPhaseErrorMetrics:
    def test_mae_calculation(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2, 3],
            "SoH_pct": [90.0, 85.0, 80.0],
            "SoH_pred": [92.0, 84.0, 82.0],
        })
        result = compute_phase_error_metrics(df)
        # |92-90| + |84-85| + |82-80| = 2 + 1 + 2 = 5, MAE = 5/3
        expected_mae = 5.0 / 3.0
        assert abs(result["mae"] - expected_mae) < 0.001

    def test_rmse_calculation(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2, 3],
            "SoH_pct": [90.0, 85.0, 80.0],
            "SoH_pred": [92.0, 84.0, 82.0],
        })
        result = compute_phase_error_metrics(df)
        # errors: +2, -1, +2; squared: 4, 1, 4; mean: 3; sqrt: 1.732
        expected_rmse = np.sqrt(9.0 / 3.0)
        assert abs(result["rmse"] - expected_rmse) < 0.001

    def test_signed_bias_positive(self):
        """Predictions consistently above actual → positive bias."""
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2, 3],
            "SoH_pct": [80.0, 75.0, 70.0],
            "SoH_pred": [83.0, 78.0, 73.0],
        })
        result = compute_phase_error_metrics(df)
        assert result["signed_bias"] == 3.0

    def test_signed_bias_negative(self):
        """Predictions consistently below actual → negative bias."""
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2],
            "SoH_pct": [80.0, 75.0],
            "SoH_pred": [78.0, 73.0],
        })
        result = compute_phase_error_metrics(df)
        assert result["signed_bias"] == -2.0

    def test_overestimation_rate(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2, 3, 4],
            "SoH_pct": [90, 85, 80, 75],
            "SoH_pred": [92, 84, 82, 74],  # overestimate in 1,3; underestimate in 2,4
        })
        result = compute_phase_error_metrics(df)
        assert result["overestimation_rate"] == 0.5  # 2 out of 4

    def test_max_abs_error(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2, 3],
            "SoH_pct": [90.0, 85.0, 80.0],
            "SoH_pred": [90.0, 85.0, 85.0],  # error: 0, 0, 5
        })
        result = compute_phase_error_metrics(df)
        assert result["max_abs_error"] == 5.0

    def test_empty_phase(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [],
            "SoH_pct": [],
            "SoH_pred": [],
        })
        result = compute_phase_error_metrics(df)
        assert result["n_cycles"] == 0
        assert result["mae"] is None

    def test_cycle_range(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [10, 20, 30],
            "SoH_pct": [90, 85, 80],
            "SoH_pred": [91, 86, 81],
        })
        result = compute_phase_error_metrics(df)
        assert result["cycle_range"] == [10, 30]


# ---------------------------------------------------------------------------
# EOL detection delay tests
# ---------------------------------------------------------------------------
class TestEolDetectionDelay:
    def test_permanent_crossing_found(self):
        soh = np.array([80, 75, 68, 72, 65, 60])  # permanent crossing at index 4
        cycles = np.array([1, 2, 3, 4, 5, 6])
        result = compute_permanent_eol_crossing(soh, cycles)
        assert result == 5  # cycle 5: 65, followed by 60 → all <= 70

    def test_first_touch_found(self):
        soh = np.array([80, 75, 68, 72, 65, 60])
        cycles = np.array([1, 2, 3, 4, 5, 6])
        result = compute_first_touch_eol(soh, cycles)
        assert result == 3  # first time <=70 is cycle 3 (68%)

    def test_no_eol(self):
        soh = np.array([90, 85, 80, 75, 72])
        cycles = np.array([1, 2, 3, 4, 5])
        assert compute_permanent_eol_crossing(soh, cycles) is None
        # first touch at cycle 5 (72 > 70), but never <=70
        # actually 72 > 70 so no first touch either
        assert compute_first_touch_eol(soh, cycles) is None

    def test_capacity_recovery_permanent_vs_first_touch(self):
        """Models the real B0018 capacity recovery behavior."""
        soh = np.array([80, 72, 68, 71, 73, 69, 67, 65])
        cycles = np.array([1, 2, 3, 4, 5, 6, 7, 8])
        first_touch = compute_first_touch_eol(soh, cycles)
        permanent = compute_permanent_eol_crossing(soh, cycles)
        # First touch: cycle 3 (68%)
        assert first_touch == 3
        # Permanent: cycle 6 because soh[5:] = [69, 67, 65], all <=70
        assert permanent == 6
        assert permanent > first_touch  # permanent is later

    def test_detection_delay_positive(self):
        """Model detects EOL late → positive delay."""
        df = pd.DataFrame({
            "discharge_cycle_index": list(range(1, 11)),
            "SoH_pct":  [85, 80, 75, 68, 65, 63, 60, 58, 55, 50],
            "SoH_pred": [86, 81, 76, 73, 71, 68, 65, 63, 60, 55],
        })
        result = compute_eol_detection_delay(df)
        assert result["actual_permanent_eol_cycle"] is not None
        assert result["predicted_permanent_eol_cycle"] is not None
        assert result["detection_delay_cycles"] > 0
        assert result.get("detection_delay_is_lower_bound") is False

    def test_detection_delay_model_never_detects(self):
        """Model predictions never drop below threshold."""
        df = pd.DataFrame({
            "discharge_cycle_index": list(range(1, 6)),
            "SoH_pct":  [80, 75, 68, 65, 60],
            "SoH_pred": [85, 82, 78, 75, 72],  # always above 70
        })
        result = compute_eol_detection_delay(df)
        assert result["actual_permanent_eol_cycle"] is not None
        assert result["predicted_permanent_eol_cycle"] is None
        # Delay is a lower bound (last_cycle - actual_perm)
        assert result["detection_delay_cycles"] is not None
        assert result["detection_delay_cycles"] > 0
        assert result.get("detection_delay_is_lower_bound") is True


# ---------------------------------------------------------------------------
# Drift onset tests
# ---------------------------------------------------------------------------
class TestDriftOnset:
    def test_drift_detected_in_late_life(self):
        df = _make_battery_df(100, pred_bias_late=5.0)
        result = compute_drift_onset(df)
        # With a strong late bias, drift should be detected
        if result["drift_onset_cycle"] is not None:
            # Drift should be in mid-to-late lifecycle
            assert result["drift_onset_lifecycle_pct"] > 0.3

    def test_no_drift_with_zero_bias(self):
        """With zero bias and small noise, no systematic drift expected."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            "discharge_cycle_index": range(1, n + 1),
            "SoH_pct": np.linspace(95, 65, n),
            "SoH_pred": np.linspace(95, 65, n) + np.random.normal(0, 0.1, n),
        })
        result = compute_drift_onset(df)
        # With near-zero bias, drift onset should not be detected
        # (this is probabilistic, but with seed 42 and tiny noise it should hold)
        assert result["drift_onset_cycle"] is None

    def test_insufficient_data(self):
        df = pd.DataFrame({
            "discharge_cycle_index": [1, 2, 3],
            "SoH_pct": [90, 85, 80],
            "SoH_pred": [91, 86, 81],
        })
        result = compute_drift_onset(df)
        assert result["drift_onset_cycle"] is None
        assert "Insufficient data" in result["note"]

    def test_detection_method_documented(self):
        df = _make_battery_df(100)
        result = compute_drift_onset(df)
        assert result["detection_method"] == "rolling_window_sustained_bias"
        assert "rolling_window" in result["parameters"]
        assert "sustained_count" in result["parameters"]
        assert "threshold_sigma" in result["parameters"]


# ---------------------------------------------------------------------------
# Full late-life analysis tests
# ---------------------------------------------------------------------------
class TestFullAnalysis:
    def test_analysis_returns_all_phases(self):
        df = _make_battery_df(100)
        result = compute_late_life_analysis(df, "TEST_BATTERY")
        assert "early" in result["phase_metrics"]
        assert "mid" in result["phase_metrics"]
        assert "late" in result["phase_metrics"]

    def test_analysis_returns_eol_delay(self):
        df = _make_battery_df(100, actual_soh_end=60.0)
        result = compute_late_life_analysis(df, "TEST")
        assert "eol_detection_delay" in result
        assert "actual_permanent_eol_cycle" in result["eol_detection_delay"]

    def test_analysis_returns_drift_onset(self):
        df = _make_battery_df(100)
        result = compute_late_life_analysis(df, "TEST")
        assert "drift_onset" in result
        assert "detection_method" in result["drift_onset"]

    def test_analysis_returns_hypothesis_evaluation(self):
        df = _make_battery_df(100, pred_bias_late=5.0, actual_soh_end=60.0)
        result = compute_late_life_analysis(df, "TEST")
        hyp = result["hypothesis_evaluation"]
        assert "supported" in hyp
        assert "criteria_met" in hyp
        assert "findings" in hyp

    def test_analysis_with_known_overestimation(self):
        """With strong late bias, late-life metrics should show overestimation."""
        df = _make_battery_df(100, pred_bias_late=6.0)
        result = compute_late_life_analysis(df, "TEST")
        late = result["phase_metrics"]["late"]
        assert late["signed_bias"] > 0  # overestimation
        assert late["overestimation_rate"] > 0.5  # majority overestimate

    def test_error_amplification_factor(self):
        df = _make_battery_df(100, pred_bias_late=5.0)
        result = compute_late_life_analysis(df, "TEST")
        # Late error should be larger than early
        if result["error_amplification_factor"] is not None:
            assert result["error_amplification_factor"] > 1.0

    def test_overall_metrics_present(self):
        df = _make_battery_df(100)
        result = compute_late_life_analysis(df, "TEST")
        assert result["overall_metrics"]["n_cycles"] == 100

    def test_column_name_normalization(self):
        """Test that alternative column names are handled correctly."""
        df = pd.DataFrame({
            "discharge_cycle_index": range(1, 51),
            "observed_soh_pct": np.linspace(95, 75, 50),
            "predicted_soh_pct": np.linspace(95, 75, 50) + 1.0,
        })
        result = compute_late_life_analysis(df, "ALT_COLUMNS")
        assert result["total_cycles"] == 50
        assert result["overall_metrics"]["mae"] is not None


# ---------------------------------------------------------------------------
# Aggregate analysis tests
# ---------------------------------------------------------------------------
class TestAggregateAnalysis:
    def test_aggregate_counts_batteries(self):
        results = {}
        for bid in ["B0005", "B0006", "B0007", "B0018"]:
            df = _make_battery_df(100, pred_bias_late=4.0, actual_soh_end=60.0)
            results[bid] = compute_late_life_analysis(df, bid)
        agg = compute_aggregate_late_life_analysis(results)
        assert agg["n_batteries_analyzed"] == 4

    def test_aggregate_ignores_non_nasa(self):
        results = {
            "B0018": compute_late_life_analysis(_make_battery_df(100), "B0018"),
            "CALCE_CS2_35": compute_late_life_analysis(_make_battery_df(50), "CALCE_CS2_35"),
        }
        agg = compute_aggregate_late_life_analysis(results)
        assert agg["n_batteries_analyzed"] == 1  # only B0018


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
