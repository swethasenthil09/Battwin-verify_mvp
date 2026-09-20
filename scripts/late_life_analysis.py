"""
Late-Life Prediction Reliability Analysis — Pipeline Script.

Runs the phase-segmented late-life analysis for all 4 NASA PCoE batteries
and produces data/late_life_analysis.json.

This script is designed to be called as part of the run_all_pipeline.py
orchestration, or standalone.

Usage:
    python scripts/late_life_analysis.py
"""
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)

import pandas as pd
from backend.services.late_life_service import (
    compute_late_life_analysis,
    compute_aggregate_late_life_analysis,
    NASA_BATTERY_IDS,
    PHASE_BOUNDARIES,
)

def run_late_life_analysis():
    all_results = {}

    for bid in NASA_BATTERY_IDS:
        fpath = os.path.join(DATA_DIR, f"{bid.lower()}_full_analysis.csv")
        if not os.path.exists(fpath):
            print(f"  [SKIP] {bid}: analysis file not found at {fpath}")
            continue

        df = pd.read_csv(fpath)
        result = compute_late_life_analysis(df, bid)
        all_results[bid] = result

        # Print per-battery summary
        print(f"\n--- {bid} ({result['total_cycles']} cycles) ---")
        for phase_name, metrics in result["phase_metrics"].items():
            if metrics["n_cycles"] > 0:
                print(
                    f"  {phase_name.upper():6s}: "
                    f"MAE={metrics['mae']:.3f}%  "
                    f"RMSE={metrics['rmse']:.3f}%  "
                    f"Bias={metrics['signed_bias']:+.3f}%  "
                    f"MaxErr={metrics['max_abs_error']:.3f}%  "
                    f"Overest={metrics['overestimation_rate']:.1%}  "
                    f"Cycles={metrics['cycle_range']}"
                )
            else:
                print(f"  {phase_name.upper():6s}: (no cycles)")

        eol = result["eol_detection_delay"]
        if eol["actual_permanent_eol_cycle"] is not None:
            print(f"  EOL actual permanent: cycle {eol['actual_permanent_eol_cycle']}")
            print(f"  EOL predicted permanent: cycle {eol['predicted_permanent_eol_cycle']}")
            if eol["detection_delay_cycles"] is not None:
                print(f"  Detection delay: {eol['detection_delay_cycles']} cycles")
        else:
            print("  EOL: not reached in recorded data")

        drift = result["drift_onset"]
        if drift["drift_onset_cycle"] is not None:
            print(f"  Drift onset: cycle {drift['drift_onset_cycle']} ({drift['drift_onset_lifecycle_pct']:.1%} lifecycle)")
        else:
            print("  Drift onset: not detected")

        hyp = result["hypothesis_evaluation"]
        print(f"  Hypothesis: {'SUPPORTED' if hyp['supported'] else 'NOT SUPPORTED'} ({hyp['criteria_met']}/{hyp['criteria_total']} criteria)")

    # Aggregate analysis
    aggregate = compute_aggregate_late_life_analysis(all_results)

    output = {
        "analysis_name": "Late-Life Prediction Reliability Analysis",
        "dataset": "NASA PCoE Li-ion Battery Aging Dataset",
        "batteries_analyzed": NASA_BATTERY_IDS,
        "phase_boundaries": {k: {"start_pct": v[0], "end_pct": v[1]} for k, v in PHASE_BOUNDARIES.items()},
        "per_battery_results": all_results,
        "aggregate_results": aggregate,
    }

    out_path = os.path.join(DATA_DIR, "late_life_analysis.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Late-Life Prediction Reliability Analysis Complete ===")
    print(f"Output: {out_path}")
    print(f"\nAggregate: {aggregate['overall_conclusion']}")

    return output


if __name__ == "__main__":
    run_late_life_analysis()
