# Kalshi API

A modular Python client library for the Kalshi trading API.

## Features

- ✅ Query market data
- ✅ Fetch orderbooks
- ✅ Place and cancel orders
- ✅ Check portfolio balance

## Installation

```bash
# Clone and install
uv sync
source .venv/bin/activate
uv pip install -e .
```

## Configuration

Create a `.env` file with your API credentials:

```bash
KALSHI_API_KEY_ID=your-api-key-id
KALSHI_PRIVATE_KEY_PATH=/path/to/private-key.key
```

Get credentials at [kalshi.com](https://kalshi.com) → Account & Security → API Keys

## Usage

```python
from kalshi_api import KalshiClient
from kalshi_api.enums import Action, Side

# Initialize client (uses .env)
client = KalshiClient()
user = client.get_user()

# 1. Search markets
markets = client.get_markets(status="open", limit=10)
market = markets[0]

# 2. Get orderbook
orderbook = market.get_orderbook()

# 3. Place order
order = user.place_order(
    market,
    action=Action.BUY,
    side=Side.YES,
    count=1,
    price=10
)

# 4. Cancel order
order.cancel()
```

## Project Structure

```
kalshi/
├── kalshi_api/           # Package
│   ├── __init__.py       # Public API exports
│   ├── client.py         # KalshiClient (auth, HTTP)
│   ├── markets.py        # get_markets, get_orderbook
│   ├── orders.py         # place_order, cancel_order
│   ├── portfolio.py      # Portfolio management
│   └── models.py         # Pydantic models
├── tests/                # Unit tests
├── pyproject.toml
└── .env                  # Credentials (gitignored)
```

## API Docs

- [Full Library Documentation](kalshi_api/docs.md)
- [Official Kalshi API Reference](https://trading-api.readme.io/api-reference)
