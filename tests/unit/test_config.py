import pytest
from pydantic import ValidationError

from sevendtd import SevenDTDSettings


def test_settings_load_exact_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEVENTDTD_BASE_URL", "http://example.test:26980")
    monkeypatch.setenv("SEVENTDTD_TOKEN_NAME", "distinct-token")
    monkeypatch.setenv("SEVENTDTD_SECRET", "distinct-secret")
    settings = SevenDTDSettings()
    assert str(settings.base_url) == "http://example.test:26980/"
    assert "distinct-secret" not in repr(settings)
    assert "distinct-secret" not in settings.model_dump_json()
    assert "distinct-token" not in settings.model_dump_json()


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        SevenDTDSettings.from_values(
            base_url="http://example.test", token_name="token", secret="secret", timeout=0
        )
