"""
Late-Life Prediction Reliability Analysis Service.

Segments battery lifecycle into configurable phases (Early/Mid/Late) and
computes error metrics per phase to quantify whether the AI SoH model
degrades systematically in late-life operation.

Exposes:
  - Phase-segmented MAE, RMSE, signed bias, max absolute error
  - Late-life overestimation rate (fraction of late-life cycles where
    predicted SoH > actual SoH)
  - EOL detection delay (cycles between actual permanent EOL and
    predicted permanent EOL)
  - Drift onset detection (first cycle where a sustained systematic bias
    exceeds a statistically derived threshold)

Design decisions:
  - Phase boundaries are configurable constants, not hard-coded.
  - NASA batteries only (B0005, B0006, B0007, B0018).
  - Reuses permanent-crossing EOL logic from rul_service.
  - Does NOT modify the existing 6-component Reliability Score.
  - Reports results honestly; does not assume the late-life hypothesis
    is true.
"""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configurable phase boundaries (fraction of total lifecycle)
# ---------------------------------------------------------------------------
PHASE_BOUNDARIES = {
    "early": (0.0, 0.4),   # 0% – 40% of lifecycle
    "mid":   (0.4, 0.7),   # 40% – 70% of lifecycle
    "late":  (0.7, 1.0),   # 70% – 100% of lifecycle
}

# Drift onset detection parameters
DRIFT_ROLLING_WINDOW = 10       # cycles for rolling bias calculation
DRIFT_SUSTAINED_COUNT = 5       # consecutive windows above threshold
DRIFT_THRESHOLD_SIGMA = 1.0     # threshold = mean_bias + sigma * std_bias

# EOL threshold (must match existing rul_service.EOL_SOH_THRESHOLD)
EOL_SOH_THRESHOLD = 70.0

