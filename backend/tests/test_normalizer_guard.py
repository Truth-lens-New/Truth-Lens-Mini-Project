"""
Tests for the semantic-cache contradiction guards (app/services/normalization/
normalizer.py).

The embedding model is replaced by a deterministic hashing bag-of-words stub,
so tests are fully offline and reproducible (no MiniLM download).
"""

import hashlib
import re
import sys
import types

import numpy as np
import pytest

from import_utils import isolated_imports


class _FakeModelManager:
    """Deterministic bag-of-words embedding: cosine = shared-token ratio."""

    def get_embedding(self, text):
        vec = np.zeros(64)
        for word in re.findall(r"[a-z0-9]+", (text or "").lower()):
            digest = int(hashlib.md5(word.encode()).hexdigest(), 16)
            vec[digest % 64] += 1
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec


@pytest.fixture(scope="module")
def bundle():
    with isolated_imports(["app", "app.services", "app.services.models"]) as imp_mod:
        # Register the model-manager stub module directly: the real
        # model_manager.py imports spaCy/transformers, which we must avoid.
        stub = types.ModuleType("app.services.models.model_manager")
        stub.get_model_manager = lambda: _FakeModelManager()
        sys.modules["app.services.models.model_manager"] = stub

        normalizer_mod = imp_mod("app.services.normalization.normalizer")
        yield normalizer_mod


@pytest.fixture()
def normalizer(bundle):
    """A fresh singleton per test."""
    bundle.ClaimNormalizer._instance = None
    return bundle.get_normalizer()


class TestExactMatches:
    def test_identical_text_is_duplicate(self, normalizer):
        first = normalizer.normalize("covid vaccines cause autism")
        assert first["is_duplicate"] is False

        second = normalizer.normalize("covid vaccines cause autism")
        assert second["is_duplicate"] is True
        assert second["canonical_id"] == first["canonical_id"]

    def test_whitespace_and_case_insensitive_exact_match(self, normalizer):
        first = normalizer.normalize("COVID vaccines cause autism")
        second = normalizer.normalize("covid   VACCINES cause autism")
        assert second["is_duplicate"] is True
        assert second["canonical_id"] == first["canonical_id"]


class TestContradictionGuards:
    def test_negated_rephrasing_is_not_a_cache_hit(self, normalizer, bundle):
        """'vaccines do not cause autism' must never reuse the affirmative verdict."""
        normalizer.SIMILARITY_THRESHOLD = 0.50  # force the semantic branch for the stub embeddings

        first = normalizer.normalize("vaccines cause autism")
        fake_verdict = object()
        normalizer.update_result(first["canonical_id"], fake_verdict)

        second = normalizer.normalize("vaccines do not cause autism")
        assert second["is_duplicate"] is False
        assert second["cached_result"] is None

    def test_never_rephrasing_is_not_a_cache_hit(self, normalizer):
        normalizer.SIMILARITY_THRESHOLD = 0.50
        first = normalizer.normalize("AI always gives accurate claims")
        normalizer.update_result(first["canonical_id"], "cached-verdict")

        second = normalizer.normalize("AI never gives accurate claims")
        assert second["is_duplicate"] is False
        assert second["cached_result"] is None

    def test_different_numbers_are_not_a_cache_hit(self, normalizer):
        normalizer.SIMILARITY_THRESHOLD = 0.50
        first = normalizer.normalize("Unemployment fell to 3.1% in September")
        normalizer.update_result(first["canonical_id"], "cached-verdict")

        second = normalizer.normalize("Unemployment fell to 4.1% in September")
        assert second["is_duplicate"] is False
        assert second["cached_result"] is None

    def test_cached_result_still_reused_for_genuine_paraphrase(self, normalizer):
        normalizer.SIMILARITY_THRESHOLD = 0.50
        first = normalizer.normalize("vaccines cause autism")
        normalizer.update_result(first["canonical_id"], "cached-verdict")

        paraphrase = normalizer.normalize("vaccines causes autism")
        assert paraphrase["is_duplicate"] is True
        assert paraphrase["cached_result"] == "cached-verdict"


class TestFirstUse:
    def test_new_claim_has_no_cached_result(self, normalizer):
        result = normalizer.normalize("The Eiffel Tower is in Paris")
        assert result["is_duplicate"] is False
        assert result["cached_result"] is None
        assert result["canonical_text"] == "The Eiffel Tower is in Paris"
