"""
Phase 2: Incomplete-Data Sensor Packet Masking Experiment (Experiment C).

Evaluates AI model resilience and reliability score degradation under simulated
sensor packet dropouts (10%, 30%, and 50% missing feature values).
Uses the shared compute_composite_reliability function.
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)

try:
    from backend.services.reliability_service import compute_composite_reliability
except ImportError:
    from services.reliability_service import compute_composite_reliability

FEATURES = [
    "discharge_cycle_index", "ambient_temperature_C",
    "voltage_mean", "voltage_min", "voltage_max",
    "current_mean", "current_min",
    "temperature_mean", "temperature_max",
    "discharge_duration_s"
]

def run_data_masking_experiment():
    model = joblib.load(os.path.join(DATA_DIR, "soh_model.joblib"))
    df = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))
    b18 = df[df.battery_id == "B0018"].sort_values("discharge_cycle_index").reset_index(drop=True)

    np.random.seed(42)
    feature_means = b18[FEATURES].mean()

    masking_levels = [0, 10, 30, 50]
    results = []

    for mask_pct in masking_levels:
        masked_X = b18[FEATURES].copy()
        if mask_pct > 0:
            mask = np.random.rand(*masked_X.shape) < (mask_pct / 100.0)
            # Impute missing cells with baseline feature means (standard sensor packet drop strategy)
            for i, col in enumerate(FEATURES):
                val = feature_means[col]
                if pd.api.types.is_integer_dtype(masked_X[col]):
                    val = int(round(val))
                masked_X.iloc[mask[:, i], i] = val

        pred = model.predict(masked_X)
        mae = float(np.mean(np.abs(b18["SoH_pct"] - pred)))
        rmse = float(np.sqrt(np.mean((b18["SoH_pct"] - pred) ** 2)))

        data_completeness = round(1.0 - (mask_pct / 100.0), 2)
        ai_agreement = max(0.0, 1.0 - mae / 20.0)

        # Call single shared reliability-score function
        rel_eval = compute_composite_reliability(
            data_completeness=data_completeness,
            domain_similarity=1.0,
            ai_agreement=ai_agreement,
            sim_fidelity=0.865,
            cross_model_agreement=0.918,
            uncertainty_coverage_before=0.045,
            uncertainty_coverage_after=0.174
        )
        rel_score = rel_eval["reliability_score_after_calibration"]

        results.append({
            "sensor_dropout_pct": mask_pct,
            "data_completeness_rating": data_completeness,
            "mae_pct": round(mae, 2),
            "rmse_pct": round(rmse, 2),
            "reliability_score": rel_score,
            "status": "Nominal" if mask_pct == 0 else "Minor Degradation" if mask_pct == 10 else "Moderate Degradation" if mask_pct == 30 else "Severe Dropout / High Risk"
        })

    output = {
        "experiment_name": "Experiment C: Sensor Packet Dropout & Masking Resilience",
        "battery_id": "B0018",
        "masking_results": results
    }

    out_file = os.path.join(DATA_DIR, "data_masking_experiment.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print("=== Sensor Packet Masking Experiment (Experiment C) Complete ===")
    for r in results:
        print(f"Dropout: {r['sensor_dropout_pct']}% -> MAE: {r['mae_pct']}% | Reliability Score: {r['reliability_score']}/100 ({r['status']})")

    return output

if __name__ == "__main__":
    run_data_masking_experiment()

