"""
Kalshi API Client

Core client class for authenticated API requests.
"""

import os
import time
import json
import logging
from base64 import b64encode
from functools import cached_property
from typing import Any
from urllib.parse import urlparse, urlencode

import requests

logger = logging.getLogger(__name__)

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from .exceptions import (
    KalshiAPIError,
    AuthenticationError,
    InsufficientFundsError,
    ResourceNotFoundError,
)
from .events import Event
from .markets import Market
from .models import MarketModel, EventModel
from .portfolio import Portfolio
from .enums import MarketStatus


# Default configuration
DEFAULT_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
DEMO_API_BASE = "https://demo-api.elections.kalshi.com/trade-api/v2"

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class KalshiClient:
    """Authenticated client for the Kalshi Trading API.

    Usage:
        client = KalshiClient()  # Uses env vars
        client = KalshiClient(api_key_id="...", private_key_path="...")
    """

    def __init__(
        self,
        api_key_id: str | None = None,
        private_key_path: str | None = None,
        api_base: str | None = None,
        demo: bool = False,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Kalshi client.

        Args:
            api_key_id: API key ID. Defaults to KALSHI_API_KEY_ID env var.
            private_key_path: Path to private key file. Defaults to KALSHI_PRIVATE_KEY_PATH env var.
            api_base: API base URL. Defaults to production or demo based on `demo` flag.
            demo: If True, use demo environment. Ignored if api_base is provided.
            timeout: Request timeout in seconds (default 10).
            max_retries: Max retries for transient failures (default 3). Set to 0 to disable.
        """
        from dotenv import load_dotenv
        load_dotenv()

        self.api_key_id = api_key_id or os.getenv("KALSHI_API_KEY_ID")
        private_key_path = private_key_path or os.getenv("KALSHI_PRIVATE_KEY_PATH")

        if not self.api_key_id:
            raise ValueError(
                "API key ID required. Set KALSHI_API_KEY_ID env var or pass api_key_id."
            )
        if not private_key_path:
            raise ValueError(
                "Private key path required. Set KALSHI_PRIVATE_KEY_PATH env var or pass private_key_path."
            )

        self.api_base = api_base or (DEMO_API_BASE if demo else DEFAULT_API_BASE)
        self.timeout = timeout
        self.max_retries = max_retries
        self.private_key = self._load_private_key(private_key_path)

    def _load_private_key(self, key_path: str) -> RSAPrivateKey:
        """Load RSA private key from PEM file."""
        with open(key_path, "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
            if not isinstance(key, RSAPrivateKey):
                raise TypeError(f"Expected RSA private key, got {type(key).__name__}")
            return key

    def _sign_request(self, method: str, path: str) -> tuple[str, str]:
        """Create RSA-PSS signature for API request."""
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method}{path}"

        signature = self.private_key.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return timestamp, b64encode(signature).decode()

    def _get_headers(self, method: str, endpoint: str) -> dict[str, str]:
        """Generate authenticated headers."""
        path_without_query = urlparse(endpoint).path
        full_path = f"/trade-api/v2{path_without_query}"
        timestamp, signature = self._sign_request(method, full_path)
        return {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
        }

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Handle API response and raise custom exceptions."""
        status_code = int(response.status_code or 500)

        if status_code < 400:
            logger.debug("Response %s: Success", status_code)
            if status_code == 204 or not response.content:
                return {}
            return response.json()

        logger.error("Response %s: Error body: %s", status_code, response.text)
        try:
            error_data = response.json()
            message = error_data.get("message") or error_data.get(
                "error_message", "Unknown Error"
            )
            code = error_data.get("code") or error_data.get("error_code")
        except (ValueError, requests.exceptions.JSONDecodeError):
            message = response.text
            code = None

        if status_code in (401, 403):
            raise AuthenticationError(status_code, message, code)
        elif status_code == 404:
            raise ResourceNotFoundError(status_code, message, code)
        elif code in ("insufficient_funds", "insufficient_balance"):
            raise InsufficientFundsError(status_code, message, code)
        else:
            raise KalshiAPIError(status_code, message, code)

    def _request(
        self,
        method_func,
        method_name: str,
        endpoint: str,
        **kwargs,
    ) -> requests.Response:
        """Execute an HTTP request with timeout and retry on transient failures.

        Retries on 429/5xx status codes and connection errors with exponential backoff.
        Re-signs each attempt to keep the timestamp fresh.
        """
        url = f"{self.api_base}{endpoint}"

        for attempt in range(self.max_retries + 1):
            headers = self._get_headers(method_name, endpoint)
            try:
                response = method_func(
                    url, headers=headers, timeout=self.timeout, **kwargs
                )
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
            ) as e:
                if attempt == self.max_retries:
                    raise
                wait = min(2 ** attempt * 0.5, 30)
                logger.warning(
                    "%s %s failed (%s), retry %d/%d in %.1fs",
                    method_name, endpoint, type(e).__name__,
                    attempt + 1, self.max_retries, wait,
                )
                time.sleep(wait)
                continue

            if response.status_code not in _RETRYABLE_STATUS_CODES:
                return response
            if attempt == self.max_retries:
                return response

            retry_after = response.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else min(2 ** attempt * 0.5, 30)
            except (ValueError, TypeError):
                wait = min(2 ** attempt * 0.5, 30)

            logger.warning(
                "%s %s returned %d, retry %d/%d in %.1fs",
                method_name, endpoint, response.status_code,
                attempt + 1, self.max_retries, wait,
            )
            time.sleep(wait)

        return response  # unreachable, satisfies type checker

    def get(self, endpoint: str) -> dict[str, Any]:
        """Make authenticated GET request."""
        logger.debug("GET %s", endpoint)
        response = self._request(requests.get, "GET", endpoint)
        return self._handle_response(response)

    def paginated_get(
        self,
        path: str,
        response_key: str,
        params: dict[str, Any],
        fetch_all: bool = False,
    ) -> list[dict]:
        """Fetch items with automatic cursor-based pagination.

        Args:
            path: API endpoint path (e.g., "/markets").
            response_key: Key in response JSON containing the items list.
            params: Query parameters (None values are filtered out).
            fetch_all: If True, follow cursors to fetch all pages.
        """
        params = dict(params)  # Don't mutate caller's dict
        all_items: list[dict] = []
        while True:
            filtered = {k: v for k, v in params.items() if v is not None}
            endpoint = f"{path}?{urlencode(filtered)}" if filtered else path
            response = self.get(endpoint)
            all_items.extend(response.get(response_key, []))
            cursor = response.get("cursor", "")
            if not fetch_all or not cursor:
                break
            params["cursor"] = cursor
        return all_items

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make authenticated POST request."""
        logger.debug("POST %s", endpoint)
        body = json.dumps(data, separators=(",", ":"))
        response = self._request(requests.post, "POST", endpoint, data=body)
        return self._handle_response(response)

    def delete(self, endpoint: str) -> dict[str, Any]:
        """Make authenticated DELETE request."""
        logger.debug("DELETE %s", endpoint)
        response = self._request(requests.delete, "DELETE", endpoint)
        return self._handle_response(response)

    # --- Domain methods ---

    @cached_property
    def portfolio(self) -> Portfolio:
        """The authenticated user's portfolio."""
        return Portfolio(self)

    def get_market(self, ticker: str) -> Market:
        """Get a Market by ticker."""
        response = self.get(f"/markets/{ticker}")
        data = response.get("market", response)
        model = MarketModel.model_validate(data)
        return Market(self, model)

    def get_markets(
        self,
        series_ticker: str | None = None,
        event_ticker: str | None = None,
        status: MarketStatus | None = None,
        limit: int = 100,
        cursor: str | None = None,
        fetch_all: bool = False,
    ) -> list[Market]:
        """Search for markets.

        Args:
            series_ticker: Filter by series ticker.
            event_ticker: Filter by event ticker.
            status: Filter by market status. Pass None for all statuses.
            limit: Maximum results per page (default 100, max 1000).
            cursor: Pagination cursor for fetching next page.
            fetch_all: If True, automatically fetch all pages.
        """
        params = {
            "status": status.value if status is not None else None,
            "limit": limit,
            "series_ticker": series_ticker,
            "event_ticker": event_ticker,
            "cursor": cursor,
        }
        data = self.paginated_get("/markets", "markets", params, fetch_all)
        return [Market(self, MarketModel.model_validate(m)) for m in data]

    def get_event(self, event_ticker: str) -> Event:
        """Get an Event by ticker."""
        response = self.get(f"/events/{event_ticker}")
        data = response.get("event", response)
        model = EventModel.model_validate(data)
        return Event(self, model)

    def get_events(
        self,
        series_ticker: str | None = None,
        status: MarketStatus | None = None,
        limit: int = 100,
        cursor: str | None = None,
        fetch_all: bool = False,
    ) -> list[Event]:
        """Search for events.

        Args:
            series_ticker: Filter by series ticker.
            status: Filter by event status.
            limit: Maximum results per page (default 100).
            cursor: Pagination cursor for fetching next page.
            fetch_all: If True, automatically fetch all pages.
        """
        params = {
            "limit": limit,
            "series_ticker": series_ticker,
            "status": status.value if status is not None else None,
            "cursor": cursor,
        }
        data = self.paginated_get("/events", "events", params, fetch_all)
        return [Event(self, EventModel.model_validate(e)) for e in data]
