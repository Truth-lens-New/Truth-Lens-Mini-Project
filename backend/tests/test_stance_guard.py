"""
Tests for the comparative entity-swap guardrail in StanceDetector.

Regression test for the Phobos/Deimos miss: claim "Deimos is the larger one"
with evidence "Phobos is the larger of Mars' two moons" was voted SUPPORTS by
zero-shot NLI, so the guardrail must shift support to refute when the claim and
the evidence attribute the same superlative to different entities.

Runs shell-isolated: no spaCy/transformers/model downloads. detect() is exercised
with a fake classifier that always votes SUPPORT heavily (the BART failure mode),
so any SUPPORTS result for a swap case means the guardrail failed.
"""

import sys
import types

import pytest

from tests.import_utils import isolated_imports


class _SupportHeavyClassifier:
    """Fake zero-shot classifier: always votes 'true' (SUPPORT) at 0.9."""

    def __call__(self, evidence_text, candidate_labels, hypothesis_template=None, multi_label=False):
        scores = {label: 0.0333 for label in candidate_labels}
        scores["true"] = 0.9
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return {"labels": [label for label, _ in ordered], "scores": [s for _, s in ordered]}


def _load_stance_detector():
    """Import the real stance_detector with a stubbed model_manager."""
    with isolated_imports(packages=("app", "app.services", "app.services.investigation", "app.services.models")):
        stub = types.ModuleType("app.services.models.model_manager")
        stub.get_model_manager = lambda: types.SimpleNamespace(
            unified_model=_SupportHeavyClassifier()
        )
        sys.modules["app.services.models.model_manager"] = stub
        module = __import__(
            "app.services.investigation.stance_detector",
            fromlist=["StanceDetector"],
        )
        detector = module.StanceDetector()
        return module.StanceDetector, detector


@pytest.fixture(scope="module")
def stance_cls():
    StanceDetector, _ = _load_stance_detector()
    return StanceDetector


@pytest.fixture(scope="module")
def detector():
    _, instance = _load_stance_detector()
    return instance


class TestComparativeEntities:
    def test_simple_claim(self, stance_cls):
        assert stance_cls._comparative_entities("Deimos is the larger one.") == {"deimos"}

    def test_compound_claim_extracts_last_subject(self, stance_cls):
        # Only the clause immediately holding the superlative counts.
        ents = stance_cls._comparative_entities(
            "Phobos and Deimos, and Deimos is the larger one."
        )
        assert ents == {"deimos"}

    def test_evidence_subject(self, stance_cls):
        ents = stance_cls._comparative_entities(
            "Phobos is the larger of Mars' two moons."
        )
        assert ents == {"phobos"}

    def test_pronoun_subjects_skipped(self, stance_cls):
        assert stance_cls._comparative_entities("It is the larger one.") == set()
        assert stance_cls._comparative_entities("That is the tallest peak.") == set()

    def test_no_comparative(self, stance_cls):
        assert stance_cls._comparative_entities("Mars has two moons.") == set()

    def test_case_insensitive(self, stance_cls):
        assert stance_cls._comparative_entities("The CN TOWER is the Tallest.") == {"tower"}


class TestComparativeSwap:
    def test_live_phobos_deimos_case(self, stance_cls):
        claim = "Phobos and Deimos, and Deimos is the larger one."
        evidence = "Phobos is the larger of Mars' two moons."
        assert stance_cls._comparative_swap(claim, evidence) is True

    def test_same_entity_no_swap(self, stance_cls):
        claim = "The Eiffel Tower is the tallest structure in Paris."
        evidence = "The Eiffel Tower is the tallest man-made structure in the city."
        assert stance_cls._comparative_swap(claim, evidence) is False

    def test_no_comparative_in_claim(self, stance_cls):
        assert stance_cls._comparative_swap(
            "Mars has two moons.", "Phobos is the larger of Mars' two moons."
        ) is False

    def test_no_comparative_in_evidence(self, stance_cls):
        assert stance_cls._comparative_swap(
            "Deimos is the larger one.", "Mars has exactly two moons."
        ) is False

    def test_pronoun_only_subjects_no_swap(self, stance_cls):
        assert stance_cls._comparative_swap(
            "It is the larger one.", "That is the bigger of the two."
        ) is False


class TestDetectGuardrail:
    CLAIM = "Phobos and Deimos, and Deimos is the larger one."
    EVIDENCE = "Phobos is the larger of Mars' two moons, discovered in 1877."

    def test_entity_swap_squashes_support(self, detector):
        # Even though the fake classifier votes SUPPORT at 0.9, the swap
        # guardrail must flip the label to REFUTES.
        result = detector.detect(self.CLAIM, self.EVIDENCE)
        assert result["label"] == "REFUTES"

    def test_matching_entity_keeps_normal_flow(self, detector):
        evidence = "Phobos is the larger of Mars' two moons. Deimos is not larger."
        claim = "Phobos is the larger of the two moons."
        # Same subject entity -> guardrail must NOT fire, support-heavy vote stands.
        result = detector.detect(claim, evidence)
        assert result["label"] == "SUPPORTS"

    def test_swap_refutes_across_swap_direction(self, detector):
        # Claim credits Phobos, evidence credits Deimos: symmetric case.
        result = detector.detect(
            "Phobos is the larger one.", "Deimos is the larger of Mars' two moons."
        )
        assert result["label"] == "REFUTES"
