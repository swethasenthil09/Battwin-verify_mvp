# BATTWIN-VERIFY — Reliability-Aware BESS Intelligence MVP

Built for: P5 — Smart Battery Energy Storage Management & RUL Prediction.

**Everything in here runs on real NASA PCoE battery data. No synthetic
rows, no hand-set metrics, no hardcoded predictions.** Where a result was
weak or a model failed, that's reported as-is (see "Honest findings" below)
rather than hidden.

## What's in this package

```
data/        Real extracted NASA cycle data + all computed model outputs
backend/     FastAPI app serving the real pipeline outputs + live predict endpoint
frontend/    Vite + React modern digital twin dashboard (npm run dev)
scripts/     The actual analysis pipeline, in run order
docs/        Original design + research-gap documents
```

## Running the React Frontend

```bash
cd frontend
npm install
npm run dev
```

The React dashboard works standalone with an embedded snapshot. If the FastAPI backend is running on `localhost:8000`, the dashboard automatically detects it and switches to **LIVE** mode.


## Running the real pipeline yourself (reproduces every number)

```bash
cd scripts
pip install pandas numpy scipy scikit-learn xgboost joblib

python extract_data.py          # NASA .mat -> clean cycle table
python train_soh_model.py       # XGBoost, held out on B0018 entirely
python rul_and_physics.py       # physics-lite exponential fade model
python cross_fidelity.py        # gap metrics + reliability score v1
python phaseE_calibration.py    # conformal calibration, before/after
python phaseF_rul_fixed.py      # RUL with corrected EOL definition
```

Note: the raw NASA `.mat` files themselves aren't bundled here (they're
~100MB) — `data/nasa_battery_cycles.csv` is the already-extracted real
output of `extract_data.py`, so everything downstream still reproduces
exactly from the CSVs included.

## Running the backend

```bash
cd backend
pip install fastapi uvicorn pandas
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /api/batteries` — summary of all 4 real batteries
- `GET /api/battery/B0018/analysis` — full per-cycle AI/physics/measured comparison
- `GET /api/battery/B0018/reliability` — composite reliability score + components
- `GET /api/battery/B0018/rul` — RUL from three independent methods
- `GET /api/battery/B0018/recommendation` — rule-based charge/discharge policy

## Method summary

- **Data**: NASA Ames PCoE Li-ion Battery Aging Dataset (Saha & Goebel, 2007).
  Batteries B0005, B0006, B0007 (training), B0018 (held out entirely — the
  model never sees this battery during training). Rated capacity 2.0Ah,
  EOL = 30% fade = 1.4Ah, per NASA's own documentation.
- **AI model**: XGBoost regressor on real per-cycle summary features
  (voltage/current/temperature stats, ambient temp, cycle index).
  Battery-level train/test split — not a random row split — so the
  reported error is genuine cross-battery generalization, not memorization.
- **Physics reference**: independent exponential capacity-fade curve,
  fit only on the first 40% of each battery's real cycles, extrapolated
  forward. Deliberately a different model family from the AI model so
  agreement/disagreement between them is a meaningful cross-check.
- **Reliability score**: weighted composite of six real, computed
  components (data completeness, domain similarity, AI agreement,
  simulation fidelity, AI-vs-physics cross-check, uncertainty quality).
  Weights are explicitly stated defaults, not tuned to produce a
  particular score — flagged in the design docs as a project metric,
  not an industry standard.

## Honest findings (worth leading the presentation with)

1. **AI SoH model**: MAE = 1.86%, R² = 0.92 on the fully held-out battery.
   Legitimate, reproducible number.
2. **Physics-lite model is much weaker** (MAE 5.12%) and **failed to
   converge on an end-of-life prediction at all** for B0018 — reported
   as a low-confidence flag, not hidden or faked.
3. **Uncertainty was badly miscalibrated**: a naive residual-std interval
   gave only 6.1% empirical coverage against an intended 80%. Split-conformal
   calibration improved this to 18.9% — real progress, but still short,
   which is itself evidence that interval-widening alone can't fix a genuine
   domain shift; a real domain-adaptation step is needed.
4. **The most important finding**: the AI model systematically
   *overestimates* SoH by 3–4 points in the battery's final real cycles —
   it reports the battery as still above the 70% EOL threshold at cycle 132
   (predicted 71.75%) when the battery had already permanently crossed EOL
   at cycle 123 (real data). Average accuracy hid a safety-relevant late-life
   bias. This is exactly the failure mode the reliability-score architecture
   exists to catch.
5. **Real capacity recovery** (a documented Li-ion relaxation effect) is
   visible in B0018's own data at cycles 106 and 121 — SoH transiently
   jumps back above the EOL line before permanently failing. The EOL
   definition was corrected from "first crossing" to "permanent crossing"
   to account for this.

## Explicit Disclosures & Simplifications (Design Doc vs. Current Implementation)

To ensure full transparency during evaluation, the following design doc items are simplified or scoped for MVP:

1. **State of Charge (SoC) Estimation**: Per-cycle Coulomb counting summary is computed (`/api/battery/{id}/soc`), but extended continuous EKF state estimation is deferred.
2. **Physics Reference Model**: Uses a 3-parameter exponential capacity-fade empirical curve fit rather than a full 2-RC Equivalent Circuit Model (ECM) voltage/current dynamics simulator.
3. **Data Completeness Metric**: Computed dynamically from missing feature cells and cycle step continuity rather than assumed at 1.0.
4. **Data Persistence**: Uses portable CSV/JSON file storage for MVP execution instead of a hosted PostgreSQL relational database.
5. **Incomplete-Data Stress Testing**: Sensor packet masking (Experiment C in evaluation plan) is deferred to Phase 2.
6. **Cross-Fidelity Interpretive Framework**: Includes A/B/C/D scenario classification (Scenarios A, B, C, D) mapping AI agreement vs. physics fidelity.
7. **Live Inference Engine**: Exposes a real-time `POST /api/predict` endpoint loading `soh_model.joblib` for on-demand inference alongside precomputed CSV trajectory evaluation.
8. **Temporal Model Architecture**: Uses XGBoost tabular regression on cycle features instead of LSTM/GRU networks.
9. **Optimizer & Explainability**: Rule-based safety recommendation policy is used instead of CVXPY optimization; SHAP feature attribution layer is planned for Phase 2.
10. **Cross-Dataset Validation**: Evaluation is performed on NASA PCoE battery held-out sets; CALCE/Oxford cross-dataset validation is scheduled for Phase 2.