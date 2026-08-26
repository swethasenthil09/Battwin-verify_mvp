"""
Extract real NASA PCoE battery data (B0005, B0006, B0007, B0018) from .mat
into a clean per-cycle feature table. No synthetic data, no interpolgiven
values invented -- only real measured summary statistics per real cycle.
"""
import scipy.io as sio
import numpy as np
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUT_CSV = os.path.join(DATA_DIR, "nasa_battery_cycles.csv")

SRC_DIR = os.path.join(BASE_DIR, "raw_mat_data")
BATTERIES = ["B0005", "B0006", "B0007", "B0018"]

if os.path.exists(SRC_DIR):
    rows = []
    for bname in BATTERIES:
        path = os.path.join(SRC_DIR, f"{bname}.mat")
        if not os.path.exists(path):
            continue
        d = sio.loadmat(path, simplify_cells=True)
        cycles = d[bname]["cycle"]

        discharge_idx = 0
        for c in cycles:
            if c["type"] != "discharge":
                continue
            discharge_idx += 1
            data = c["data"]

            voltage = np.asarray(data["Voltage_measured"], dtype=float)
            current = np.asarray(data["Current_measured"], dtype=float)
            temperature = np.asarray(data["Temperature_measured"], dtype=float)
            capacity = float(data["Capacity"])  # real measured discharge capacity (Ah)
            ambient_temp = c.get("ambient_temperature", np.nan)

            rows.append({
                "battery_id": bname,
                "discharge_cycle_index": discharge_idx,   # proxy for cycle-based battery age
                "capacity_Ah": capacity,
                "ambient_temperature_C": ambient_temp,
                "voltage_mean": np.nanmean(voltage),
                "voltage_min": np.nanmin(voltage),
                "voltage_max": np.nanmax(voltage),
                "current_mean": np.nanmean(current),
                "current_min": np.nanmin(current),
                "temperature_mean": np.nanmean(temperature),
                "temperature_max": np.nanmax(temperature),
                "discharge_duration_s": float(np.nanmax(data["Time"])) if len(data["Time"]) else np.nan,
            })

    if rows:
        df = pd.DataFrame(rows)
        RATED_CAPACITY = 2.0
        df["SoH_pct"] = (df["capacity_Ah"] / RATED_CAPACITY) * 100.0
        df.to_csv(OUT_CSV, index=False)
        print("Extracted dataset to:", OUT_CSV)
else:
    print(f"Raw .mat source directory '{SRC_DIR}' not found. Using pre-extracted CSV at '{OUT_CSV}'.")
    df = pd.read_csv(OUT_CSV)
print(df.groupby("battery_id").agg(
    n_cycles=("discharge_cycle_index", "max"),
    start_capacity=("capacity_Ah", "first"),
    end_capacity=("capacity_Ah", "last"),
    start_SoH=("SoH_pct", "first"),
    end_SoH=("SoH_pct", "last"),
))
print("\nTotal rows:", len(df))
print(df.head())