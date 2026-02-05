# agents/analyzer_agent.py
import os
import json
from datetime import datetime

class AnalyzerAgent:
    """
    Reads clinic_db.json and mmse_scores/interactions then produces a simple textual report.
    """

    def __init__(self, clinic_db_path="clinic_db.json"):
        self.path = clinic_db_path
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({"patients": {}, "interactions": {}, "mmse_scores": {}, "reports": {}}, f, indent=2)

    def _read_db(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def generate_patient_report(self, patient_id):
        db = self._read_db()
        patient = db.get("patients", {}).get(patient_id, {})
        mmse_list = db.get("mmse_scores", {}).get(patient_id, [])
        interactions = db.get("interactions", {}).get(patient_id, [])

        # compute latest MMSE
        latest_mmse = mmse_list[-1] if mmse_list else None
        recall = latest_mmse.get("recall_score") if latest_mmse else None

        # basic scoring logic:
        risk = 0
        reasons = []

        # Latency: use last mmse latency if available
        latency = latest_mmse.get("latency") if latest_mmse else None
        if latency and latency > 3.0:
            risk += 25
            reasons.append(f"High response latency ({latency}s).")

        # Recall score
        if recall is not None:
            if recall >= 3:
                reasons.append(f"MMSE recall perfect ({recall}/3).")
            elif recall == 2:
                risk += 10
                reasons.append("MMSE recall mild impairment (2/3).")
            elif recall == 1:
                risk += 25
                reasons.append("MMSE recall moderate impairment (1/3).")
            elif recall == 0:
                risk += 40
                reasons.append("MMSE recall severe impairment (0/3).")
        else:
            reasons.append("No MMSE record found.")

        # confabulations / caregiver mismatch count (if any interactions stored)
        confab_count = 0
        for log in interactions:
            if log.get("type") == "nurse_caretaker":
                # if caretaker truth stored vs nurse logged patient answers — simplistic
                if log.get("discrepancy", False):
                    confab_count += 1
        if confab_count:
            risk += confab_count * 15
            reasons.append(f"{confab_count} discrepancies between patient answers and caregiver ground truth.")

        # final judgment
        if risk >= 60:
            stage = "SEVERE IMPAIRMENT SUSPECTED"
            level = "HIGH"
        elif risk >= 30:
            stage = "MILD COGNITIVE IMPAIRMENT (MCI) POSSIBLE"
            level = "MEDIUM"
        else:
            stage = "LIKELY NORMAL COGNITION"
            level = "LOW"

        report = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "patient": patient.get("PatientName", patient_id),
            "stage": stage,
            "risk_level": level,
            "risk_score": risk,
            "reasons": reasons,
            "latest_mmse": latest_mmse
        }

        # persist into DB
        db.setdefault("reports", {})
        db["reports"][patient_id] = report
        with open(self.path, "w") as f:
            json.dump(db, f, indent=2)

        # present a readable plain-text report
        out = []
        out.append("========== AI ANALYZER REPORT ==========")
        out.append(f"Patient: {report['patient']}")
        out.append(f"Generated: {report['generated_at']}")
        out.append(f"Stage: {report['stage']}")
        out.append(f"Risk Level: {report['risk_level']} (score={report['risk_score']})")
        out.append("Reasons:")
        for r in report["reasons"]:
            out.append(" - " + r)
        out.append("========================================")
        return "\n".join(out)
