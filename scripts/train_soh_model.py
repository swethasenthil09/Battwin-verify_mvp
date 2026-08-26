"""
Train a real SoH regression model with a battery-level (leakage-safe) split:
train on B0005, B0006, B0007; test on B0018 entirely held out.
No row-level shuffling across the split -- this tests generalization to an
unseen physical battery, not memorization within one battery's trajectory.
"""
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

df = pd.read_csv(os.path.join(DATA_DIR, "nasa_battery_cycles.csv"))

FEATURES = [
    "discharge_cycle_index", "ambient_temperature_C",
    "voltage_mean", "voltage_min", "voltage_max",
    "current_mean", "current_min",
    "temperature_mean", "temperature_max",
    "discharge_duration_s",
]
TARGET = "SoH_pct"

train_df = df[df.battery_id.isin(["B0005", "B0006", "B0007"])]
test_df  = df[df.battery_id == "B0018"]

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_test, y_test = test_df[FEATURES], test_df[TARGET]

model = XGBRegressor(
    n_estimators=200, max_depth=4, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, random_state=42
)
model.fit(X_train, y_train)

pred = model.predict(X_test)
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)

print(f"Held-out battery: B0018 (n={len(test_df)} real cycles, never seen in training)")
print(f"SoH MAE:  {mae:.3f} %")
print(f"SoH RMSE: {rmse:.3f} %")
print(f"SoH R2:   {r2:.4f}")

joblib.dump(model, os.path.join(DATA_DIR, "soh_model.joblib"))

# Save predictions for all batteries for multi-battery support
for bid in ["B0005", "B0006", "B0007", "B0018"]:
    b_df = df[df.battery_id == bid].copy()
    b_pred = model.predict(b_df[FEATURES])
    b_df["SoH_pred"] = b_pred
    out_name = "b0018_predictions.csv" if bid == "B0018" else f"{bid.lower()}_predictions.csv"
    b_df.to_csv(os.path.join(DATA_DIR, out_name), index=False)

print("Saved predictions for all batteries to data/")