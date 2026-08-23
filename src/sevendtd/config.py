"""Environment-backed client configuration."""

from typing import Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SevenDTDSettings(BaseSettings):
    """Connection settings. Credentials are required and secret-safe."""

    model_config = SettingsConfigDict(
        env_prefix="SEVENTDTD_",
        extra="ignore",
        validate_default=True,
    )

    base_url: AnyHttpUrl
    token_name: SecretStr
    secret: SecretStr
    timeout: float = Field(default=10.0, gt=0)

    @field_validator("token_name", "secret")
    @classmethod
    def _not_empty(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value():
            raise ValueError("credential cannot be empty")
        return value

    @classmethod
    def from_values(
        cls,
        *,
        base_url: str,
        token_name: str,
        secret: str,
        timeout: float = 10.0,
    ) -> Self:
        return cls.model_validate(
            {
                "base_url": base_url,
                "token_name": SecretStr(token_name),
                "secret": SecretStr(secret),
                "timeout": timeout,
            }
        )

    @classmethod
    def from_environment(cls) -> Self:
        """Load required values from the configured environment names."""

        return cls()  # pyright: ignore[reportCallIssue]
