"""
K2: Explicit Domain-Shift Detector Module.

Analyzes operational condition shift (ambient temperature, voltage/current profile,
cycle duration distributions) between a target battery and the training population
(B0005, B0006, B0007). Returns domain shift score, component shift metrics,
and explicit status flags (NOMINAL, MODERATE_SHIFT, HIGH_SHIFT).
"""
import pandas as pd
import numpy as np
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def detect_domain_shift(target_battery_id: str, df: pd.DataFrame = None) -> dict:
    if df is None:
        df = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))

    train_ids = ["B0005", "B0006", "B0007"]
    train_df = df[df.battery_id.isin(train_ids)]
    target_df = df[df.battery_id == target_battery_id]

    if target_df.empty:
        raise ValueError(f"Battery {target_battery_id} not found in dataset")

    # 1. Ambient Temperature Shift
    train_temp_mean = float(train_df.ambient_temperature_C.mean())
    target_temp_mean = float(target_df.ambient_temperature_C.mean())
    temp_shift_c = abs(train_temp_mean - target_temp_mean)
    temp_shift_score = min(100.0, (temp_shift_c / 10.0) * 100.0)

    # 2. Voltage Profile Shift
    train_v_mean = float(train_df.voltage_mean.mean())
    train_v_std = float(train_df.voltage_mean.std()) if float(train_df.voltage_mean.std()) > 0 else 1.0
    target_v_mean = float(target_df.voltage_mean.mean())
    v_shift_z = abs(target_v_mean - train_v_mean) / train_v_std

    # 3. Discharge Current Shift
    train_i_mean = float(train_df.current_mean.mean())
    train_i_std = float(train_df.current_mean.std()) if float(train_df.current_mean.std()) > 0 else 1.0
    target_i_mean = float(target_df.current_mean.mean())
    i_shift_z = abs(target_i_mean - train_i_mean) / train_i_std

    # 4. Discharge Duration Shift
    train_d_mean = float(train_df.discharge_duration_s.mean())
    train_d_std = float(train_df.discharge_duration_s.std()) if float(train_df.discharge_duration_s.std()) > 0 else 1.0
    target_d_mean = float(target_df.discharge_duration_s.mean())
    d_shift_z = abs(target_d_mean - train_d_mean) / train_d_std

    # Composite Z-score profile shift
    composite_z = float((v_shift_z + i_shift_z + d_shift_z) / 3.0)
    profile_shift_score = min(100.0, (composite_z / 3.0) * 100.0)

    # Overall Domain Shift Index (0 = identical, 100 = severe out-of-domain)
    domain_shift_index = float(0.6 * temp_shift_score + 0.4 * profile_shift_score)

    if domain_shift_index < 15:
        status_flag = "NOMINAL"
        severity = "In-Domain Training Population"
        recommendation_impact = "Standard model confidence applies."
    elif domain_shift_index < 40:
        status_flag = "MODERATE_SHIFT"
        severity = "Moderate Operating Condition Variance"
        recommendation_impact = "Apply mild interval widening and conservative charge caps."
    else:
        status_flag = "HIGH_SHIFT"
        severity = "Significant Out-of-Domain Shift Detected"
        recommendation_impact = "Require conformal recalibration and mandate conservative operational caps."

    # Explanatory details
    details = []
    if temp_shift_c > 0.5:
        details.append(f"Ambient temperature shift: target={target_temp_mean:.1f}°C vs train avg={train_temp_mean:.1f}°C (ΔT={temp_shift_c:.1f}°C).")
    else:
        details.append(f"Ambient temperature closely matches training population ({target_temp_mean:.1f}°C).")

    if composite_z > 1.0:
        details.append(f"Operating waveform profile deviates from training envelope (average feature Z-score shift = {composite_z:.2f}).")
    else:
        details.append("Voltage/current waveform summary statistics lie within standard training bounds.")

    return {
        "target_battery_id": target_battery_id,
        "is_held_out": (target_battery_id == "B0018"),
        "status_flag": status_flag,
        "domain_shift_index_pct": round(domain_shift_index, 1),
        "domain_similarity_score": round(max(0.0, 1.0 - (domain_shift_index / 100.0)), 3),
        "severity": severity,
        "ambient_temp_shift_c": round(temp_shift_c, 2),
        "ambient_temp_target_c": round(target_temp_mean, 2),
        "ambient_temp_train_c": round(train_temp_mean, 2),
        "feature_profile_shift_z": round(composite_z, 2),
        "details": details,
        "recommendation_impact": recommendation_impact,
    }

def generate_all_domain_shift_summaries():
    df = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))
    all_summaries = {}
    for bid in ["B0005", "B0006", "B0007", "B0018"]:
        all_summaries[bid] = detect_domain_shift(bid, df)

    out_file = os.path.join(DATA_DIR, "domain_shift_summary.json")
    with open(out_file, "w") as f:
        json.dump(all_summaries, f, indent=2)
    print("Saved domain shift summaries to:", out_file)
    return all_summaries

if __name__ == "__main__":
    res = generate_all_domain_shift_summaries()
    print(json.dumps(res["B0018"], indent=2))