# NASA batteries for primary analysis
NASA_BATTERY_IDS = ["B0005", "B0006", "B0007", "B0018"]


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names so the service works regardless of whether the
    DataFrame uses SoH_pct/SoH_pred or observed_soh_pct/predicted_soh_pct.
    """
    df = df.copy()
    if "SoH_pred" not in df.columns:
        if "predicted_soh_pct" in df.columns:
            df["SoH_pred"] = df["predicted_soh_pct"]
        elif "adapted_predicted_soh" in df.columns:
            df["SoH_pred"] = df["adapted_predicted_soh"]
    if "SoH_pct" not in df.columns:
        if "observed_soh_pct" in df.columns:
            df["SoH_pct"] = df["observed_soh_pct"]
    return df


def assign_lifecycle_phases(
    df: pd.DataFrame,
    phase_boundaries: dict = None,
) -> pd.DataFrame:
    """
    Assigns a lifecycle phase label to each cycle based on its position
    within the battery's total recorded lifecycle.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain 'discharge_cycle_index'.
    phase_boundaries : dict, optional
        Mapping of phase name -> (start_frac, end_frac).
        Defaults to PHASE_BOUNDARIES.

    Returns
    -------
    pd.DataFrame
        Copy of df with added columns: 'lifecycle_pct', 'phase'.
    """
    if phase_boundaries is None:
        phase_boundaries = PHASE_BOUNDARIES

    df = df.sort_values("discharge_cycle_index").reset_index(drop=True)
    n = len(df)
    if n == 0:
        df["lifecycle_pct"] = []
        df["phase"] = []
        return df

    # lifecycle_pct: position of each cycle as fraction of total lifecycle
    # Cycle 1 → close to 0.0, last cycle → 1.0
    min_c = df["discharge_cycle_index"].min()
    max_c = df["discharge_cycle_index"].max()
    span = max_c - min_c
    if span == 0:
        df["lifecycle_pct"] = 0.5
    else:
        df["lifecycle_pct"] = (df["discharge_cycle_index"] - min_c) / span

    def _classify(pct):
        for phase_name, (lo, hi) in phase_boundaries.items():
            if lo <= pct < hi:
                return phase_name
        # Edge case: pct == 1.0 belongs to the last phase
        last_phase = list(phase_boundaries.keys())[-1]
        return last_phase

    df["phase"] = df["lifecycle_pct"].apply(_classify)
    return df


def compute_phase_error_metrics(df: pd.DataFrame) -> dict:
    """
    Computes error metrics for a single lifecycle phase subset.

    Parameters
    ----------
    df : pd.DataFrame
        Subset of analysis data for a single phase. Must contain
        'SoH_pct' and 'SoH_pred'.

    Returns
    -------
    dict with keys: n_cycles, mae, rmse, signed_bias, max_abs_error,
                    overestimation_rate, cycle_range
    """
    if df.empty:
        return {
            "n_cycles": 0,
            "mae": None,
            "rmse": None,
            "signed_bias": None,
            "max_abs_error": None,
            "overestimation_rate": None,
            "cycle_range": None,
        }

    actual = df["SoH_pct"].values
    predicted = df["SoH_pred"].values
    errors = predicted - actual  # positive = overestimation

    abs_errors = np.abs(errors)
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    signed_bias = float(np.mean(errors))  # positive = systematic overestimation
    max_abs_error = float(np.max(abs_errors))
    overestimation_rate = float(np.mean(errors > 0))

    cycle_min = int(df["discharge_cycle_index"].min())
    cycle_max = int(df["discharge_cycle_index"].max())

    return {
        "n_cycles": len(df),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "signed_bias": round(signed_bias, 4),
        "max_abs_error": round(max_abs_error, 4),
        "overestimation_rate": round(overestimation_rate, 4),
        "cycle_range": [cycle_min, cycle_max],
    }


def compute_permanent_eol_crossing(soh_values: np.ndarray, cycles: np.ndarray) -> int:
    """
    Finds the first cycle where SoH remains <= EOL_SOH_THRESHOLD for all
    subsequent cycles (permanent crossing). Reuses the same logic as
    rul_service.compute_rul_for_battery.

    Returns cycle index or None if never permanently crossed.
    """
    for i in range(len(soh_values)):
        if np.all(soh_values[i:] <= EOL_SOH_THRESHOLD):
            return int(cycles[i])
    return None


def compute_first_touch_eol(soh_values: np.ndarray, cycles: np.ndarray) -> int:
    """
    Finds the first cycle where SoH drops to or below EOL threshold.
    Returns cycle index or None.
    """
    below = np.where(soh_values <= EOL_SOH_THRESHOLD)[0]
    if len(below) > 0:
        return int(cycles[below[0]])
    return None


def compute_eol_detection_delay(df: pd.DataFrame) -> dict:
    """
    Computes the delay between actual and predicted permanent EOL crossing.

    Four crossing types are distinguished:
      1. actual_first_touch_eol: first cycle where actual SoH <= 70%
      2. actual_permanent_eol: first cycle where actual SoH stays <= 70%
      3. predicted_first_touch_eol: first cycle where predicted SoH <= 70%
      4. predicted_permanent_eol: first cycle where predicted SoH stays <= 70%

    Detection delay = predicted_permanent_eol - actual_permanent_eol
    (positive = model detects EOL late; negative = early)
    """
    df = _ensure_columns(df)
    df_sorted = df.sort_values("discharge_cycle_index").reset_index(drop=True)

    actual_soh = df_sorted["SoH_pct"].values
    pred_soh = df_sorted["SoH_pred"].values
    cycles = df_sorted["discharge_cycle_index"].values

    actual_first_touch = compute_first_touch_eol(actual_soh, cycles)
    actual_permanent = compute_permanent_eol_crossing(actual_soh, cycles)
    predicted_first_touch = compute_first_touch_eol(pred_soh, cycles)
    predicted_permanent = compute_permanent_eol_crossing(pred_soh, cycles)

    # Detection delay based on permanent crossing (the scientifically
    # correct EOL definition given capacity recovery effects)
    delay_is_lower_bound = False
    if actual_permanent is not None and predicted_permanent is not None:
        delay_cycles = predicted_permanent - actual_permanent
    elif actual_permanent is not None and predicted_permanent is None:
        # Model never permanently predicts EOL within recorded data
        last_cycle = int(cycles[-1])
        delay_cycles = last_cycle - actual_permanent  # lower bound of delay
        delay_is_lower_bound = True
    else:
        delay_cycles = None

    return {
        "actual_first_touch_eol_cycle": actual_first_touch,
        "actual_permanent_eol_cycle": actual_permanent,
        "predicted_first_touch_eol_cycle": predicted_first_touch,
        "predicted_permanent_eol_cycle": predicted_permanent,
        "detection_delay_cycles": delay_cycles,
        "detection_delay_is_lower_bound": delay_is_lower_bound,
        "delay_interpretation": _interpret_delay(delay_cycles, predicted_permanent, actual_permanent),
    }


def _interpret_delay(delay, pred_perm, actual_perm):
    """Human-readable interpretation of the EOL detection delay."""
    if actual_perm is None:
        return "Battery did not permanently reach EOL within recorded data."
    if pred_perm is None:
        return (
            f"The model did not permanently cross the 70% EOL threshold within the "
            f"recorded dataset; the detection delay is therefore at least {delay} cycles."
        )
    if delay is None:
        return "Insufficient data to compute detection delay."
    if delay > 0:
        return (
            f"Model detected permanent EOL {delay} cycles LATE "
            f"(actual: cycle {actual_perm}, predicted: cycle {pred_perm}). "
            f"Late detection implies the model overestimates SoH during critical end-of-life operation."
        )
    elif delay < 0:
        return (
            f"Model detected permanent EOL {abs(delay)} cycles EARLY "
            f"(actual: cycle {actual_perm}, predicted: cycle {pred_perm}). "
            f"Conservative — model is cautious near end of life."
        )
    else:
        return (
            f"Model detected permanent EOL at exactly the correct cycle ({actual_perm}). "
            f"No detection delay."
        )


def compute_drift_onset(df: pd.DataFrame) -> dict:
    """
    Detects the onset of systematic prediction drift using a rolling-window
    bias analysis.

    Definition (reproducible criterion):
      The drift onset cycle is the FIRST cycle where the rolling-window
      mean signed error (predicted - actual) exceeds a threshold AND
      remains above that threshold for at least DRIFT_SUSTAINED_COUNT
      consecutive windows.

      Threshold = global_mean_bias + DRIFT_THRESHOLD_SIGMA * global_std_bias

    This captures sustained systematic overestimation rather than
    isolated noisy spikes. The parameters are exposed as module-level
    constants for reproducibility.

    Limitations:
      - Requires at least DRIFT_ROLLING_WINDOW cycles of data.
      - Sensitive to window size and sigma multiplier; these are documented
        defaults, not universally optimal values.
      - For batteries with few cycles (< 30), the detection may be unreliable.
      - Only detects positive drift (overestimation). Underestimation drift
        is not currently flagged.
    """
    df = _ensure_columns(df)
    df_sorted = df.sort_values("discharge_cycle_index").reset_index(drop=True)

    if len(df_sorted) < DRIFT_ROLLING_WINDOW + DRIFT_SUSTAINED_COUNT:
        return {
            "drift_onset_cycle": None,
            "drift_onset_lifecycle_pct": None,
            "detection_method": "rolling_window_sustained_bias",
            "parameters": {
                "rolling_window": DRIFT_ROLLING_WINDOW,
                "sustained_count": DRIFT_SUSTAINED_COUNT,
                "threshold_sigma": DRIFT_THRESHOLD_SIGMA,
            },
            "threshold_value": None,
            "note": "Insufficient data for drift detection "
                    f"(need >= {DRIFT_ROLLING_WINDOW + DRIFT_SUSTAINED_COUNT} cycles).",
        }

    errors = df_sorted["SoH_pred"].values - df_sorted["SoH_pct"].values
    cycles = df_sorted["discharge_cycle_index"].values

    global_mean = float(np.mean(errors))
    global_std = float(np.std(errors))
    threshold = global_mean + DRIFT_THRESHOLD_SIGMA * global_std

    # Rolling mean of signed error
    rolling_bias = pd.Series(errors).rolling(window=DRIFT_ROLLING_WINDOW, min_periods=DRIFT_ROLLING_WINDOW).mean().values

    # Find sustained exceedance
    above_threshold = rolling_bias > threshold
    drift_onset_idx = None
    consecutive = 0
    for i in range(len(above_threshold)):
        if above_threshold[i]:
            consecutive += 1
            if consecutive >= DRIFT_SUSTAINED_COUNT and drift_onset_idx is None:
                # The onset is at the start of the sustained run
                drift_onset_idx = i - DRIFT_SUSTAINED_COUNT + 1
        else:
            consecutive = 0

    # Lifecycle percentage at drift onset
    min_c = cycles[0]
    max_c = cycles[-1]
    span = max_c - min_c if max_c > min_c else 1

    if drift_onset_idx is not None:
        onset_cycle = int(cycles[drift_onset_idx])
        onset_pct = round(float((onset_cycle - min_c) / span), 4)
    else:
        onset_cycle = None
        onset_pct = None

    return {
        "drift_onset_cycle": onset_cycle,
        "drift_onset_lifecycle_pct": onset_pct,
        "detection_method": "rolling_window_sustained_bias",
        "parameters": {
            "rolling_window": DRIFT_ROLLING_WINDOW,
            "sustained_count": DRIFT_SUSTAINED_COUNT,
            "threshold_sigma": DRIFT_THRESHOLD_SIGMA,
        },
        "threshold_value": round(threshold, 4),
        "global_mean_bias": round(global_mean, 4),
        "global_std_bias": round(global_std, 4),
        "note": (
            f"Drift onset detected at cycle {onset_cycle} ({onset_pct:.1%} of lifecycle). "
            f"Rolling bias exceeded threshold ({threshold:.3f}%) for {DRIFT_SUSTAINED_COUNT}+ consecutive windows."
        ) if onset_cycle is not None else (
            "No sustained systematic drift detected with current parameters. "
            "The model's signed error does not show a persistent positive shift "
            "above the threshold."
        ),
    }


def compute_late_life_analysis(
    df_analysis: pd.DataFrame,
    battery_id: str,
    phase_boundaries: dict = None,
) -> dict:
    """
    Full late-life prediction reliability analysis for a single battery.

    Parameters
    ----------
    df_analysis : pd.DataFrame
        Full analysis DataFrame for the battery (from *_full_analysis.csv).
    battery_id : str
        Battery identifier (e.g., 'B0018').
    phase_boundaries : dict, optional
        Phase boundary definitions. Defaults to PHASE_BOUNDARIES.

    Returns
    -------
    dict with complete analysis results.
    """
    if phase_boundaries is None:
        phase_boundaries = PHASE_BOUNDARIES

    df = _ensure_columns(df_analysis)
    df = assign_lifecycle_phases(df, phase_boundaries)

    # Per-phase metrics
    phase_metrics = {}
    for phase_name in phase_boundaries:
        phase_df = df[df["phase"] == phase_name]
        phase_metrics[phase_name] = compute_phase_error_metrics(phase_df)

    # Overall metrics (for comparison)
    overall = compute_phase_error_metrics(df)

    # Late-life specific: overestimation analysis
    late_df = df[df["phase"] == "late"]
    late_overestimation = None
    if not late_df.empty:
        late_errors = late_df["SoH_pred"].values - late_df["SoH_pct"].values
        late_overestimation = {
            "mean_overestimation_pct": round(float(np.mean(late_errors[late_errors > 0])), 4) if np.any(late_errors > 0) else 0.0,
            "max_overestimation_pct": round(float(np.max(late_errors)), 4) if len(late_errors) > 0 else 0.0,
            "overestimation_rate": round(float(np.mean(late_errors > 0)), 4),
            "n_overestimating_cycles": int(np.sum(late_errors > 0)),
            "n_late_cycles": len(late_errors),
        }

    # EOL detection delay
    eol_delay = compute_eol_detection_delay(df)

    # Drift onset
    drift = compute_drift_onset(df)

    # Late-life error amplification factor
    early_metrics = phase_metrics.get("early", {})
    late_metrics = phase_metrics.get("late", {})
    if early_metrics.get("mae") and late_metrics.get("mae") and early_metrics["mae"] > 0:
        error_amplification = round(late_metrics["mae"] / early_metrics["mae"], 4)
    else:
        error_amplification = None

    # Summary determination
    late_life_hypothesis_supported = _evaluate_hypothesis(phase_metrics, eol_delay)

    return {
        "battery_id": battery_id,
        "total_cycles": len(df),
        "phase_boundaries": {k: {"start_pct": v[0], "end_pct": v[1]} for k, v in phase_boundaries.items()},
        "phase_metrics": phase_metrics,
        "overall_metrics": overall,
        "late_life_overestimation": late_overestimation,
        "eol_detection_delay": eol_delay,
        "drift_onset": drift,
        "error_amplification_factor": error_amplification,
        "hypothesis_evaluation": late_life_hypothesis_supported,
    }


def _evaluate_hypothesis(phase_metrics: dict, eol_delay: dict) -> dict:
    """
    Evaluates whether the data supports the hypothesis that predictions
    become less reliable in late life.

    Criteria:
      1. Late-life MAE > Early-life MAE
      2. Late-life signed bias is positive (overestimation)
      3. EOL detection is delayed (positive delay)

    Reports honestly if the hypothesis is NOT supported.
    """
    early = phase_metrics.get("early", {})
    late = phase_metrics.get("late", {})

    findings = []
    criteria_met = 0
    criteria_total = 3

    # Criterion 1: Late MAE > Early MAE
    if early.get("mae") is not None and late.get("mae") is not None:
        if late["mae"] > early["mae"]:
            findings.append(
                f"Late-life MAE ({late['mae']:.2f}%) exceeds early-life MAE "
                f"({early['mae']:.2f}%) — prediction accuracy degrades in late life."
            )
            criteria_met += 1
        else:
            findings.append(
                f"Late-life MAE ({late['mae']:.2f}%) does NOT exceed early-life MAE "
                f"({early['mae']:.2f}%) — no evidence of late-life accuracy degradation "
                f"for this battery."
            )
    else:
        findings.append("Insufficient data to compare early vs late MAE.")

    # Criterion 2: Late-life overestimation bias
    if late.get("signed_bias") is not None:
        if late["signed_bias"] > 0:
            findings.append(
                f"Late-life signed bias is +{late['signed_bias']:.2f}% "
                f"(systematic overestimation of SoH)."
            )
            criteria_met += 1
        else:
            findings.append(
                f"Late-life signed bias is {late['signed_bias']:.2f}% "
                f"(no systematic overestimation detected)."
            )
    else:
        findings.append("No late-life cycles available for bias analysis.")

    # Criterion 3: EOL detection delay
    delay = eol_delay.get("detection_delay_cycles")
    delay_is_lower_bound = eol_delay.get("detection_delay_is_lower_bound", False)
    if delay is not None:
        if delay > 0 and not delay_is_lower_bound:
            findings.append(
                f"EOL detection is delayed by {delay} cycles — "
                f"model fails to flag end-of-life in a timely manner."
            )
            criteria_met += 1
        elif delay > 0 and delay_is_lower_bound:
            findings.append(
                f"Actual permanent EOL at cycle {eol_delay.get('actual_permanent_eol_cycle')}, "
                f"but predicted permanent EOL never crossed. "
                f"Minimum observed detection gap is {delay} cycles."
            )
            criteria_met += 1
        elif delay == 0:
            findings.append("EOL detected at the correct cycle — no delay.")
        else:
            findings.append(
                f"EOL detected {abs(delay)} cycles early — model is conservative."
            )
    else:
        findings.append("EOL not reached in recorded data; delay not applicable.")

    supported = criteria_met >= 2
    return {
        "hypothesis": "Late-life predictions are less reliable than early/mid-life predictions",
        "supported": supported,
        "criteria_met": criteria_met,
        "criteria_total": criteria_total,
        "findings": findings,
        "conclusion": (
            f"SUPPORTED — {criteria_met}/{criteria_total} criteria met. "
            f"The AI model shows measurable degradation in prediction quality "
            f"during late-life battery operation."
        ) if supported else (
            f"NOT CLEARLY SUPPORTED — only {criteria_met}/{criteria_total} criteria met. "
            f"The evidence for systematic late-life prediction failure is "
            f"inconclusive for this battery."
        ),
    }


def compute_aggregate_late_life_analysis(
    all_results: dict,
) -> dict:
    """
    Aggregates late-life analysis across multiple NASA batteries to determine
    whether the late-life hypothesis holds generally.
    """
    batteries_supporting = 0
    batteries_total = 0
    aggregate_early_mae = []
    aggregate_mid_mae = []
    aggregate_late_mae = []
    aggregate_late_bias = []
    eol_delays = []

    for bid, result in all_results.items():
        if bid not in NASA_BATTERY_IDS:
            continue
        batteries_total += 1

        if result["hypothesis_evaluation"]["supported"]:
            batteries_supporting += 1

        early_m = result["phase_metrics"].get("early", {})
        mid_m = result["phase_metrics"].get("mid", {})
        late_m = result["phase_metrics"].get("late", {})

        if early_m.get("mae") is not None:
            aggregate_early_mae.append(early_m["mae"])
        if mid_m.get("mae") is not None:
            aggregate_mid_mae.append(mid_m["mae"])
        if late_m.get("mae") is not None:
            aggregate_late_mae.append(late_m["mae"])
        if late_m.get("signed_bias") is not None:
            aggregate_late_bias.append(late_m["signed_bias"])

        delay = result["eol_detection_delay"].get("detection_delay_cycles")
        if delay is not None:
            eol_delays.append({"battery_id": bid, "delay_cycles": delay})

    mean_early_mae = round(float(np.mean(aggregate_early_mae)), 4) if aggregate_early_mae else None
    mean_mid_mae = round(float(np.mean(aggregate_mid_mae)), 4) if aggregate_mid_mae else None
    mean_late_mae = round(float(np.mean(aggregate_late_mae)), 4) if aggregate_late_mae else None
    mean_late_bias = round(float(np.mean(aggregate_late_bias)), 4) if aggregate_late_bias else None

    return {
        "n_batteries_analyzed": batteries_total,
        "n_batteries_supporting_hypothesis": batteries_supporting,
        "aggregate_mae_by_phase": {
            "early": mean_early_mae,
            "mid": mean_mid_mae,
            "late": mean_late_mae,
        },
        "mean_late_life_bias": mean_late_bias,
        "eol_detection_delays": eol_delays,
        "overall_conclusion": (
            f"The late-life prediction degradation hypothesis is supported by "
            f"{batteries_supporting}/{batteries_total} NASA batteries. "
            f"Mean late-life MAE ({mean_late_mae}%) vs early-life MAE ({mean_early_mae}%). "
            f"Mean late-life signed bias: {mean_late_bias:+.2f}%."
        ) if mean_late_mae is not None and mean_early_mae is not None else (
            "Insufficient data for aggregate conclusion."
        ),
    }
