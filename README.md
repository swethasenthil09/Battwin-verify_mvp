# BATTWIN Verify

> Reliability-aware battery intelligence for BESS monitoring, health estimation, and end-of-life decision support.

**Built for:** P5 — Smart Battery Energy Storage Management & RUL Prediction

BATTWIN Verify evaluates real NASA PCoE battery degradation data through an end-to-end workflow covering data extraction, State of Health (SoH) prediction, physics-based comparison, reliability scoring, Remaining Useful Life (RUL) analysis, and interactive visual analytics.

The project focuses not only on model accuracy, but also on identifying model limitations, uncertainty, domain shift, and late-life prediction failures.

---

## Why BATTWIN Verify?

Battery health prediction models can appear accurate overall while still producing unreliable predictions during critical late-life operation.

BATTWIN Verify is designed as a transparent decision-support prototype that evaluates:

- How accurately battery health can be predicted
- Where prediction models fail
- Whether predictions remain reliable under domain shift
- How AI predictions compare with a physics-based reference
- Whether reliability-aware monitoring can detect unsafe late-life behavior

Rather than hiding weak results, the system explicitly reports them as part of the evaluation.

---

## Key Features

-  Real NASA PCoE battery aging data
-  AI-based State of Health (SoH) estimation using XGBoost
-  Physics-based capacity fade comparison
-  Remaining Useful Life (RUL) analysis
-  Reliability scoring for prediction quality assessment
-  Detection of unsafe late-life prediction drift
-  FastAPI backend for battery diagnostics and recommendations
-  React dashboard for interactive analysis and visualization
-  Reproducible end-to-end data analysis pipeline

---

##  System Architecture

            NASA Battery Data
                   │
                   ▼
          Data Extraction & Processing
                    │
                    ▼
          Cycle-Level Feature Generation
                    │
        ├───────────────────────┐
        ▼                       ▼
    XGBoost SoH Model      Physics-Based Fade Model
        │                       │
        └───────────┬───────────┘
                    ▼
          Reliability Analysis
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        SoH        RUL    Risk Detection
                    │
                    ▼
              FastAPI Backend
                    │
                    ▼
             React Dashboard


---

##  Technical Approach

### Data Source

The project uses the NASA Ames PCoE Li-ion Battery Aging Dataset, including real battery degradation measurements and cycle-level capacity data.

### Validation Strategy

Instead of randomly splitting cycle records, the model uses battery-level holdout validation.

- Training batteries are used for model development.
- Battery B0018 is held out for evaluation.

This provides a more realistic evaluation of how the model performs on an unseen battery.

### AI-Based SoH Estimation

An XGBoost Regressor predicts battery State of Health (SoH) using cycle-level summary features extracted from battery degradation data.

### Physics-Based Reference

An empirical exponential capacity-fade model is fitted using early-cycle battery behavior and used as a reference for comparison.

### Reliability Analysis

A composite reliability workflow evaluates factors including:

- Data completeness
- Agreement between model outputs
- Prediction fidelity
- Uncertainty behavior

This helps identify situations where a prediction may appear valid but is potentially unreliable.

---

##  Verified Findings

The project intentionally reports both successful and weak results.

### 1. Strong AI-Based SoH Prediction

On the fully held-out battery:

- **MAE:** ≈ 1.86%
- **R²:** ≈ 0.92

### 2. Physics Reference Limitations

The empirical physics-based model performed less effectively:

- **MAE:** ≈ 5.12%
- Did not converge to a reliable end-of-life prediction for B0018.

### 3. Uncertainty Calibration Challenges

The baseline uncertainty approach achieved:

- **6.1% empirical coverage** against an **80% target**

Split-conformal calibration improved coverage to:

- **18.9%**

However, the results still indicate that uncertainty calibration remains challenging under domain shift.

### 4. Late-Life Prediction Bias

The AI model showed systematic late-life bias by **overestimating SoH near the end of the battery lifecycle**.

This resulted in the model reporting the battery above the End-of-Life threshold even after the real battery data had permanently crossed that threshold.

### 5. Capacity Recovery Effects

Real capacity recovery effects were observed in the B0018 trajectory.

Because of this, a simple first-crossing End-of-Life definition was not considered reliable. The workflow was updated to use a **permanent-crossing EOL definition**.


---

##  Repository Structure

BATTWIN-Verify/
│
├── data/          # Extracted NASA cycle data and computed outputs
├── backend/       # FastAPI backend and prediction endpoints
├── frontend/      # Vite + React dashboard
├── scripts/       # Reproducible analysis pipeline
├── docs/          # Design notes and supporting documentation
└── README.md

---

##  Tech Stack

| Layer | Technologies |
|---|---|
| Data Processing | Python, Pandas, NumPy |
| Machine Learning | XGBoost, Scikit-learn |
| Scientific Computing | SciPy |
| Backend | FastAPI |
| Frontend | React, Vite |
| Data Storage | CSV, JSON |
| Dataset | NASA PCoE Battery Dataset |

---

##  Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm

### 1. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```
### 2. Run the backend
```bash
cd backend
pip install fastapi uvicorn pandas
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Available API Endpoints
GET  /api/batteries
GET  /api/battery/B0018/analysis
GET  /api/battery/B0018/reliability
GET  /api/battery/B0018/rul
GET  /api/battery/B0018/recommendation
POST /api/predict

### 3. Reproduce the Analysis Pipeline
cd scripts

pip install pandas numpy scipy scikit-learn xgboost joblib

python extract_data.py
python train_soh_model.py
python rul_and_physics.py
python cross_fidelity.py
python phaseE_calibration.py
python phaseF_rul_fixed.py

---

##  Current Scope and Limitations

BATTWIN Verify is currently an MVP and intentionally keeps several components simplified.

- SoC estimation uses cycle-level Coulomb counting summaries rather than a continuous EKF implementation.
- The physics reference is an empirical exponential fade model rather than a complete ECM simulator.
- Data persistence currently uses local CSV and JSON files.
- Advanced cross-dataset validation is deferred to future work.
- Incomplete-data stress testing is not yet implemented.

The following features are planned but not currently complete:

- SHAP-based model explainability
- Optimizer-based recommendation logic
- Advanced domain adaptation
- Database integration
- Broader battery dataset evaluation


---

##  Recommended Use Cases

BATTWIN Verify is designed as a technical prototype for:

- Battery health assessment
- State of Health (SoH) prediction
- Remaining Useful Life (RUL) analysis
- Reliability-aware machine learning evaluation
- End-of-life risk detection
- Battery monitoring and diagnostics
- AI and physics-based model comparison

---

##  Future Improvements

- Support additional battery datasets
- Improve cross-dataset validation
- Add SHAP-based model explainability
- Implement advanced uncertainty estimation
- Add database persistence
- Introduce optimizer-based battery recommendations
- Improve domain adaptation across battery types
- Add automated testing and CI workflows

---

##  Project Focus

The primary contribution of BATTWIN Verify is not simply achieving high prediction accuracy.

The system is designed to answer a more practical question:

> **When should a battery health prediction be trusted?**

By combining AI-based prediction, physics-based comparison, uncertainty analysis, and reliability scoring, the project makes model limitations visible instead of treating accuracy as the only measure of success.

---

## Dataset Reference

NASA Ames Prognostics Center of Excellence (PCoE)  
Li-ion Battery Aging Dataset  
Saha & Goebel, 2007

---

##  License

This project is currently intended as an academic and research prototype. A license file will be added before public release.
