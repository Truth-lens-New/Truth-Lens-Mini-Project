"""
Tests for production configuration guardrails (app/core/startup_checks.py).
"""

import pytest

from import_utils import isolated_imports


@pytest.fixture(scope="module")
def checks():
    with isolated_imports(["app", "app.core"]) as imp:
        yield imp("app.core.startup_checks")


SAMPLE_SECRET = "your_super_secret_jwt_key_change_in_production"
GOOD_SECRET = "a-long-random-production-secret-value-7f3a9c2e41"


class TestDevelopmentIsUnaffected:
    def test_sample_secret_allowed_in_development(self, checks):
        checks.validate_startup_config("development", SAMPLE_SECRET, "")

    def test_default_db_creds_allowed_in_development(self, checks):
        checks.validate_startup_config(
            "development", GOOD_SECRET,
            "postgresql+asyncpg://truthlens:truthlens_secret@localhost:5432/truthlens",
        )

    def test_unset_env_treated_as_development(self, checks):
        checks.validate_startup_config("", "", "")


class TestProductionGuards:
    def test_sample_jwt_secret_refused(self, checks):
        with pytest.raises(RuntimeError):
            checks.validate_startup_config("production", SAMPLE_SECRET, "postgresql+asyncpg://u:p@db:5432/db")

    def test_prod_substring_refused(self, checks):
        with pytest.raises(RuntimeError):
            checks.validate_startup_config("prod", SAMPLE_SECRET, "")

    def test_empty_jwt_secret_refused(self, checks):
        with pytest.raises(RuntimeError):
            checks.validate_startup_config("production", "", "")

    def test_default_db_credentials_refused(self, checks):
        with pytest.raises(RuntimeError):
            checks.validate_startup_config(
                "production", GOOD_SECRET,
                "postgresql+asyncpg://truthlens:truthlens_secret@db:5432/truthlens",
            )

    def test_sample_db_password_refused(self, checks):
        with pytest.raises(RuntimeError):
            checks.validate_startup_config(
                "production", GOOD_SECRET,
                "postgresql+asyncpg://truthlens:your_secure_password_here@db:5432/truthlens",
            )

    def test_case_insensitive_environment_and_markers(self, checks):
        with pytest.raises(RuntimeError):
            checks.validate_startup_config(
                "Production", GOOD_SECRET,
                "postgresql+asyncpg://truthlens:TRUTHLENS_SECRET@db:5432/truthlens",
            )

    def test_valid_production_configures_cleanly(self, checks):
        checks.validate_startup_config(
            "production", GOOD_SECRET,
            "postgresql+asyncpg://truthlens:Str0ngPr1vatePassw0rd@db:5432/truthlens",
        )
