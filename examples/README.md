# Examples

Runnable examples demonstrating the `kalshi-api` library.

## Setup

1. Install the library:
   ```bash
   pip install kalshi-api
   ```

2. Create a `.env` file with your Kalshi API credentials:
   ```
   KALSHI_API_KEY_ID=your-key-id
   KALSHI_PRIVATE_KEY_PATH=/path/to/private-key.key
   ```

   Get your API key from [kalshi.com](https://kalshi.com) → Account & Security → API Keys.

## Examples

| File | Description |
|------|-------------|
| `basic_usage.py` | Browse markets, check balance, view positions |
| `stream_orderbook.py` | Real-time WebSocket streaming |
| `place_order.py` | Place, modify, and cancel orders |

## Running

```bash
python examples/basic_usage.py
python examples/stream_orderbook.py
python examples/place_order.py
```

## Demo Environment

For testing without real money, use Kalshi's demo environment:

```python
client = KalshiClient(demo=True)
```

The demo environment has separate credentials - create them at [demo.kalshi.com](https://demo.kalshi.com).
