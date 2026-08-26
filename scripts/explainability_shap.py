"""
Phase 2: SHAP & Model Explainability Layer.

Computes feature attribution importance scores and per-cycle contribution vectors
to explain XGBoost State of Health (SoH) predictions using real shap.TreeExplainer.
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
import shap

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

FEATURES = [
    "discharge_cycle_index", "ambient_temperature_C",
    "voltage_mean", "voltage_min", "voltage_max",
    "current_mean", "current_min",
    "temperature_mean", "temperature_max",
    "discharge_duration_s"
]

FEATURE_LABELS = {
    "discharge_cycle_index": "Discharge Cycle Index",
    "ambient_temperature_C": "Ambient Temperature (°C)",
    "voltage_mean": "Mean Discharge Voltage (V)",
    "voltage_min": "End-of-Discharge Voltage (V)",
    "voltage_max": "Initial Open-Circuit Voltage (V)",
    "current_mean": "Mean Current Draw (A)",
    "current_min": "Peak Current Draw (A)",
    "temperature_mean": "Mean Cell Temperature (°C)",
    "temperature_max": "Peak Cell Temperature (°C)",
    "discharge_duration_s": "Discharge Duration (s)"
}

def generate_shap_explainability():
    model_path = os.path.join(DATA_DIR, "soh_model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model = joblib.load(model_path)
    df_nasa = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))
    calce_path = os.path.join(DATA_DIR, "calce_battery_cycles.csv")
    df_calce = pd.read_csv(calce_path) if os.path.exists(calce_path) else pd.DataFrame()
    full_df = pd.concat([df_nasa, df_calce], ignore_index=True)

    X_full = full_df[FEATURES]

    # Real TreeExplainer computation
    explainer = shap.TreeExplainer(model)
    shap_values_full = explainer.shap_values(X_full)

    # 1. Global Feature Importances based on mean absolute SHAP values
    mean_abs_shap = np.mean(np.abs(shap_values_full), axis=0)
    tot_shap = np.sum(mean_abs_shap)
    norm_importances = mean_abs_shap / tot_shap if tot_shap > 0 else mean_abs_shap

    global_ranking = []
    for feat, imp in sorted(zip(FEATURES, norm_importances), key=lambda x: x[1], reverse=True):
        global_ranking.append({
            "feature_key": feat,
            "feature_name": FEATURE_LABELS.get(feat, feat),
            "importance_pct": round(float(imp * 100.0), 2)
        })

    all_explanations = {}

    for bid in ["B0018", "B0005", "B0006", "B0007", "CALCE_CS2_35"]:
        b_df = full_df[full_df.battery_id == bid].sort_values("discharge_cycle_index").reset_index(drop=True)
        if b_df.empty:
            continue

        baseline_soh = float(b_df["SoH_pct"].mean())
        cycle_explanations = {}

        max_c = int(b_df["discharge_cycle_index"].max())
        sample_cycles = [max(1, int(max_c * 0.1)), max(1, int(max_c * 0.5)), max_c]

        for cycle_idx in sample_cycles:
            matching = b_df[b_df.discharge_cycle_index == cycle_idx]
            if matching.empty:
                continue
            row = matching.iloc[0]
            row_df = pd.DataFrame([row[FEATURES].to_dict()])[FEATURES]

            pred_val = float(model.predict(row_df)[0])
            row_shap = explainer.shap_values(row_df)[0]

            contributions = []
            for i, feat in enumerate(FEATURES):
                feat_val = float(row[feat])
                shap_impact = float(row_shap[i])

                contributions.append({
                    "feature_key": feat,
                    "feature_name": FEATURE_LABELS.get(feat, feat),
                    "feature_value": round(feat_val, 2),
                    "shap_impact_delta": round(shap_impact, 2)
                })

            contributions.sort(key=lambda x: abs(x["shap_impact_delta"]), reverse=True)

            cycle_explanations[f"cycle_{cycle_idx}"] = {
                "discharge_cycle_index": cycle_idx,
                "actual_soh_pct": round(float(row["SoH_pct"]), 2),
                "predicted_soh_pct": round(pred_val, 2),
                "baseline_mean_soh_pct": round(baseline_soh, 2),
                "feature_contributions": contributions
            }

        all_explanations[bid] = {
            "battery_id": bid,
            "model_type": "XGBoost Regressor (TreeExplainer Attribution)",
            "global_feature_importances": global_ranking,
            "sample_cycle_explanations": cycle_explanations
        }

    out_file = os.path.join(DATA_DIR, "shap_explainability.json")
    with open(out_file, "w") as f:
        json.dump(all_explanations, f, indent=2)

    print("=== SHAP Real TreeExplainer Feature Attribution Complete ===")
    return all_explanations

if __name__ == "__main__":
    generate_shap_explainability()

