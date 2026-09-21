import pytest

from tests.database import (
    TEST_DATABASE_URL_ENV,
    TestDatabase,
    UnsafeTestDatabaseError,
    validate_test_database_url,
)

DEV_URL = "postgresql+asyncpg://postgres:postgres@db:5432/qa_workspace"
TEST_URL = "postgresql+asyncpg://postgres:postgres@db:5432/qa_workspace_test"


def test_accepts_a_database_whose_name_ends_in_test() -> None:
    url = validate_test_database_url(TEST_URL, DEV_URL)

    assert url.database == "qa_workspace_test"


@pytest.mark.parametrize(
    "unsafe_url",
    [
        DEV_URL,
        "postgresql+asyncpg://postgres:postgres@db:5432/testing",
        "postgresql+asyncpg://postgres:postgres@db:5432/",
        "postgresql+asyncpg://postgres:postgres@db:5432",
        "postgresql+psycopg://postgres:postgres@db:5432/qa_workspace_test",
    ],
)
def test_rejects_urls_that_are_not_clearly_a_test_database(unsafe_url: str) -> None:
    with pytest.raises(UnsafeTestDatabaseError):
        validate_test_database_url(unsafe_url, DEV_URL)


def test_rejects_a_test_url_identical_to_the_development_url() -> None:
    with pytest.raises(UnsafeTestDatabaseError, match="same database"):
        validate_test_database_url(TEST_URL, TEST_URL)


def test_from_environment_fails_clearly_when_the_url_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(TEST_DATABASE_URL_ENV, raising=False)

    with pytest.raises(UnsafeTestDatabaseError, match=TEST_DATABASE_URL_ENV):
        TestDatabase.from_environment()


def test_from_environment_connects_administration_to_the_postgres_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(TEST_DATABASE_URL_ENV, TEST_URL)
    monkeypatch.setenv("DATABASE_URL", DEV_URL)

    database = TestDatabase.from_environment()

    assert database.name == "qa_workspace_test"
    assert database.admin_url.database == "postgres"
