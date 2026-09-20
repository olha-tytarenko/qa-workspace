import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def clean_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Isolate from a developer's shell environment and local .env file."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_application_modules_import_without_database_url() -> None:
    env = {key: value for key, value in os.environ.items() if key != "DATABASE_URL"}

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import app.main, app.core.config, app.db.base, app.db.session",
        ],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_get_settings_fails_clearly_when_database_url_is_missing() -> None:
    with pytest.raises(ValidationError) as error:
        get_settings()

    assert "database_url" in str(error.value)


def test_get_settings_reads_environment_and_caches_the_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")

    first = get_settings()

    assert first.database_url == "postgresql+asyncpg://u:p@localhost/db"
    assert get_settings() is first


def test_settings_reject_a_synchronous_driver_url() -> None:
    with pytest.raises(ValidationError) as error:
        Settings(database_url="postgresql+psycopg://u:p@localhost/db")

    assert "asyncpg" in str(error.value)
