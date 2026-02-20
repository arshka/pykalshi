import pytest
from unittest.mock import MagicMock
from pykalshi import KalshiClient


@pytest.fixture
def mock_response():
    """Helper to create a mock httpx.Response."""

    def _create(json_data, status_code=200, text=""):
        resp = MagicMock()
        resp.json.return_value = json_data
        resp.status_code = status_code
        resp.text = text
        resp.content = b"ok" if json_data else b""
        resp.headers = {}
        return resp

    return _create


@pytest.fixture
def client(mocker):
    """
    Returns a KalshiClient with mocked authentication and HTTP session.
    This allows testing without real keys or API calls.
    """
    # Mock private key loading and signing to avoid file I/O and crypto
    mocker.patch("pykalshi._base._BaseKalshiClient._load_private_key")
    mocker.patch(
        "pykalshi._base._BaseKalshiClient._sign_request",
        return_value=("1234567890", "fake_sig"),
    )

    # Mock httpx.Client to prevent network calls
    mocker.patch("httpx.Client")

    # Initialize client with dummy values
    c = KalshiClient(api_key_id="fake_key", private_key_path="fake_path", demo=True)
    return c
