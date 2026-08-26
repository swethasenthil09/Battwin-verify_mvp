"""
Phase H: Degradation-aware charge/discharge recommendation.

This is DELIBERATELY rule-based, not a trained model -- it consumes the
already-validated (or flagged-unreliable) SoH/reliability outputs from the
upstream pipeline and applies explicit, auditable constraints. No black box
here: every recommendation traces to a stated rule.
"""

def recommend(soh_pct: float, temperature_c: float, reliability_score: float,
              ai_physics_disagreement_pct: float) -> dict:
    reasons = []
    max_charge_rate_c = 1.0  # baseline 1C
    max_discharge_rate_c = 1.0
    action = "normal"

    if reliability_score < 60:
        max_charge_rate_c = 0.3
        max_discharge_rate_c = 0.5
        action = "conservative"
        reasons.append(
            f"Reliability score {reliability_score:.0f}/100 is low -- predictions "
            f"are not well-verified against physics/uncertainty checks, so operating "
            f"limits are tightened as a precaution."
        )
    elif reliability_score < 80:
        max_charge_rate_c = 0.6
        max_discharge_rate_c = 0.8
        action = "cautious"
        reasons.append(
            f"Reliability score {reliability_score:.0f}/100 is moderate -- charge rate "
            f"reduced pending additional verification."
        )

    if temperature_c > 40:
        max_charge_rate_c = min(max_charge_rate_c, 0.3)
        action = "conservative"
        reasons.append(f"Elevated temperature ({temperature_c:.1f}C) increases degradation risk at high C-rate.")

    if soh_pct < 75:
        max_discharge_rate_c = min(max_discharge_rate_c, 0.7)
        reasons.append(f"SoH {soh_pct:.1f}% is approaching end-of-life threshold (70%) -- discharge rate capped to reduce further stress.")

    if ai_physics_disagreement_pct > 4:
        action = "conservative"
        reasons.append(
            f"AI and physics models disagree by {ai_physics_disagreement_pct:.1f}% SoH -- "
            f"treat the point prediction as unverified and default to the conservative policy "
            f"until the gap is investigated."
        )

    if not reasons:
        reasons.append("All checks nominal -- normal operating policy applies.")

    return {
        "action": action,
        "max_charge_rate_C": round(max_charge_rate_c, 2),
        "max_discharge_rate_C": round(max_discharge_rate_c, 2),
        "reasons": reasons,
    }