# BATTWIN Verify

Reliability-aware battery intelligence for BESS monitoring, health estimation, and end-of-life decision support.

Built for: P5 — Smart Battery Energy Storage Management & RUL Prediction.

This project evaluates real NASA PCoE battery degradation data using a practical end-to-end workflow: data extraction, SoH modeling, physics-based comparison, reliability scoring, and a dashboard for interactive review.

## Why this project exists

The goal is to build a decision-support system that is transparent about model quality and failure modes, not just a high-accuracy demo. The repository intentionally reports weak or uncertain results alongside stronger ones so that reliability-aware failure analysis is visible in the system design.

## What is included

- Real NASA battery aging data and extracted cycle summaries
- AI-based state-of-health (SoH) estimation
- Physics-informed reference modeling
- Reliability scoring workflow for detection of unsafe late-life drift
- Backend API for battery diagnostics and recommendations
- React dashboard for exploration and visual comparison

## Repository structure

```text
data/         Real extracted NASA cycle data and computed outputs
backend/      FastAPI API serving the pipeline results and live prediction endpoint
frontend/     Vite + React dashboard for visual analytics
scripts/      Reproducible analysis pipeline, structured in execution order
docs/         Design notes, research-gap material, and supporting documentation
README.md     Project overview and setup instructions
```

## Key technical approach

- Data source: NASA Ames PCoE Li-ion battery aging dataset (Saha & Goebel, 2007)
- Training strategy: battery-level holdout validation on B0018, rather than random row-level splitting
- AI model: XGBoost regressor using cycle-level summary features
- Physics reference: exponential capacity-fade model fit on early-cycle data
- Reliability metric: composite score combining several real, computed factors such as data completeness, agreement quality, fidelity, and uncertainty behavior

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### 1) Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard can run as a standalone snapshot view and will automatically detect the backend at `localhost:8000` and switch into live mode when available.

### 2) Run the backend

```bash
cd backend
pip install fastapi uvicorn pandas
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Available endpoints include:

- `GET /api/batteries`
- `GET /api/battery/B0018/analysis`
- `GET /api/battery/B0018/reliability`
- `GET /api/battery/B0018/rul`
- `GET /api/battery/B0018/recommendation`
- `POST /api/predict`

### 3) Reproduce the analysis pipeline

```bash
cd scripts
pip install pandas numpy scipy scikit-learn xgboost joblib

python extract_data.py          # NASA .mat -> clean battery cycle table
python train_soh_model.py       # XGBoost model with B0018 held out
python rul_and_physics.py       # Physics-based fade model and related outputs
python cross_fidelity.py        # Gap metrics and reliability scoring
python phaseE_calibration.py    # Uncertainty calibration checks
python phaseF_rul_fixed.py      # Corrected RUL flow with EOL handling
```

> The raw NASA `.mat` files are not bundled in this repository because they are large. The included CSV outputs in `data/` are sufficient for downstream reproducibility and evaluation.

## Verified findings

These are the main results and are reported transparently rather than optimized away.

1. AI SoH performance on the fully held-out battery is strong and reproducible: MAE ≈ 1.86% and R² ≈ 0.92.
2. The physics-lite model is materially weaker, with MAE ≈ 5.12%, and it failed to converge on a usable end-of-life prediction for B0018.
3. Uncertainty calibration was poor in the baseline model: naive residual standard deviation intervals achieved only 6.1% empirical coverage against an 80% target. Split-conformal calibration improved this to 18.9%, which still indicates that interval widening alone is insufficient under domain shift.
4. The most important safety-relevant result is a late-life bias: the AI model systematically overestimates SoH in the final real cycles, reporting the battery above the EOL threshold even after it had permanently crossed EOL in real data.
5. Real capacity recovery effects are visible in the B0018 trajectory, confirming that a naive first-crossing EOL definition is not robust; the project corrected this to a permanent-crossing definition.

## Project scope and disclosures

The current MVP is intentionally scoped and simplified compared with the full design specification. Important transparency notes include:

- SoC estimation is partial and uses cycle-level Coulomb counting summaries rather than a full continuous EKF implementation.
- The physics reference is an empirical exponential fade model, not a full ECM simulator.
- Data persistence uses local CSV/JSON files instead of a full database layer.
- Incomplete-data stress testing and more advanced cross-dataset validation are deferred to later phases.
- SHAP explainability, optimizer-based recommendation logic, and broader domain adaptation are planned future work rather than complete current features.

## Recommended use

This repository is best used as a transparent technical prototype for:

- battery health assessment workflows
- reliability-aware model evaluation under domain shift
- end-of-life risk detection and monitoring dashboards
- communicating trade-offs between AI and physics-based methods

## Notes for repository readiness

This project is structured for a clean Git push and collaborative review. Before making the repository public, it is recommended to add:

- an explicit license file
- a `.gitignore` for local environment artifacts
- a short contributor guide if collaboration is intended
- optional CI checks for backend/frontend validation

## Summary

BATTWIN Verify demonstrates a realistic path from raw battery measurements to AI/physics decision support, while keeping the model limitations visible. That transparency is the key value of the project: it shows where the system is useful, where it fails, and how reliability-aware monitoring can catch late-life risk before it becomes a hidden operational issue.
