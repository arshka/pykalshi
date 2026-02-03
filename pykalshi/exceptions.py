from typing import Any


class KalshiError(Exception):
    """Base exception for all Kalshi API errors."""

    retryable: bool = False


class KalshiAPIError(KalshiError):
    """Raised when the API returns a non-200 response.

    Attributes:
        status_code: HTTP status code.
        message: Error message from the API.
        error_code: Kalshi-specific error code (e.g., "insufficient_balance").
        method: HTTP method of the failed request.
        endpoint: API endpoint path.
        request_body: Request payload (for POST/PUT), if available.
        response_body: Raw response body for debugging.
        retryable: Whether this error is safe to retry (e.g., 5xx, rate limits).
    """

    retryable = True  # 5xx errors are generally retryable

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str | None = None,
        *,
        method: str | None = None,
        endpoint: str | None = None,
        request_body: dict[str, Any] | None = None,
        response_body: dict[str, Any] | str | None = None,
    ):
        # Build informative message
        parts = [f"{status_code}: {message}"]
        if error_code:
            parts[0] = f"{status_code}: {message} ({error_code})"
        if method and endpoint:
            parts.append(f"[{method} {endpoint}]")

        super().__init__(" ".join(parts))

        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.method = method
        self.endpoint = endpoint
        self.request_body = request_body
        self.response_body = response_body

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"status_code={self.status_code}, "
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"endpoint={self.endpoint!r})"
        )


class AuthenticationError(KalshiAPIError):
    """Raised when authentication fails (401/403).

    Common causes:
    - Invalid or expired API key
    - Malformed signature
    - Clock skew (timestamp too old)
    """

    retryable = False


class InsufficientFundsError(KalshiAPIError):
    """Raised when the order cannot be placed due to insufficient funds.

    Check `request_body` for the order that was rejected.
    """

    retryable = False


class ResourceNotFoundError(KalshiAPIError):
    """Raised when a resource (market, order) is not found (404).

    Check `endpoint` to see which resource was not found.
    """

    retryable = False


class RateLimitError(KalshiAPIError):
    """Raised when rate limit retries are exhausted (429).

    Consider using a RateLimiter to proactively throttle requests.
    """

    retryable = True


class OrderRejectedError(KalshiAPIError):
    """Raised when an order is rejected by the exchange.

    Common causes:
    - Market is closed or settled
    - Invalid price (outside 1-99 range)
    - Self-trade prevention triggered
    - Post-only order would take liquidity

    Check `request_body` for the rejected order details.
    """

    retryable = False
