"""Core decision simulation and counterfactual risk engine for LAWSEER."""
from typing import Dict, Any

class LegalRiskEngine:
    def __init__(self, case_facts: Dict[str, Any]):
        self.facts = case_facts

    def evaluate_notice_decision(self, send_notice: bool) -> Dict[str, Any]:
        # Safely parse numeric inputs to prevent empty string crashes
        try:
            dispute_amount = float(self.facts.get("claim_amount") or 0)
        except (ValueError, TypeError):
            dispute_amount = 0.0

        try:
            breach_age_days = int(self.facts.get("breach_age_days") or 0)
        except (ValueError, TypeError):
            breach_age_days = 0

        has_clear_liability = bool(self.facts.get("written_contract", False))

        if send_notice:
            resolution_prob = 0.72 if has_clear_liability else 0.45
            litigation_risk = "MODERATE" if breach_age_days < 90 else "HIGH"
            estimated_turnaround_days = 15
            primary_consequence = (
                "Formal legal timeline activated. Opposing party mandated to cure or respond within 15 days."
            )
            branch_key = "NOTICE_ISSUED"
        else:
            resolution_prob = 0.18
            litigation_risk = "CRITICAL"
            estimated_turnaround_days = 90
            primary_consequence = (
                "Forfeiture of statutory pre-action leverage. Cause of action may suffer limitation challenges."
            )
            branch_key = "NOTICE_WITHHELD"

        counterfactual_delta = {
            "resolution_probability_delta": "+54%" if send_notice else "-54%",
            "cost_exposure": f"${dispute_amount * 0.05:,.2f}" if send_notice else f"${dispute_amount * 0.35:,.2f}",
        }

        return {
            "branch": branch_key,
            "send_notice": send_notice,
            "resolution_probability": resolution_prob,
            "litigation_risk": litigation_risk,
            "turnaround_days": estimated_turnaround_days,
            "primary_consequence": primary_consequence,
            "delta": counterfactual_delta,
            "evidence_safety_score": 94 if has_clear_liability else 62
        }

    def run_full_comparison(self) -> Dict[str, Any]:
        return {
            "notice_yes": self.evaluate_notice_decision(send_notice=True),
            "notice_no": self.evaluate_notice_decision(send_notice=False)
        }