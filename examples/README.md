# Examples

Runnable examples demonstrating the `pykalshi` library.

## Setup

1. Install the library:
   ```bash
   pip install pykalshi
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
| `momentum_bot.py` | Simple momentum trading bot |

## Running

```bash
python examples/basic_usage.py
python examples/stream_orderbook.py
python examples/place_order.py
```

## Demo Environment

For testing without real money, use Kalshi's demo environment. Create credentials at [demo.kalshi.com](https://demo.kalshi.com), then set up `.env`:

```
KALSHI_API_KEY_ID=your-demo-key-id
KALSHI_PRIVATE_KEY_PATH=/path/to/demo-private-key.pem
```

```python
client = KalshiClient.from_env(demo=True)
```
