"""
Step 3: RUL via real capacity-fade trend extrapolation to EOL (1.4 Ah / 70% SoH).
Step 4: Independent physics-lite reference -- exponential capacity-fade model
        fit ONLY on early cycles, extrapolated forward. This is deliberately
        NOT the same model family as XGBoost, so agreement/disagreement with
        the AI model is a meaningful independent check, not a restatement.
No fabricated numbers -- both are computed from the real measured trajectory.
"""
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

df = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))
EOL_CAPACITY = 1.4
RATED_CAPACITY = 2.0

def exp_fade(cycle, a, b, c):
    # capacity(cycle) = a * exp(-b * cycle) + c   -- standard empirical Li-ion fade form
    return a * np.exp(-b * cycle) + c

results = []
for bid, g in df.groupby("battery_id"):
    g = g.sort_values("discharge_cycle_index").reset_index(drop=True)
    n = len(g)

    # Use first 40% of real cycles to fit the physics-lite curve
    fit_frac = 0.4
    n_fit = max(10, int(n * fit_frac))
    fit_data = g.iloc[:n_fit]

    try:
        # Bounds: a in [0.1, 1.5], b in [0, 0.1], c in [0, 1.35] so asymptotic capacity drops below EOL (1.4Ah)
        popt, _ = curve_fit(
            exp_fade, fit_data.discharge_cycle_index, fit_data.capacity_Ah,
            p0=[0.5, 0.005, 1.0], bounds=([0.05, 1e-6, 0.0], [1.5, 0.1, 1.35]), maxfev=10000
        )
        future_cycles = np.arange(1, n + 300)
        sim_capacity = exp_fade(future_cycles, *popt)
        eol_candidates = future_cycles[sim_capacity <= EOL_CAPACITY]
        physics_eol_cycle = int(eol_candidates[0]) if len(eol_candidates) else None
    except Exception as e:
        popt = None
        physics_eol_cycle = None

    below_eol = g[g.capacity_Ah <= EOL_CAPACITY]
    actual_eol_cycle = int(below_eol.discharge_cycle_index.iloc[0]) if len(below_eol) else None

    last_cycle = int(g.discharge_cycle_index.iloc[-1])
    physics_rul_from_last = (physics_eol_cycle - last_cycle) if physics_eol_cycle else None
    actual_rul_from_last = (actual_eol_cycle - last_cycle) if actual_eol_cycle else 0

    results.append({
        "battery_id": bid,
        "n_real_cycles": n,
        "fit_on_first_n_cycles": n_fit,
        "physics_predicted_EOL_cycle": physics_eol_cycle,
        "actual_EOL_cycle_in_data": actual_eol_cycle,
        "physics_RUL_error_cycles": (physics_eol_cycle - actual_eol_cycle) if (physics_eol_cycle and actual_eol_cycle) else None,
    })

res_df = pd.DataFrame(results)
print(res_df.to_string(index=False))
res_df.to_csv(os.path.join(DATA_DIR, "physics_rul_results.csv"), index=False)