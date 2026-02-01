import os
import sys
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Ensure we can import kalshi_api from project root
# This assumes the server is run from the project root
sys.path.append(os.getcwd())

from kalshi_api.client import KalshiClient
from kalshi_api.models import MarketModel, OrderbookResponse, BalanceModel, EventModel
from kalshi_api.enums import MarketStatus
from kalshi_api.exceptions import KalshiAPIError

load_dotenv()

app = FastAPI(title="Kalshi UI Backend")

# Serve React App
@app.get("/")
async def read_index():
    return FileResponse('web/frontend/index.html')

@app.get("/app.jsx")
async def read_app_jsx():
    return FileResponse('web/frontend/app.jsx')

# Configure CORS for local React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: Optional[KalshiClient] = None

@app.on_event("startup")
async def startup_event():
    global client
    try:
        # Initialize client with env vars
        client = KalshiClient()
        print("Successfully authenticated with Kalshi API")
    except Exception as e:
        print(f"Failed to initialize KalshiClient: {e}")
        # Doing this so we can at least return a 500 with a message

def get_client() -> KalshiClient:
    if not client:
        raise HTTPException(status_code=503, detail="Kalshi Client not initialized. Check server logs/credentials.")
    return client

@app.get("/api/balance", response_model=BalanceModel)
def get_balance():
    c = get_client()
    try:
        return c.portfolio.balance
    except KalshiAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.get("/api/markets", response_model=List[MarketModel])
def list_markets(limit: int = 100, status: str = "open", ticker: Optional[str] = None):
    c = get_client()
    try:
        # Convert string status to Enum
        market_status = None
        if status.lower() != "all":
            try:
                market_status = MarketStatus(status)
            except ValueError:
                pass 
        
        # 1. Fetch a larger pool to find active markets
        # Many markets have 0 volume, so we need to fetch enough to find the "alive" ones.
        raw_limit = 1000 
        markets = c.get_markets(limit=raw_limit, status=market_status)
        
        market_data = [m.data for m in markets]
        
        # 2. Filter for Active Markets
        # We only keep volume/OI check to avoid truly dead/empty slots
        filtered_markets = []
        for m in market_data:
            # Skip if Volume and OI are both 0/None
            has_vol = (m.volume and m.volume > 0) or (m.volume_24h and m.volume_24h > 0)
            has_oi = (m.open_interest and m.open_interest > 0)
            if not (has_vol or has_oi):
               continue
            
            filtered_markets.append(m)

        market_data = filtered_markets

        # 3. Sort by Volume (Descending)
        # Prioritize 24h volume for "Hot" markets, then total volume
        market_data.sort(key=lambda m: (m.volume_24h or 0, m.volume or 0), reverse=True)
        
        # 4. Filter by Ticker if requested
        if ticker:
            ticker_lower = ticker.lower()
            market_data = [m for m in market_data if ticker_lower in m.ticker.lower()]
            
        return market_data[:limit]
    except KalshiAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.get("/api/markets/{ticker}", response_model=MarketModel)
def get_market_detail(ticker: str):
    c = get_client()
    try:
        market = c.get_market(ticker)
        return market.data
    except KalshiAPIError as e:
        # If market not found, try looking up as Series or Event ticker
        # This handles cases like ?ticker=KXSB (Series) or ?ticker=KXSB-26 (Event)
        # We redirect" effectively by returning the first market.
        if e.status_code == 404:
            try:
                # Try Series Ticker first
                markets = c.get_markets(series_ticker=ticker)
                if markets:
                     return markets[0].data
                
                # Try Event Ticker
                markets = c.get_markets(event_ticker=ticker)
                if markets:
                     return markets[0].data
            except Exception:
                pass # Fall back to raising original 404
                
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.get("/api/markets/{ticker}/orderbook", response_model=OrderbookResponse)
def get_market_orderbook(ticker: str):
    c = get_client()
    try:
        # We need to resolve the ticker first in case it's a series/event ticker
        real_ticker = ticker
        try:
             # Quick check if it's a valid market ticker (optimization: skip if we knew format)
             c.get_market(ticker)
        except KalshiAPIError as e:
             if e.status_code == 404:
                # Try to resolve to a real market ticker
                markets = c.get_markets(series_ticker=ticker)
                if not markets:
                    markets = c.get_markets(event_ticker=ticker)
                
                if markets:
                    real_ticker = markets[0].ticker
        
        market = c.get_market(real_ticker)
        return market.get_orderbook()
    except KalshiAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.get("/api/series", response_model=List[str])
def list_series():
    """
    Returns a list of unique series tickers found from active/recent events.
    """
    c = get_client()
    try:
        # Fetch a reasonable number of events to discover series
        # We try to get diverse events by just fetching recent ones
        events = c.get_events(limit=100, status=MarketStatus.OPEN)
        
        # Extract unique series tickers
        series = sorted(list(set(e.series_ticker for e in events if e.series_ticker)))
        return series
    except KalshiAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.get("/api/series/{series_ticker}/events", response_model=List[EventModel])
def list_series_events(series_ticker: str):
    c = get_client()
    try:
        events = c.get_events(series_ticker=series_ticker, limit=100)
        return [e.data for e in events]
    except KalshiAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@app.get("/api/events/{event_ticker}/markets", response_model=List[MarketModel])
def list_event_markets(event_ticker: str):
    c = get_client()
    try:
        markets = c.get_markets(event_ticker=event_ticker)
        return [m.data for m in markets]
    except KalshiAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
