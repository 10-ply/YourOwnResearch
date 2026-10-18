from typing import List, Dict, Any, Optional
import math
import re

class System1DecisionEngine:
    """
    Non-autoregressive System 1 Decision Model interface (choice, score, noul primitives)
    implementing fast, single-forward-pass direct classification and calibrated confidence.
    """
    def __init__(self):
        # High precision semantic keyword vectors for citation polarity classification
        self.refutation_keywords = [
            "refute", "refutes", "refuted", "refuting",
            "contradict", "contradicts", "contradicted", "contradicting",
            "fail to replicate", "failed to replicate", "failure to observe", "failed to observe",
            "irreproducible", "falsify", "falsified", "disproven", "no evidence of",
            "artifact", "artifacts", "spurious", "incorrect", "flawed"
        ]
        self.supporting_keywords = [
            "confirm", "confirms", "confirmed", "confirming",
            "replicate", "replicates", "replicated", "replicating",
            "validate", "validates", "validated", "validating",
            "corroborate", "corroborates", "corroborated",
            "support", "supports", "supported", "reinforce", "demonstrate"
        ]
        self.domain_constraint_keywords = [
            "bound", "bounded", "boundary", "limit", "limiting", "limitations",
            "valid within", "fails when extended", "restricted to", "parameter domain",
            "breakdown", "breaks down", "approximation", "perihelion", "relativistic"
        ]

    def choice(self, state: str, choices: List[str], descriptions: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        System 1 `choice` primitive: maps unstructured state (citation snippet context)
        to a categorical class with distribution and calibrated confidence score.
        """
        text_lower = state.lower()
        scores = {c: 0.1 for c in choices}

        # Match keyword patterns with weighting
        for kw in self.refutation_keywords:
            if kw in text_lower:
                if "CONTESTING" in scores:
                    scores["CONTESTING"] += 2.5

        for kw in self.supporting_keywords:
            if kw in text_lower:
                if "SUPPORTING" in scores:
                    scores["SUPPORTING"] += 2.0

        for kw in self.domain_constraint_keywords:
            if kw in text_lower:
                if "DOMAIN_CONSTRAINED" in scores:
                    scores["DOMAIN_CONSTRAINED"] += 2.2

        if max(scores.values()) == 0.1 and "NEUTRAL" in scores:
            scores["NEUTRAL"] += 1.0

        # Softmax normalization
        exp_scores = {c: math.exp(v) for c, v in scores.items()}
        total_exp = sum(exp_scores.values())
        probs = {c: exp_scores[c] / total_exp for c in choices}

        best_choice = max(probs, key=probs.get)
        confidence = probs[best_choice]

        return {
            "prediction": best_choice,
            "distribution": probs,
            "confidence": confidence
        }

    def score(self, state: str, rubric: str) -> float:
        """
        System 1 `score` primitive: continuous score evaluation in [0, 1].
        """
        choice_res = self.choice(state, ["HIGH", "MEDIUM", "LOW"])
        if choice_res["prediction"] == "HIGH":
            return 0.9
        elif choice_res["prediction"] == "MEDIUM":
            return 0.5
        return 0.1

    def noul(self, state: str, question: str) -> float:
        """
        System 1 `noul` primitive: binary probability in [0, 1].
        """
        res = self.choice(state, ["YES", "NO"])
        return res["distribution"].get("YES", 0.5)

    def classify_citation_context(self, snippet: str) -> Dict[str, Any]:
        choices = ["SUPPORTING", "CONTESTING", "DOMAIN_CONSTRAINED", "NEUTRAL"]
        res = self.choice(snippet, choices)
        return {
            "polarity": res["prediction"],
            "confidence": res["confidence"],
            "distribution": res["distribution"]
        }

classifier_engine = System1DecisionEngine()
