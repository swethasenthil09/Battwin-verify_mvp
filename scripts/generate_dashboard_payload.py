"""
Generate data/dashboard_payload.json containing embedded data for all 4 batteries,
reliability summaries, RUL, recommendations, and domain shift analysis.
"""
import os
import sys
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from backend.recommendation import recommend

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

cycles_df = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))

with open(os.path.join(DATA_DIR, "all_reliability_summaries.json")) as f:
    all_reliability = json.load(f)

with open(os.path.join(DATA_DIR, "all_rul_summaries.json")) as f:
    all_rul = json.load(f)

with open(os.path.join(DATA_DIR, "domain_shift_summary.json")) as f:
    domain_shift = json.load(f)

calce_shift = {}
calce_shift_path = os.path.join(DATA_DIR, "calce_domain_shift_summary.json")
if os.path.exists(calce_shift_path):
    with open(calce_shift_path) as f:
        calce_shift = json.load(f)

shap_data = {}
shap_path = os.path.join(DATA_DIR, "shap_explainability.json")
if os.path.exists(shap_path):
    with open(shap_path) as f:
        shap_data = json.load(f)

ecm_data = {}
ecm_path = os.path.join(DATA_DIR, "ecm_physics_results.json")
if os.path.exists(ecm_path):
    with open(ecm_path) as f:
        ecm_data = json.load(f)

masking_data = {}
masking_path = os.path.join(DATA_DIR, "data_masking_experiment.json")
if os.path.exists(masking_path):
    with open(masking_path) as f:
        masking_data = json.load(f)

payload = {
    "batteries": [],
    "analyses": {},
    "reliability": all_reliability,
    "rul": all_rul,
    "domain_shift": domain_shift,
    "calce_domain_shift": calce_shift,
    "shap_explainability": shap_data,
    "ecm_physics": ecm_data,
    "data_masking_experiment": masking_data,
    "recommendations": {}
}


for bid in ["B0018", "B0005", "B0006", "B0007"]:
    g = cycles_df[cycles_df.battery_id == bid]
    payload["batteries"].append({
        "battery_id": bid,
        "n_cycles": int(g.discharge_cycle_index.max()),
        "start_SoH": round(float(g.SoH_pct.iloc[0]), 2),
        "end_SoH": round(float(g.SoH_pct.iloc[-1]), 2),
        "role": "held-out test battery (never trained on)" if bid == "B0018" else "training battery",
    })

    analysis_csv = os.path.join(DATA_DIR, f"{bid.lower()}_full_analysis.csv")
    if os.path.exists(analysis_csv):
        df_an = pd.read_csv(analysis_csv).sort_values("discharge_cycle_index")
        payload["analyses"][bid] = df_an.to_dict(orient="records")

        last = df_an.iloc[-1]
        rel = all_reliability.get(bid, {})
        score = rel.get("reliability_score_after_calibration", rel.get("reliability_score", 75.0))
        disagreement = rel.get("ai_vs_physics_mae", 0.0)

        rec = recommend(
            soh_pct=float(last.SoH_pred),
            temperature_c=float(last.temperature_mean),
            reliability_score=score,
            ai_physics_disagreement_pct=disagreement,
        )
        payload["recommendations"][bid] = rec

payload["b0018_analysis"] = payload["analyses"]["B0018"]
payload["reliability_b0018"] = payload["reliability"]["B0018"]

out_path = os.path.join(DATA_DIR, "dashboard_payload.json")
with open(out_path, "w") as f:
    json.dump(payload, f, indent=2)

print("Generated full multi-battery dashboard payload at:", out_path)

# Also update frontend embeddedData.js
frontend_data_dir = os.path.join(BASE_DIR, "frontend", "src", "data")
if os.path.exists(frontend_data_dir):
    js_content = f"export const EMBEDDED_DATA = {json.dumps(payload, indent=2)};\n"
    js_file = os.path.join(frontend_data_dir, "embeddedData.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    print("Exported embedded data to frontend at:", js_file)