"""
Tests for the shared fact-check rating mapping (app/services/evidence/ratings.py).
Covers the previously broken cases: "not true", "half true", "partly true",
"incorrect", "pants on fire" — plus stance mapping and relevance guarding.
"""

import pytest

from import_utils import isolated_imports


@pytest.fixture(scope="module")
def ratings():
    with isolated_imports(["app", "app.services", "app.models", "app.services.evidence"]) as imp:
        yield imp("app.services.evidence.ratings")


class TestRatingNormalization:
    @pytest.mark.parametrize("rating,expected", [
        # Previously WARN cases in the orchestrator's substring mapping:
        ("not true", "False"),
        ("Not True", "False"),
        ("not correct", "False"),
        ("Half True", "Misleading"),
        ("half true", "Misleading"),
        ("Partly true", "Misleading"),
        ("partly false", "Misleading"),
        ("Incorrect", "False"),
        ("Pants on Fire", "False"),
        ("pants on fire", "False"),
        # Positives:
        ("True", "True"),
        ("TRUE", "True"),
        ("mostly true", "True"),
        ("Correct", "True"),
        # Misleading:
        ("Mixture", "Misleading"),
        ("misleading", "Misleading"),
        ("Out of context", "Misleading"),
        # Unverifiable:
        ("no evidence", "Unverifiable"),
        ("Unproven", "Unverifiable"),
        ("needs context", "Unverifiable"),
    ])
    def test_known_ratings(self, ratings, rating, expected):
        assert ratings.normalize_rating(rating) == expected

    @pytest.mark.parametrize("rating", ["gibberish nonsense", "on fire?", "", None])
    def test_unknown_ratings_return_none(self, ratings, rating):
        assert ratings.normalize_rating(rating) is None

    def test_negation_never_maps_to_true(self, ratings):
        """The core regression: 'not true' contained the substring 'true'."""
        assert ratings.normalize_rating("not true") == "False"
        assert ratings.normalize_rating("it is NOT true") == "False"


class TestStanceMapping:
    def test_true_supports(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("True")
        assert stance == Stance.SUPPORTS and confidence >= 0.9

    def test_false_refutes(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("False")
        assert stance == Stance.REFUTES and confidence >= 0.9

    def test_misleading_is_neutral_not_definitive(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("Misleading")
        assert stance == Stance.NEUTRAL
        assert confidence < 0.9   # must never trigger the early-stop path

    def test_unverifiable_is_neutral(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("Unverifiable")
        assert stance == Stance.NEUTRAL

    def test_none_is_low_confidence_neutral(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating(None)
        assert stance == Stance.NEUTRAL and confidence < 0.9


class TestHedgedRatings:
    """Hedged qualifiers must NOT be definitive (below the 0.9 early-stop gate)."""

    def test_mostly_true_supports_but_not_definitive(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("Mostly True")
        assert stance == Stance.SUPPORTS
        assert 0.7 <= confidence < 0.9

    def test_mostly_false_refutes_but_not_definitive(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("mostly false")
        assert stance == Stance.REFUTES
        assert 0.7 <= confidence < 0.9

    def test_snopes_screen_case(self, ratings):
        """The exact case from live testing: 'Mostly True' at 95% overrode everything."""
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("Mostly True")
        assert confidence < 0.9      # early stop (>= 0.9) must not fire

    def test_flat_true_stays_definitive(self, ratings):
        from app.models.evidence import Stance
        stance, confidence = ratings.stance_from_rating("fact-checked and true")
        assert stance == Stance.SUPPORTS and confidence >= 0.9


class TestRelevanceGuard:
    def test_relevant_factcheck_matches(self, ratings):
        assert ratings.factcheck_is_relevant(
            "vaccines cause autism",
            "A viral post claiming vaccines cause autism has been debunked by scientists."
        ) is True

    def test_unrelated_factcheck_does_not_match(self, ratings):
        assert ratings.factcheck_is_relevant(
            "vaccines cause autism",
            "The football match between the two rivals was cancelled due to rain."
        ) is False

    def test_empty_text_is_not_relevant(self, ratings):
        assert ratings.factcheck_is_relevant("vaccines cause autism", "") is False


class TestTemporalQualifiers:
    """Regression for the live-tested Eiffel Tower case."""

    def test_detects_annual_qualifier(self, ratings):
        assert ratings.temporal_qualifiers(
            "The Eiffel Tower grows about 15 centimeters taller every year"
        ) == frozenset({"annual"})

    def test_detects_season_qualifier(self, ratings):
        assert ratings.temporal_qualifiers(
            "The Eiffel Tower grows taller in the summer"
        ) == frozenset({"summer"})

    def test_no_qualifier_is_empty(self, ratings):
        assert ratings.temporal_qualifiers("Smoking causes lung cancer") == frozenset()

    def test_live_case_flags_conflict(self, ratings):
        "The exact mismatch from live testing: 'every year' vs 'in the summer'."
        assert ratings.qualifier_conflict(
            "The Eiffel Tower grows about 15 centimeters taller every year.",
            "Claim that the Eiffel Tower grows taller in the summer rated mostly true."
        ) is True

    def test_matching_qualifier_is_not_a_conflict(self, ratings):
        assert ratings.qualifier_conflict(
            "Mount Everest grows about 4 millimeters taller each year",
            "Everest grows roughly 4mm annually"
        ) is False

    def test_no_claim_qualifier_is_not_a_conflict(self, ratings):
        assert ratings.qualifier_conflict(
            "The Sun is 150 million kilometers from Earth",
            "The Sun sits about 150 million km away"
        ) is False

    def test_summer_plus_annual_claim_with_summer_evidence(self, ratings):
        assert ratings.qualifier_conflict(
            "The tower grows 15cm taller in summer",
            "It grows taller in the summertime"
        ) is False
