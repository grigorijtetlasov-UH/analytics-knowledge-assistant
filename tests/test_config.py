import pytest

from app.config import Settings


def make_settings(**overrides: object) -> Settings:
    # _env_file=None: ignore the developer's real .env so the test is deterministic.
    values: dict[str, object] = {
        "postgres_user": "analytics",
        "postgres_password": "secret",
        "postgres_db": "analytics",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_database_url_uses_defaults_for_host_and_port() -> None:
    settings = make_settings()
    assert settings.database_url == "postgresql://analytics:secret@127.0.0.1:5432/analytics"


def test_database_url_percent_encodes_special_characters_in_password() -> None:
    settings = make_settings(postgres_password="p@ss:w/rd")
    assert settings.database_url == (
        "postgresql://analytics:p%40ss%3Aw%2Frd@127.0.0.1:5432/analytics"
    )


def test_password_is_hidden_in_repr() -> None:
    settings = make_settings(postgres_password="secret")
    assert "secret" not in repr(settings)


def test_readonly_url_uses_the_readonly_role() -> None:
    settings = make_settings(readonly_db_password="r@o")
    assert settings.readonly_database_url == (
        "postgresql://olist_reader:r%40o@127.0.0.1:5432/analytics"
    )


def test_readonly_url_needs_a_password() -> None:
    with pytest.raises(ValueError, match="READONLY_DB_PASSWORD"):
        _ = make_settings().readonly_database_url
