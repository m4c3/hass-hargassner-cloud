from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any, Self

import pytest

from custom_components.hargassner_cloud.api import (
    HargassnerAuthError,
    HargassnerClient,
    HargassnerClientCredentialsError,
    HargassnerConnectionError,
    HargassnerMaintenanceError,
)


class FakeResponse:
    def __init__(
        self,
        status: int,
        payload: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> None:
        self.status = status
        self.payload = payload or {}
        self._text = text if text is not None else str(self.payload)

    async def text(self) -> str:
        return self._text

    async def json(self) -> dict[str, Any]:
        return self.payload

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


class FakeSession:
    def __init__(
        self,
        *,
        posts: list[FakeResponse] | None = None,
        gets: list[FakeResponse] | None = None,
    ) -> None:
        self.posts = posts or []
        self.gets = gets or []
        self.post_calls: list[tuple[str, dict[str, Any]]] = []
        self.get_calls: list[str] = []

    def post(
        self, url: str, *, json: dict[str, Any], **_kwargs: object
    ) -> FakeResponse:
        self.post_calls.append((url, json))
        return self.posts.pop(0)

    def get(self, url: str, **_kwargs: object) -> FakeResponse:
        self.get_calls.append(url)
        return self.gets.pop(0)


def make_client(
    session: FakeSession, *, secret: str = "secret", client_id: str = "1"
) -> HargassnerClient:
    return HargassnerClient(
        session,  # type: ignore[arg-type]
        "https://example.test",
        "user@example.test",
        "password",
        secret,
        "42",
        client_id,
    )


def run(coro_factory: Callable[[], Any]) -> Any:
    return asyncio.run(coro_factory())


def test_login_uses_access_token_without_logging_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = FakeSession(
        posts=[FakeResponse(200, {"access_token": "token"})],
        gets=[FakeResponse(500)],
    )
    client = make_client(session)

    with caplog.at_level(
        logging.DEBUG, logger="custom_components.hargassner_cloud.api"
    ):
        run(client.login)

    assert client._token == "token"
    assert session.post_calls[0][1]["client_id"] == "1"
    assert session.post_calls[0][1]["client_secret"] == "secret"
    assert "user@example.test" not in caplog.text
    assert "password" not in caplog.text
    assert "secret" not in caplog.text
    assert "token" not in caplog.text
    assert client.diagnostics == {
        "phase": "login",
        "outcome": "success",
        "http_status": 200,
        "credential_source": "stored_legacy",
        "error_type": None,
    }


def test_login_distinguishes_connection_failure() -> None:
    session = FakeSession(posts=[FakeResponse(500)], gets=[FakeResponse(500)])
    client = make_client(session)

    with pytest.raises(HargassnerConnectionError):
        run(client.login)


def test_login_reports_missing_web_client_credentials() -> None:
    session = FakeSession(gets=[FakeResponse(500)])
    client = make_client(session, secret="", client_id="")

    with pytest.raises(HargassnerClientCredentialsError):
        run(client.login)


def test_login_reports_official_maintenance_page() -> None:
    html = "<html><title>Hargassner | Wartungsarbeiten</title></html>"
    session = FakeSession(gets=[FakeResponse(200, text=html)])
    client = make_client(session, secret="", client_id="")

    with pytest.raises(HargassnerMaintenanceError, match="maintenance"):
        run(client.login)

    assert session.post_calls == []
    assert client.diagnostics == {
        "phase": "login_page",
        "outcome": "maintenance",
        "http_status": 200,
        "credential_source": "unavailable",
        "error_type": None,
    }


def test_login_reports_rejected_stored_web_client_credentials() -> None:
    session = FakeSession(posts=[FakeResponse(401)], gets=[FakeResponse(500)])
    client = make_client(session)

    with pytest.raises(HargassnerClientCredentialsError):
        run(client.login)


def test_login_rediscovers_rotated_credentials() -> None:
    html = '<script type="module" src="/build/assets/app-test.js"></script>'
    bundle = 'const aa="7",bb="rotated-secret";request({client_id:aa,client_secret:bb})'
    session = FakeSession(
        posts=[FakeResponse(200, {"access_token": "new-token"})],
        gets=[FakeResponse(200, text=html), FakeResponse(200, text=bundle)],
    )
    client = make_client(session, secret="old-secret")

    run(client.login)

    assert client._token == "new-token"
    assert session.post_calls[-1][1]["client_id"] == "7"
    assert session.post_calls[-1][1]["client_secret"] == "rotated-secret"


def test_login_uses_concrete_callsite_in_current_minified_bundle() -> None:
    html = '<script type="module" src="/build/assets/app-test.js"></script>'
    bundle = (
        'const t="wrong-id",a="wrong-secret",ra="7",ps="rotated-secret";'
        "const api={login(i,e,t,a){return post({client_id:t,client_secret:a})}};"
        "class auth{static login(e,t){return api.login(e,t,ra,ps)}}"
    )
    session = FakeSession(
        posts=[FakeResponse(200, {"access_token": "new-token"})],
        gets=[FakeResponse(200, text=html), FakeResponse(200, text=bundle)],
    )
    client = make_client(session, secret="old-secret")

    run(client.login)

    assert session.post_calls == [
        (
            "https://example.test/api/auth/login",
            {
                "email": "user@example.test",
                "password": "password",
                "client_id": "7",
                "client_secret": "rotated-secret",
            },
        )
    ]


def test_login_rejects_bad_password_without_repeating_same_credentials() -> None:
    html = '<script type="module" src="/build/assets/app-test.js"></script>'
    bundle = 'const aa="1",bb="secret";request({client_id:aa,client_secret:bb})'
    session = FakeSession(
        posts=[FakeResponse(401)],
        gets=[FakeResponse(200, text=html), FakeResponse(200, text=bundle)],
    )
    client = make_client(session)

    with pytest.raises(HargassnerAuthError):
        run(client.login)

    assert len(session.post_calls) == 1


def test_widgets_retry_same_endpoint_after_401() -> None:
    session = FakeSession(gets=[FakeResponse(401), FakeResponse(200, {"data": []})])
    client = make_client(session)
    client._token = "expired"

    async def fake_login() -> None:
        client._token = "renewed"

    client.login = fake_login  # type: ignore[method-assign]
    result = run(client.get_widgets)

    assert result == {"data": []}
    assert len(session.get_calls) == 2
    assert session.get_calls[0] == session.get_calls[1]


def test_device_metadata_extracts_allowlisted_software_versions() -> None:
    payload = {
        "data": {
            "name": "Private installation",
            "devices": [
                {
                    "serial_number": "private-serial",
                    "software": {"version_code": "V_HKR4f1"},
                    "io_firmware_version": "IO_2.3",
                }
            ],
        }
    }

    assert HargassnerClient._parse_device_metadata(payload) == {
        "software_version": "V_HKR4f1",
        "io_firmware_version": "IO_2.3",
    }


def test_device_metadata_rejects_unexpected_or_private_values() -> None:
    payload = {
        "data": {
            "devices": [
                {
                    "software": {"version_code": "user@example.test"},
                    "io_firmware_version": {"value": "secret"},
                }
            ]
        }
    }

    assert HargassnerClient._parse_device_metadata(payload) == {}


def test_device_metadata_endpoint_is_optional_when_forbidden() -> None:
    session = FakeSession(gets=[FakeResponse(403)])
    client = make_client(session)
    client._token = "token"

    assert run(client.get_device_metadata) == {}


@pytest.mark.parametrize(
    "payload",
    [
        {"data": [{"id": 42, "name": "Home"}]},
        {"installations": [{"id": "42", "name": "Home"}]},
        [{"id": 42, "name": "Home"}],
    ],
)
def test_parse_installations(payload: object) -> None:
    assert HargassnerClient._parse_installations(payload) == [
        {"id": "42", "name": "Home"}
    ]


def test_installation_discovery_falls_back_after_404() -> None:
    session = FakeSession(
        gets=[FakeResponse(404), FakeResponse(200, {"data": [{"id": 42}]})]
    )
    client = make_client(session)
    client._token = "token"

    result = run(client.get_installations)

    assert result == [{"id": "42", "name": "Installation 42"}]
    assert session.get_calls == [
        "https://example.test/api/installations",
        "https://example.test/api/user/installations",
    ]
