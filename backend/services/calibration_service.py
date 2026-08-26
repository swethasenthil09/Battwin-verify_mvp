"""
Zero-Leakage Split-Conformal Calibration Service.

Derives calibration width (q80) strictly from training batteries (B0005, B0006, B0007).
Test battery (B0018) is never used during calibration width estimation.
"""
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split

FEATURES = [
    "discharge_cycle_index", "ambient_temperature_C",
    "voltage_mean", "voltage_min", "voltage_max",
    "current_mean", "current_min",
    "temperature_mean", "temperature_max",
    "discharge_duration_s",
]

def compute_calibration_widths(df_cycles: pd.DataFrame) -> dict:
    """
    Computes naive Gaussian z80 half-width and zero-leakage split-conformal q80 half-width.
    """
    train_df = df_cycles[df_cycles.battery_id.isin(["B0005", "B0006", "B0007"])].copy()

    # 1. Naive training residual std (z80 = 1.28 for ~80% Gaussian interval)
    # Fit initial model on all training data
    model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
    model.fit(train_df[FEATURES], train_df["SoH_pct"])
    train_pred_all = model.predict(train_df[FEATURES])
    naive_std = float((train_df["SoH_pct"].values - train_pred_all).std())
    z80 = 1.28
    naive_half_width = float(z80 * naive_std)

    # 2. Zero-Leakage Split-Conformal Quantile (q80)
    # Hold out a calibration split strictly from within training batteries
    fit_idx, calib_idx = train_test_split(train_df.index, test_size=0.25, random_state=42)
    fit_set = train_df.loc[fit_idx]
    calib_set = train_df.loc[calib_idx]

    model_calib = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)
    model_calib.fit(fit_set[FEATURES], fit_set["SoH_pct"])

    calib_pred = model_calib.predict(calib_set[FEATURES])
    nonconformity = np.abs(calib_set["SoH_pct"].values - calib_pred)
    q80_half_width = float(np.quantile(nonconformity, 0.80))

    return {
        "naive_half_width": round(naive_half_width, 4),
        "conformal_half_width": round(q80_half_width, 4),
        "target_coverage_pct": 80.0
    }

def apply_calibration_bounds(df_target_analysis: pd.DataFrame, calibration_info: dict) -> tuple:
    """
    Applies before and after calibration bounds to a target battery's predictions.
    """
    merged = df_target_analysis.copy()
    pred = merged["SoH_pred"].values if "SoH_pred" in merged.columns else merged["predicted_soh_pct"].values
    actual = merged["SoH_pct"].values if "SoH_pct" in merged.columns else merged["observed_soh_pct"].values

    hw_before = calibration_info["naive_half_width"]
    hw_after = calibration_info["conformal_half_width"]

    before_lower = pred - hw_before
    before_upper = pred + hw_before
    cov_before = float(np.mean((actual >= before_lower) & (actual <= before_upper)))

    after_lower = pred - hw_after
    after_upper = pred + hw_after
    cov_after = float(np.mean((actual >= after_lower) & (actual <= after_upper)))

    merged["lower80_before"] = before_lower
    merged["upper80_before"] = before_upper
    merged["lower80_after"] = after_lower
    merged["upper80_after"] = after_upper

    calib_summary = {
        "calibration_before": {
            "coverage": round(cov_before, 4),
            "half_width": round(hw_before, 4),
            "coverage_pct": round(cov_before * 100.0, 1),
        },
        "calibration_after": {
            "coverage": round(cov_after, 4),
            "half_width": round(hw_after, 4),
            "coverage_pct": round(cov_after * 100.0, 1),
        },
        "warning": "Uncertainty calibration needs improvement under domain shift." if cov_after < 0.5 else None
    }

    return merged, calib_summary