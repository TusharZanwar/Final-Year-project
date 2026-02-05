# agents/analyzer_agent.py
import os
import json


class AnalyzerAgent:
    """
    Reads clinic_db.json to compute risk, robustness,
    and produce an explainable textual report.
    """

    def __init__(self, clinic_db_path="clinic_db.json"):
        self.clinic_db_path = clinic_db_path

    def _load(self):
        with open(self.clinic_db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # =========================
    # NEW: Explainable Risk Breakdown
    # =========================
    def compute_risk_components(self, recall, avg_latency, caretaker_match):
        recall_risk = max(0, (3 - recall) / 3) if recall is not None else 1
        latency_risk = min(avg_latency / 6, 1.0) if avg_latency else 0
        caretaker_risk = 0 if caretaker_match else 1

        total = recall_risk + latency_risk + caretaker_risk
        if total == 0:
            return {
                "MMSE Recall": 0,
                "Response Latency": 0,
                "Caretaker Validation": 0
            }

        return {
            "MMSE Recall": round((recall_risk / total) * 100, 2),
            "Response Latency": round((latency_risk / total) * 100, 2),
            "Caretaker Validation": round((caretaker_risk / total) * 100, 2)
        }

    # =========================
    # NEW: Consistency / Robustness
    # =========================
    def compute_consistency(self, mmse_history):
        if len(mmse_history) < 2:
            return "INSUFFICIENT DATA", None

        diffs = []
        for i in range(1, len(mmse_history)):
            prev = mmse_history[i - 1]["recall_count"]
            curr = mmse_history[i]["recall_count"]
            diffs.append(abs(curr - prev))

        avg_diff = sum(diffs) / len(diffs)

        if avg_diff <= 1:
            return "HIGH", round(avg_diff, 2)
        elif avg_diff <= 2:
            return "MODERATE", round(avg_diff, 2)
        else:
            return "LOW", round(avg_diff, 2)

    # =========================
    # NEW: Failure Mode Detection
    # =========================
    def detect_failure_modes(self, avg_latency, recall):
        flags = []

        if avg_latency is not None and avg_latency < 0.5:
            flags.append("Unrealistically fast responses")

        if avg_latency is not None and avg_latency > 8:
            flags.append("Very slow response latency")

        if recall == 0:
            flags.append("Complete recall failure")

        if not flags:
            return "No reliability issues detected."

        return " | ".join(flags)

    # =========================
    # MAIN REPORT GENERATION
    # =========================
    def generate_patient_report(self, patient_id):
        clinic = self._load()
        patient_meta = clinic.get("patients", {}).get(patient_id, {})
        mmse_history = clinic.get("mmse_scores", {}).get(patient_id, [])

        latest_mmse = mmse_history[-1] if mmse_history else None
        # Use latest MMSE entry if available, else fallback to patient metadata
        if latest_mmse:
            recall = latest_mmse.get("recall_count")
            avg_latency = latest_mmse.get("avg_latency")
        else:
            recall = patient_meta.get("last_mmse_recall")
            avg_latency = patient_meta.get("last_mmse_avg_latency", 0)

        caretaker_match = patient_meta.get("validation", {}).get("breakfast_match", True)

        # -------------------------
        # Risk scoring (existing logic)
        # -------------------------
        score = 0
        reasons = []

        if recall is None:
            reasons.append("No MMSE data available.")
        else:
            if recall < 1:
                score += 70
                reasons.append(f"Very low recall performance: {recall}/3")
            elif recall < 3:
                score += 30
                reasons.append(f"Partial recall: {recall}/3")
            else:
                reasons.append("Recall performance within normal limits.")

        if avg_latency and avg_latency > 5:
            score += 30
            reasons.append(f"High response latency: {avg_latency}s")

        if caretaker_match is False:
            score += 20
            reasons.append("Mismatch with caretaker-provided ground truth.")
        else:
            reasons.append("Caretaker validation matched.")

        # -------------------------
        # Interpretation
        # -------------------------
        if score >= 80:
            stage = "SEVERE_IMPAIRMENT_SUSPECTED"
            risk = "HIGH"
        elif score >= 40:
            stage = "MILD COGNITIVE IMPAIRMENT (MCI)"
            risk = "MEDIUM"
        else:
            stage = "NORMAL COGNITION"
            risk = "LOW"

        # -------------------------
        # NEW ANALYTICS
        # -------------------------
        risk_components = self.compute_risk_components(
            recall, avg_latency, caretaker_match
        )

        reliability, variance = self.compute_consistency(mmse_history)
        failure_flags = self.detect_failure_modes(avg_latency, recall)

        report = {
            "patient_id": patient_id,
            "stage": stage,
            "risk": risk,
            "score": score,
            "reasons": reasons,
            "risk_breakdown": risk_components,
            "consistency": {
                "reliability": reliability,
                "variance": variance
            },
            "reliability_warnings": failure_flags,
            "mmse_latest": latest_mmse
        }

        clinic.setdefault("reports", {})[patient_id] = report
        with open(self.clinic_db_path, "w", encoding="utf-8") as f:
            json.dump(clinic, f, indent=2)

        # -------------------------
        # HUMAN-READABLE REPORT
        # -------------------------
        lines = []
        lines.append("========== AI ANALYZER REPORT ==========")
        lines.append(f"Patient ID: {patient_id}")
        lines.append(f"Stage: {stage}")
        lines.append(f"Risk Level: {risk}")
        lines.append(f"Risk Score: {score}")
        lines.append("\nPrimary Reasons:")
        for r in reasons:
            lines.append(f" - {r}")

        lines.append("\nRisk Contribution Breakdown:")
        for k, v in risk_components.items():
            lines.append(f" - {k}: {v}%")

        lines.append("\nConsistency Analysis:")
        lines.append(f" - Reliability: {reliability}")
        if variance is not None:
            lines.append(f" - Test-Retest Variance: {variance}")

        lines.append("\nAssessment Reliability Flags:")
        lines.append(f" - {failure_flags}")

        lines.append("========================================")
        return "\n".join(lines)