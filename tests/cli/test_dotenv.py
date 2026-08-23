from pathlib import Path

import pytest

from sevendtd.cli.app import CLIState, load_cli_dotenv
from sevendtd.exceptions import SevenDTDConfigurationError

VARIABLES = (
    "SEVENTDTD_BASE_URL",
    "SEVENTDTD_TOKEN_NAME",
    "SEVENTDTD_SECRET",
    "SEVENTDTD_TIMEOUT",
)


def clear_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_explicit_dotenv_loads_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings(monkeypatch)
    env_file = tmp_path / "server.env"
    env_file.write_text(
        "SEVENTDTD_BASE_URL=http://dotenv.example:26980\n"
        "SEVENTDTD_TOKEN_NAME=dotenv-token\n"
        "SEVENTDTD_SECRET=dotenv-secret\n"
        "SEVENTDTD_TIMEOUT=12.5\n"
    )

    assert load_cli_dotenv(env_file) == env_file
    settings = CLIState(None, None, None, None).settings()
    assert str(settings.base_url) == "http://dotenv.example:26980/"
    assert settings.timeout == 12.5


def test_process_environment_wins_over_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clear_settings(monkeypatch)
    monkeypatch.setenv("SEVENTDTD_BASE_URL", "http://process.example:26980")
    monkeypatch.setenv("SEVENTDTD_TOKEN_NAME", "process-token")
    monkeypatch.setenv("SEVENTDTD_SECRET", "process-secret")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "SEVENTDTD_BASE_URL=http://dotenv.example:26980\n"
        "SEVENTDTD_TOKEN_NAME=dotenv-token\n"
        "SEVENTDTD_SECRET=dotenv-secret\n"
    )

    load_cli_dotenv(env_file)
    settings = CLIState(None, None, None, None).settings()
    assert str(settings.base_url) == "http://process.example:26980/"


def test_cli_flags_win_over_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_settings(monkeypatch)
    monkeypatch.setenv("SEVENTDTD_BASE_URL", "http://process.example:26980")
    monkeypatch.setenv("SEVENTDTD_TOKEN_NAME", "process-token")
    monkeypatch.setenv("SEVENTDTD_SECRET", "process-secret")

    settings = CLIState("http://flag.example:26980", "flag-token", "flag-secret", 3.0).settings()
    assert str(settings.base_url) == "http://flag.example:26980/"
    assert settings.token_name.get_secret_value() == "flag-token"
    assert settings.timeout == 3.0


def test_missing_explicit_dotenv_fails(tmp_path: Path) -> None:
    with pytest.raises(SevenDTDConfigurationError, match="does not exist"):
        load_cli_dotenv(tmp_path / "missing.env")
