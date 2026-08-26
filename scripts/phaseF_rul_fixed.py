"""
Phase F (corrected): Real Li-ion capacity recovery/relaxation causes transient
dips below the EOL threshold before permanent failure (documented phenomenon,
visible directly in B0018's real trace at cycles 106 and 121). A correct EOL
definition requires a PERMANENT crossing, not a first-touch crossing.
"""
import pandas as pd
import numpy as np
import json

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
EOL_SOH = 70.0

import sys
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.dirname(BASE_DIR))
sys.path.insert(0, os.path.join(os.path.dirname(BASE_DIR), "backend"))

try:
    from backend.services.rul_service import compute_rul_for_battery
except ImportError:
    from services.rul_service import compute_rul_for_battery

physics_res = pd.read_csv(os.path.join(DATA_DIR, "physics_rul_results.csv")).set_index("battery_id")

all_rul_summaries = {}

for bid in ["B0005", "B0006", "B0007", "B0018"]:
    fpath = os.path.join(DATA_DIR, f"{bid.lower()}_full_analysis.csv")
    merged = pd.read_csv(fpath)

    p_info = physics_res.loc[bid] if bid in physics_res.index else None
    physics_eol = int(p_info["physics_predicted_EOL_cycle"]) if p_info is not None and not pd.isna(p_info["physics_predicted_EOL_cycle"]) else None

    summary = compute_rul_for_battery(merged, bid, physics_eol_cycle=physics_eol)

    # Add backward compatible aliases for frontend fallback
    summary["last_observed_cycle"] = summary["current_cycle"]
    summary["last_observed_SoH_pct"] = summary["predicted_soh_pct"]
    summary["RUL_ai_trend_cycles"] = summary["rul_ai_cycles"]
    summary["RUL_physics_cycles"] = summary["rul_physics_cycles"]
    summary["RUL_actual_cycles_in_recorded_data"] = summary["evaluation"]["actual_rul_delta"]
    summary["actual_EOL_cycle_permanent"] = summary["evaluation"]["actual_eol_cycle_permanent"]
    summary["actual_EOL_cycle_first_touch_naive"] = summary["evaluation"]["actual_eol_cycle_first_touch"]

    all_rul_summaries[bid] = summary

print(json.dumps(all_rul_summaries["B0018"], indent=2))

with open(os.path.join(DATA_DIR, "b0018_rul_summary.json"), "w") as f:
    json.dump(all_rul_summaries["B0018"], f, indent=2)

with open(os.path.join(DATA_DIR, "all_rul_summaries.json"), "w") as f:
    json.dump(all_rul_summaries, f, indent=2)