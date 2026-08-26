"""
Orchestration script: runs the entire pipeline end-to-end to generate
all CSVs, JSON summaries, domain shift metrics, and model files.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
sys.path.insert(0, SCRIPTS_DIR)

print("=== Running BATTWIN-VERIFY Full Pipeline ===")

print("\n1. Data extraction...")
import extract_data

print("\n2. SOH Model Training & Prediction...")
import train_soh_model

print("\n3. Physics Reference Model...")
import rul_and_physics

print("\n4. Cross-Fidelity & Reliability Metrics...")
import cross_fidelity

print("\n5. Standalone Domain-Shift Detection...")
import domain_shift_detector
domain_shift_detector.generate_all_domain_shift_summaries()

print("\n6. Split-Conformal Uncertainty Calibration...")
import phaseE_calibration

print("\n7. RUL Layer with Permanent EOL Crossing...")
import phaseF_rul_fixed

print("\n8. Phase 2: CALCE Cross-Dataset Domain Shift & Residual Adaptation...")
import cross_dataset_domain_shift
cross_dataset_domain_shift.run_cross_dataset_domain_shift()

print("\n9. Phase 2: SHAP Feature Attribution Explainability...")
import explainability_shap
explainability_shap.generate_shap_explainability()

print("\n10. Phase 2: 2-RC Equivalent Circuit Model (ECM) Simulation...")
import ecm_physics_sim
ecm_physics_sim.simulate_2rc_ecm_for_battery()

print("\n11. Phase 2: Experiment C Sensor Packet Drop Stress Test...")
import data_masking_experiment
data_masking_experiment.run_data_masking_experiment()

print("\n12. Generating Frontend Dashboard Payload...")
import generate_dashboard_payload

print("\n=== PIPELINE RUN COMPLETE: All data artifacts & Phase 2 modules updated cleanly ===")