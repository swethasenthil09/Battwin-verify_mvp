"""
Central RUL & EOL Service.

Distinguishes between:
1. Operational Prediction (no leakage, uses observations available up to current cycle).
2. Evaluation Ground Truth (full recorded battery history for benchmarking).
"""
import numpy as np
import pandas as pd

EOL_SOH_THRESHOLD = 70.0

def compute_rul_for_battery(df_analysis: pd.DataFrame, battery_id: str, physics_eol_cycle: int = None) -> dict:
    """
    Computes operational RUL prediction and ground-truth evaluation summary.
    """
    df_sorted = df_analysis.sort_values("discharge_cycle_index").reset_index(drop=True)
    if df_sorted.empty:
        raise ValueError(f"No analysis data found for battery {battery_id}")

    if "SoH_pred" not in df_sorted.columns:
        if "predicted_soh_pct" in df_sorted.columns:
            df_sorted["SoH_pred"] = df_sorted["predicted_soh_pct"]
        elif "adapted_predicted_soh" in df_sorted.columns:
            df_sorted["SoH_pred"] = df_sorted["adapted_predicted_soh"]
        elif "SoH_pct" in df_sorted.columns:
            df_sorted["SoH_pred"] = df_sorted["SoH_pct"]
        else:
            df_sorted["SoH_pred"] = 80.0

    if "SoH_pct" not in df_sorted.columns:
        if "observed_soh_pct" in df_sorted.columns:
            df_sorted["SoH_pct"] = df_sorted["observed_soh_pct"]
        else:
            df_sorted["SoH_pct"] = df_sorted["SoH_pred"]

    last_row = df_sorted.iloc[-1]
    current_cycle = int(last_row["discharge_cycle_index"])
    observed_soh = float(last_row["SoH_pct"])
    predicted_soh = float(last_row["SoH_pred"])

    # Ground-truth evaluation from complete recorded history
    soh_all = df_sorted["SoH_pct"].values
    cycles_all = df_sorted["discharge_cycle_index"].values

    # Permanent EOL crossing: first cycle where SoH remains <= 70.0% for all remaining cycles
    permanent_eol_idx = None
    for i in range(len(soh_all)):
        if np.all(soh_all[i:] <= EOL_SOH_THRESHOLD):
            permanent_eol_idx = i
            break

    actual_eol_permanent = int(cycles_all[permanent_eol_idx]) if permanent_eol_idx is not None else None

    # First touch EOL crossing
    below_indices = np.where(soh_all <= EOL_SOH_THRESHOLD)[0]
    actual_eol_first_touch = int(cycles_all[below_indices[0]]) if len(below_indices) else None

    actual_rul_delta = (actual_eol_permanent - current_cycle) if actual_eol_permanent is not None else 0

    # --- OPERATIONAL PREDICTION (No test leakage) ---
    # Check if currently available observations establish that EOL has already been reached
    eol_reached = (observed_soh <= EOL_SOH_THRESHOLD)

    if eol_reached:
        rul_ai = 0.0
    else:
        # Use recent window (last 20-30 cycles) for robust degradation slope
        window_size = min(30, len(df_sorted))
        recent_df = df_sorted.iloc[-window_size:]
        slope, intercept = np.polyfit(recent_df["discharge_cycle_index"], recent_df["SoH_pred"], 1)

        if slope < 0:
            eol_cycle_pred = (EOL_SOH_THRESHOLD - intercept) / slope
            rul_ai = max(0.0, round(float(eol_cycle_pred - current_cycle), 1))
        else:
            rul_ai = 999.0

    # Operational Physics RUL
    if physics_eol_cycle is not None:
        rul_physics = max(0, physics_eol_cycle - current_cycle) if physics_eol_cycle >= current_cycle else 0
    else:
        rul_physics = None

    note_text = (
        "Battery has permanently reached EOL threshold (70% SoH). Operational RUL is 0 cycles."
        if eol_reached
        else f"Operational RUL estimated via recent degradation slope ({rul_ai} cycles remaining)."
    )

    eol_note = (
        f"Naive first-crossing EOL was cycle {actual_eol_first_touch}, but real capacity recovery "
        f"(documented Li-ion relaxation) pushed SoH back above threshold. "
        f"Corrected permanent EOL is cycle {actual_eol_permanent}."
        if actual_eol_first_touch and actual_eol_permanent and actual_eol_first_touch != actual_eol_permanent
        else f"Permanent EOL threshold crossing identified at cycle {actual_eol_permanent}."
    )

    return {
        "battery_id": battery_id,
        "current_cycle": current_cycle,
        "observed_soh_pct": round(observed_soh, 2),
        "predicted_soh_pct": round(predicted_soh, 2),
        "eol_reached": bool(eol_reached),
        "rul_ai_cycles": rul_ai,
        "rul_physics_cycles": rul_physics,
        "note": note_text,
        "EOL_definition_note": eol_note,
        "evaluation": {
            "actual_eol_cycle_permanent": actual_eol_permanent,
            "actual_eol_cycle_first_touch": actual_eol_first_touch,
            "actual_rul_delta": actual_rul_delta,
        }
    }