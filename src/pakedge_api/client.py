"""Pakedge API client for managed switches (SX-24P16, etc.)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)


def _normalize_obj(raw: str) -> str:
    """Convert PakEdge's unquoted-key object to valid Python dict literal.

    Input:  {port:1,linkstatus:0,state:1,pvid:1}
    Output: {"port":1,"linkstatus":0,"state":1,"pvid":1}
    """
    # Normalize: first strip trailing comma inside braces
    if raw.endswith(","):
        raw = raw[:-1]
    # Wrap bare word keys in double quotes
    # After stripping trailing comma, keys are at {word: or ,word:
    return re.sub(r"(?<=\{|\,)\s*(\w+)\s*:", r' "\1":', raw)


@dataclass
class PortStatus:
    """Represents the status of a single switch port."""

    port: int
    state: int  # 0 = no link, 1 = link
    linkstatus: int  # 0 = off, 1 = up
    pvid: int  # Port VLAN ID


@dataclass
class FirmwareInfo:
    """Firmware information from the switch."""

    version: str
    update_available: bool = False


class PakedgeError(Exception):
    """Base exception for Pakedge API errors."""


class PakedgeAuthError(PakedgeError):
    """Authentication failed."""


class PakedgeSessionExpired(PakedgeError):
    """Session has timed out."""


class PakedgeClient:
    """Client for Pakedge managed switches.

    Uses the same CGI-based interface as the web UI. All endpoints
    use GET requests with query parameters. Session state is managed
    via cookies.
    """

    def __init__(
        self,
        host: str,
        username: str = "pakedge",
        password: str = "",
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session = requests.Session()
        self._logged_in = False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    def login(self) -> None:
        """Authenticate with the switch.

        The PakEdge uses a client-side cookie (``usa_Pakedge_user``)
        for session management — there is no server-side session.
        The cookie format is ``username|0``.
        """
        url = f"http://{self.host}/cgi/login_pkd"
        params = {"username": self.username, "password": self.password}

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise PakedgeError(f"Login failed: {exc}") from exc

        # The PakEdge sets the session cookie client-side (JS).
        # We replicate the JS behavior: document.cookie = "usa_Pakedge_user=" + username + "|0"
        self._session.cookies.set(
            "usa_Pakedge_user",
            f"{self.username}|0",
            domain=self.host,
            path="/",
        )
        self._logged_in = True
        logger.info("Logged in to %s as %s", self.host, self.username)

    def logout(self) -> None:
        """Invalidate the session."""
        if not self._logged_in:
            return

        try:
            self._session.get(
                f"http://{self.host}/cgi/logout_pkd",
                timeout=self.timeout,
            )
        except requests.RequestException:
            pass  # Best effort

        self._logged_in = False
        self._session.cookies.clear()

    def _request(self, endpoint: str, params: dict[str, str] | None = None) -> str:
        """Make a GET request to a CGI endpoint.

        Raises:
            PakedgeSessionExpired: If the session has timed out.
        """
        if not self._logged_in:
            raise PakedgeError("Not logged in. Call login() first.")

        url = f"http://{self.host}/{endpoint}"
        params = {**(params or {}), "rand": str(id(self))}

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise PakedgeError(f"Request to {endpoint} failed: {exc}") from exc

        # Check for session timeout (the JS checks for return value 20)
        if resp.text.strip() == "20":
            self._logged_in = False
            raise PakedgeSessionExpired("Session expired")

        return resp.text

    def get_port_status(self) -> list[PortStatus]:
        """Get the status of all switch ports.

        Returns a list of PortStatus objects, one per port (1-indexed).
        Port data is returned as pipe-delimited JSON objects.
        """
        raw = self._request("cgi/port_basicInfo_pkd")
        return self._parse_port_status(raw)

    def get_firmware_info(self) -> FirmwareInfo:
        """Get firmware version and update availability."""
        raw = self._request("cgi/cloudfu_basicInfo_pkd")
        return self._parse_firmware_info(raw)

    def check_session(self) -> bool:
        """Check if the session is still valid.

        Returns True if the session is alive, False if expired.
        """
        try:
            raw = self._request("cgi/check_timeout_pkd")
            return raw.strip() != "20"
        except PakedgeSessionExpired:
            return False
        except PakedgeError:
            return False

    @staticmethod
    def _parse_port_status(raw: str) -> list[PortStatus]:
        """Parse pipe-delimited port status data.

        Format: {port:1,linkstatus:0,state:1,pvid:1,}|{port:2,...}|...|0
        Keys are unquoted, trailing commas present, and there may be a
        trailing footer value (e.g. ``|0``) after the last port.
        """
        raw = raw.strip()
        if not raw:
            return []

        # Unwrap outer quotes if present
        if raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1]

        parts = raw.split("|")
        ports: list[PortStatus] = []

        for i, part in enumerate(parts):
            part = part.strip()
            if not part or part == "0":
                continue

            # Only parse if it looks like an object
            if not (part.startswith("{") and part.endswith("}")):
                continue

            # Normalize: remove trailing comma, quote keys
            # {port:1,linkstatus:0,state:1,pvid:1,} → {"port":1,"linkstatus":0,"state":1,"pvid":1}
            normalized = part.rstrip(",")
            normalized = _normalize_obj(normalized)

            try:
                data: dict[str, Any] = eval(normalized)  # noqa: S307 — trusted device data
                ports.append(
                    PortStatus(
                        port=data.get("port", i + 1),
                        state=data.get("state", 0),
                        linkstatus=data.get("linkstatus", 0),
                        pvid=data.get("pvid", 1),
                    )
                )
            except (SyntaxError, ValueError) as exc:
                logger.warning("Failed to parse port %d data: %s", i + 1, exc)

        return ports

    @staticmethod
    def _parse_firmware_info(raw: str) -> FirmwareInfo:
        """Parse firmware info JSON.

        Format: '{firmVersion:"V",update:0}' — outer quotes, unquoted keys,
        string values may already be quoted but numeric values are bare.
        """
        raw = raw.strip()
        if not raw:
            return FirmwareInfo(version="unknown", update_available=False)

        # Unwrap outer quotes
        if raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1]

        # Quote unquoted keys: {firmVersion: → {"firmVersion":
        raw = re.sub(r"(?<=\{|\,)\s*(\w+)\s*:", r' "\1":', raw)

        try:
            data: dict[str, Any] = eval(raw)  # noqa: S307
            return FirmwareInfo(
                version=data.get("firmVersion", "unknown"),
                update_available=bool(data.get("update", False)),
            )
        except (SyntaxError, ValueError) as exc:
            logger.warning("Failed to parse firmware info: %s", exc)
            return FirmwareInfo(version="unknown")

    def __enter__(self) -> PakedgeClient:
        self.login()
        return self

    def __exit__(self, *args: Any) -> None:
        self.logout()

    def __repr__(self) -> str:
        status = "logged in" if self._logged_in else "not logged in"
        return f"<PakedgeClient host={self.host} {status}>"
