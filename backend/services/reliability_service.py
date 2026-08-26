"""
Reliability Score & Component Rating Service.

Exposes component-level ratings, warnings, and overall status tags to make
reliability scoring transparent and explainable.
"""
import numpy as np

WEIGHTS = {
    "data_completeness": 0.15,
    "domain_similarity": 0.15,
    "ai_agreement": 0.25,
    "sim_fidelity": 0.20,
    "cross_model_agreement": 0.10,
    "uncertainty_quality": 0.15,
}

def rate_component(val: float, is_uncertainty: bool = False) -> dict:
    pct = round(val * 100.0)
    if is_uncertainty:
        if val >= 0.70:
            return {"rating": "Good", "status": "✓ Good Coverage", "badge": "good"}
        elif val >= 0.40:
            return {"rating": "Moderate", "status": "⚠ Fair Coverage", "badge": "warn"}
        else:
            return {"rating": "Poor", "status": "⚠ Needs Improvement", "badge": "bad"}
    else:
        if val >= 0.90:
            return {"rating": "Excellent", "status": "✓ Excellent", "badge": "good"}
        elif val >= 0.75:
            return {"rating": "Good", "status": "✓ Strong", "badge": "good"}
        elif val >= 0.50:
            return {"rating": "Moderate", "status": "⚠ Moderate", "badge": "warn"}
        else:
            return {"rating": "Poor", "status": "⚠ Poor", "badge": "bad"}

def compute_composite_reliability(
    data_completeness: float,
    domain_similarity: float,
    ai_agreement: float,
    sim_fidelity: float,
    cross_model_agreement: float,
    uncertainty_coverage_before: float,
    uncertainty_coverage_after: float
) -> dict:
    # Score calculation BEFORE calibration fix
    unc_score_before = min(uncertainty_coverage_before / 0.80, 1.0)
    score_before = 100.0 * (
        WEIGHTS["data_completeness"] * data_completeness +
        WEIGHTS["domain_similarity"] * domain_similarity +
        WEIGHTS["ai_agreement"] * ai_agreement +
        WEIGHTS["sim_fidelity"] * sim_fidelity +
        WEIGHTS["cross_model_agreement"] * cross_model_agreement +
        WEIGHTS["uncertainty_quality"] * unc_score_before
    )

    # Score calculation AFTER calibration fix
    unc_score_after = min(uncertainty_coverage_after / 0.80, 1.0)
    score_after = 100.0 * (
        WEIGHTS["data_completeness"] * data_completeness +
        WEIGHTS["domain_similarity"] * domain_similarity +
        WEIGHTS["ai_agreement"] * ai_agreement +
        WEIGHTS["sim_fidelity"] * sim_fidelity +
        WEIGHTS["cross_model_agreement"] * cross_model_agreement +
        WEIGHTS["uncertainty_quality"] * unc_score_after
    )

    # Component rating breakdown
    component_ratings = {
        "data_completeness": {
            "score_pct": round(data_completeness * 100.0, 1),
            **rate_component(data_completeness)
        },
        "domain_similarity": {
            "score_pct": round(domain_similarity * 100.0, 1),
            **rate_component(domain_similarity)
        },
        "ai_agreement": {
            "score_pct": round(ai_agreement * 100.0, 1),
            **rate_component(ai_agreement)
        },
        "sim_fidelity": {
            "score_pct": round(sim_fidelity * 100.0, 1),
            **rate_component(sim_fidelity)
        },
        "cross_model_agreement": {
            "score_pct": round(cross_model_agreement * 100.0, 1),
            **rate_component(cross_model_agreement)
        },
        "uncertainty_quality": {
            "score_pct": round(uncertainty_coverage_after * 100.0, 1),
            "target_coverage_pct": 80.0,
            **rate_component(uncertainty_coverage_after, is_uncertainty=True)
        }
    }

    # Status tag
    if score_after >= 85 and uncertainty_coverage_after >= 0.70:
        status_text = "High Confidence"
        reliability_warning = None
    elif score_after >= 60:
        status_text = "Moderate Reliability"
        reliability_warning = "⚠ Uncertainty calibration needs improvement" if uncertainty_coverage_after < 0.50 else "⚠ Verify before acting"
    else:
        status_text = "Low Reliability — Conservative Policy Required"
        reliability_warning = "⚠ Multiple validation checks failed"

    # Cross-Fidelity A/B/C/D Scenario Classification
    if ai_agreement >= 0.85 and sim_fidelity >= 0.75:
        scenario_code = "A"
        scenario_title = "Scenario A: Optimal Digital Twin Alignment"
        scenario_desc = "Both AI model and physical reference model show high agreement with measured battery telemetry. Operational confidence is high."
    elif ai_agreement >= 0.85 and sim_fidelity < 0.75:
        scenario_code = "B"
        scenario_title = "Scenario B: AI Data-Driven Dominance / Physics Degradation Mis-fit"
        scenario_desc = "AI model accurately tracks capacity fade, but physics reference model failed to capture late-life non-linearities. Rely primarily on AI predictions with elevated monitoring."
    elif ai_agreement < 0.85 and sim_fidelity >= 0.75:
        scenario_code = "C"
        scenario_title = "Scenario C: AI Out-of-Domain Flag / Physics Backup Safe"
        scenario_desc = "AI model accuracy degraded due to domain shift or unseen operating regime. Physics reference model remains within bounds -- fallback to physics RUL."
    else:
        scenario_code = "D"
        scenario_title = "Scenario D: High-Risk Anomaly / Conservative Operating Policy Mandatory"
        scenario_desc = "Both AI and physics models show low agreement or significant disagreement. Multi-pillar verification failed -- default to conservative operating limits."

    scenario_info = {
        "code": scenario_code,
        "title": scenario_title,
        "description": scenario_desc
    }

    return {
        "reliability_score": round(score_before, 2),
        "reliability_score_after_calibration": round(score_after, 2),
        "status_text": status_text,
        "reliability_warning": reliability_warning,
        "data_completeness": data_completeness,
        "domain_similarity": domain_similarity,
        "ai_agreement": ai_agreement,
        "sim_fidelity": sim_fidelity,
        "cross_model_agreement": cross_model_agreement,
        "uncertainty_coverage_before": uncertainty_coverage_before,
        "uncertainty_coverage_after": uncertainty_coverage_after,
        "weights": WEIGHTS,
        "component_ratings": component_ratings,
        "scenario": scenario_info
    }