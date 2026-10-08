"""Pulls price history and fundamentals for the stock universe via yfinance.

Yahoo Finance aggressively blocks requests from cloud/datacenter IP ranges
(AWS, Azure, GitHub Actions, etc.) based on TLS fingerprint + rate, even for
single polite requests. curl_cffi's browser impersonation gets past this far
more reliably than plain `requests`/urllib3 (what yfinance uses by default).
"""
import time
import pandas as pd
import yfinance as yf
from curl_cffi import requests as curl_requests

from nifty50_symbols import NIFTY50


def to_yf_ticker(symbol: str) -> str:
    return f"{symbol}.NS"


def make_session():
    return curl_requests.Session(impersonate="chrome120")


def fetch_stock(symbol: str, retries: int = 3, backoff_sec: float = 5.0) -> dict | None:
    """Fetch price history + fundamentals for one NSE symbol. Returns None on
    repeated failure. Retries with backoff since yfinance rate-limits bursts
    of requests rather than rejecting individual symbols."""
    hist = None
    info = {}
    for attempt in range(retries):
        try:
            session = make_session()
            ticker = yf.Ticker(to_yf_ticker(symbol), session=session)
            hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
            if hist.empty or len(hist) < 60:
                return None
            info = ticker.info or {}
            break
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(backoff_sec * (attempt + 1))

    last_price = float(hist["Close"].iloc[-1])
    return {
        "symbol": symbol,
        "price": last_price,
        "history": hist,
        "trailing_pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": info.get("returnOnEquity"),
        "debt_to_equity": info.get("debtToEquity"),
        "earnings_growth": info.get("earningsGrowth"),
        "revenue_growth": info.get("revenueGrowth"),
        "market_cap": info.get("marketCap"),
        "sector": info.get("sector"),
        "name": info.get("longName", symbol),
    }


def fetch_universe(symbols: list[str] | None = None, pause_sec: float = 1.0) -> list[dict]:
    """Fetch all symbols in the universe, skipping failures. Rate-limited to be polite."""
    symbols = symbols or NIFTY50
    results = []
    for sym in symbols:
        data = fetch_stock(sym)
        if data is not None:
            results.append(data)
        time.sleep(pause_sec)
    return results
