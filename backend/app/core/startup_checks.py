"""
TruthLens Startup Configuration Checks

Validates that the application is not started in production with sample/insecure
secrets or database credentials. Kept dependency-free (stdlib only) so it can be
unit tested without installing the ML/API stack.
"""

_WINDOW_HINTS = (
    # Known sample / unsafe markers for the JWT secret
    "your_super_secret_jwt_key_change_in_production",
    "change_in_production",
    "super_secret_jwt",
)

_DB_CREDENTIAL_HINTS = (
    # Default/demo database credentials that must never be used in production
    "truthlens:truthlens_secret@",
    ":truthlens_secret@",
    "your_secure_password_here",
    "postgres:postgres@",
    "password@",
)


def validate_startup_config(
    environment: str,
    jwt_secret_key: str,
    database_url: str,
) -> None:
    """
    Raise RuntimeError if running in production with insecure defaults.

    Args:
        environment: Deployment environment (e.g. "development", "production").
        jwt_secret_key: Configured JWT signing secret.
        database_url: Configured SQLAlchemy database URL.

    Raises:
        RuntimeError: In production ("production"/"prod") when insecure
            defaults are detected. Never raises outside production.
    """
    env = (environment or "development").strip().lower()
    if env not in ("production", "prod"):
        return

    problems = []

    secret = (jwt_secret_key or "").strip()
    if not secret or any(h in secret.lower() for h in _WINDOW_HINTS):
        problems.append(
            "JWT_SECRET_KEY is missing or uses the sample/default value. "
            "Set a long random secret before starting in production."
        )

    db_url = (database_url or "")
    if any(h in db_url.lower() for h in _DB_CREDENTIAL_HINTS):
        problems.append(
            "DATABASE_URL uses default/demo credentials. "
            "Configure a private database password before starting in production."
        )

    if problems:
        raise RuntimeError(
            "Refusing to start: unsafe configuration for production. "
            + " | ".join(problems)
        )
