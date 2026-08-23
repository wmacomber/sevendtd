"""Authenticated HTTP transport. No game-domain knowledge lives here."""

from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from time import monotonic
from typing import Any, TypeVar

import httpx
from pydantic import SecretStr, TypeAdapter, ValidationError

from sevendtd.exceptions import (
    SevenDTDAPIError,
    SevenDTDAuthenticationError,
    SevenDTDConnectionError,
    SevenDTDInvalidResponseError,
    SevenDTDTimeoutError,
)
from sevendtd.logging import get_logger, safe_extra
from sevendtd.models.common import ResponseEnvelope, ResponseMeta

T = TypeVar("T")

TOKEN_HEADER = "X-SDTD-API-TOKENNAME"
SECRET_HEADER = "X-SDTD-API-SECRET"


class HTTPTransport:
    def __init__(
        self,
        *,
        base_url: str,
        token_name: SecretStr,
        secret: SecretStr,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
        owns_client: bool | None = None,
    ) -> None:
        normalized = base_url.rstrip("/") + "/"
        self._base_url = httpx.URL(normalized)
        self._headers = {
            TOKEN_HEADER: token_name.get_secret_value(),
            SECRET_HEADER: secret.get_secret_value(),
        }
        self._timeout_seconds = timeout
        self._client = client or httpx.AsyncClient(base_url=normalized, timeout=timeout)
        self._owns_client = client is None if owns_client is None else owns_client
        self._logger = get_logger()

    @property
    def timeout_seconds(self) -> float:
        return self._timeout_seconds

    async def close(self) -> None:
        if self._owns_client and not self._client.is_closed:
            await self._client.aclose()

    async def request_json(
        self,
        method: str,
        endpoint: str,
        data_type: type[T] | Any,
        *,
        resource: str,
        json: object | None = None,
    ) -> tuple[T, ResponseMeta]:
        response = await self._request(
            method,
            endpoint,
            resource=resource,
            json=json,
        )
        try:
            raw = response.json()
            envelope = ResponseEnvelope.model_validate(raw)
            data = TypeAdapter(data_type).validate_python(envelope.data)
        except (ValueError, ValidationError) as exc:
            self._logger.warning(
                "response.parse.failed",
                extra=safe_extra(
                    {
                        "resource": resource,
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "exception_category": type(exc).__name__,
                    }
                ),
            )
            raise SevenDTDInvalidResponseError(
                f"invalid response structure for {endpoint}"
            ) from exc
        return data, envelope.meta

    async def request_bytes(
        self,
        endpoint: str,
        *,
        resource: str,
        params: Mapping[str, str | int] | None = None,
    ) -> httpx.Response:
        return await self._request("GET", endpoint, resource=resource, params=params)

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        resource: str,
        json: object | None = None,
        params: Mapping[str, str | int] | None = None,
    ) -> httpx.Response:
        started = monotonic()
        try:
            response = await self._client.request(
                method,
                self._base_url.join(endpoint.lstrip("/")),
                headers=self._headers,
                json=json,
                params=params,
            )
        except httpx.TimeoutException as exc:
            self._log_failure(method, endpoint, resource, started, exc)
            raise SevenDTDTimeoutError(f"request timed out for {endpoint}") from exc
        except httpx.RequestError as exc:
            self._log_failure(method, endpoint, resource, started, exc)
            raise SevenDTDConnectionError(f"request failed for {endpoint}") from exc
        self._log_complete(method, endpoint, resource, started, response.status_code)
        self._raise_for_status(endpoint, response.status_code)
        return response

    @asynccontextmanager
    async def stream(
        self,
        endpoint: str,
        *,
        resource: str,
        headers: Mapping[str, str] | None = None,
    ) -> AsyncGenerator[httpx.Response]:
        request_headers = dict(headers or {})
        request_headers.update(self._headers)
        timeout = httpx.Timeout(
            connect=self._timeout_seconds,
            read=None,
            write=self._timeout_seconds,
            pool=self._timeout_seconds,
        )
        started = monotonic()
        try:
            async with self._client.stream(
                "GET",
                self._base_url.join(endpoint.lstrip("/")),
                headers=request_headers,
                timeout=timeout,
            ) as response:
                self._log_complete("GET", endpoint, resource, started, response.status_code)
                self._raise_for_status(endpoint, response.status_code)
                yield response
        except httpx.TimeoutException as exc:
            self._log_failure("GET", endpoint, resource, started, exc)
            raise SevenDTDTimeoutError(f"stream timed out for {endpoint}") from exc
        except httpx.RequestError as exc:
            self._log_failure("GET", endpoint, resource, started, exc)
            raise SevenDTDConnectionError(f"stream failed for {endpoint}") from exc

    @staticmethod
    def _raise_for_status(endpoint: str, status_code: int) -> None:
        if status_code in {401, 403}:
            raise SevenDTDAuthenticationError(endpoint, status_code)
        if not 200 <= status_code < 300:
            raise SevenDTDAPIError(endpoint, status_code)

    def _log_complete(
        self,
        method: str,
        endpoint: str,
        resource: str,
        started: float,
        status_code: int,
    ) -> None:
        self._logger.info(
            "http.request.completed",
            extra=safe_extra(
                {
                    "method": method,
                    "endpoint": endpoint,
                    "resource": resource,
                    "status_code": status_code,
                    "latency_ms": round((monotonic() - started) * 1000, 3),
                }
            ),
        )

    def _log_failure(
        self,
        method: str,
        endpoint: str,
        resource: str,
        started: float,
        exc: Exception,
    ) -> None:
        self._logger.warning(
            "http.request.failed",
            extra=safe_extra(
                {
                    "method": method,
                    "endpoint": endpoint,
                    "resource": resource,
                    "latency_ms": round((monotonic() - started) * 1000, 3),
                    "exception_category": type(exc).__name__,
                }
            ),
        )
