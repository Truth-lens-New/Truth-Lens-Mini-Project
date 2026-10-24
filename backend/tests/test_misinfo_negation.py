"""
Regression tests: a known-misinformation pattern must NOT label an explicitly
negated version of the claim as false.
"""

import json

import pytest

from import_utils import isolated_imports


@pytest.fixture(scope="module")
def checker_cls():
    with isolated_imports(["app", "app.services", "app.services.evidence"]) as imp:
        mod = imp("app.services.evidence.known_misinfo_checker")
        yield mod.KnownMisinfoChecker


@pytest.fixture()
def db_file(tmp_path):
    data = {
        "vaccines_autism": {
            "patterns": ["vaccine", "autism", "cause"],
            "verdict": "VERIFIED_FALSE",
            "confidence": 0.99,
            "reason": "Debunked repeatedly.",
            "sources": ["CDC"],
        },
        "climate_change_not_real": {
            # Stored pattern itself contains a negation.
            "patterns": ["climate change", "not real"],
            "verdict": "VERIFIED_FALSE",
            "confidence": 0.98,
            "reason": "Climate change is real.",
            "sources": ["IPCC"],
        },
    }
    path = tmp_path / "known_misinformation.json"
    path.write_text(json.dumps(data))
    return str(path)


@pytest.fixture()
def checker(checker_cls, db_file):
    return checker_cls(db_path=db_file)


class TestNegationGuard:
    def test_positive_falsehood_is_matched(self, checker):
        result = checker.check("Vaccines cause autism")
        assert result is not None
        assert result.verdict == "VERIFIED_FALSE"

    def test_negated_claim_is_not_labelled_false(self, checker):
        assert checker.check("Vaccines do not cause autism") is None

    def test_negated_claim_uppercase_variation(self, checker):
        assert checker.check("Vaccines DO NOT cause autism") is None

    def test_contraction_negation_is_not_labelled_false(self, checker):
        assert checker.check("Vaccines don't cause autism") is None

    def test_negated_claim_falls_through_to_normal_pipeline(self, checker, checker_cls):
        """No falsy verdict may be produced for a negated form of the myth."""
        for claim in (
            "Vaccines do not cause autism",
            "Vaccines never caused autism",
            "Vaccines cannot cause autism",
        ):
            assert checker.check(claim) is None, f"ranked as known-misinfo: {claim}"

    def test_pattern_containing_negation_still_matches(self, checker):
        """A claim that legitimately includes the DB's own negated pattern."""
        result = checker.check("Climate change is not real")
        assert result is not None
        assert result.verdict == "VERIFIED_FALSE"

    def test_unrelated_claim_is_not_matched(self, checker):
        assert checker.check("The sun is 93 million miles away") is None
