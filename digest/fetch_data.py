"""Pulls price history and fundamentals for the stock universe directly from
Yahoo Finance's public endpoints via curl_cffi (browser TLS impersonation).

We deliberately bypass the `yfinance` library's own session/cookie/crumb
handling: on Linux (including GitHub Actions runners) its internal cookie
parsing throws `'str' object has no attribute 'name'` when given a
curl_cffi session, a known incompatibility that does not reproduce on
Windows. Calling Yahoo's chart + quoteSummary endpoints ourselves avoids
that broken code path entirely and is simpler to reason about.
"""
import time
import pandas as pd
from curl_cffi import requests as curl_requests

from nifty50_symbols import NIFTY50

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
QUOTE_SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
COOKIE_WARMUP_URL = "https://fc.yahoo.com"


def to_yf_ticker(symbol: str) -> str:
    return f"{symbol}.NS"


def make_session():
    return curl_requests.Session(impersonate="chrome120")


def get_crumb(session) -> str:
    session.get(COOKIE_WARMUP_URL, timeout=10)
    resp = session.get(CRUMB_URL, timeout=10)
    resp.raise_for_status()
    return resp.text


def _raw(value):
    """Yahoo wraps numeric fields as {'raw': x, 'fmt': '...'}; unwrap them."""
    if isinstance(value, dict):
        return value.get("raw")
    return value


def fetch_chart(session, symbol: str) -> pd.DataFrame | None:
    url = CHART_URL.format(symbol=to_yf_ticker(symbol))
    resp = session.get(url, params={"range": "1y", "interval": "1d"}, timeout=15)
    if resp.status_code != 200:
        return None
    data = resp.json().get("chart", {})
    results = data.get("result")
    if not results:
        return None
    result = results[0]
    timestamps = result.get("timestamp")
    closes = result.get("indicators", {}).get("quote", [{}])[0].get("close")
    if not timestamps or not closes:
        return None
    df = pd.DataFrame({"Close": closes}, index=pd.to_datetime(timestamps, unit="s"))
    df = df.dropna()
    if len(df) < 60:
        return None
    return df


def fetch_fundamentals(session, crumb: str, symbol: str) -> dict:
    url = QUOTE_SUMMARY_URL.format(symbol=to_yf_ticker(symbol))
    params = {
        "modules": "defaultKeyStatistics,financialData,summaryDetail,price",
        "crumb": crumb,
    }
    resp = session.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        return {}
    results = resp.json().get("quoteSummary", {}).get("result")
    if not results:
        return {}
    r = results[0]
    financial = r.get("financialData", {})
    summary = r.get("summaryDetail", {})
    stats = r.get("defaultKeyStatistics", {})
    price_block = r.get("price", {})
    return {
        "trailing_pe": _raw(summary.get("trailingPE")),
        "pb": _raw(stats.get("priceToBook")),
        "roe": _raw(financial.get("returnOnEquity")),
        "debt_to_equity": _raw(financial.get("debtToEquity")),
        "earnings_growth": _raw(financial.get("earningsGrowth")),
        "revenue_growth": _raw(financial.get("revenueGrowth")),
        "market_cap": _raw(price_block.get("marketCap")),
        "name": price_block.get("longName") or price_block.get("shortName") or symbol,
    }


def fetch_stock(session, crumb: str, symbol: str, retries: int = 3, backoff_sec: float = 3.0) -> dict | None:
    for attempt in range(retries):
        try:
            hist = fetch_chart(session, symbol)
            if hist is None:
                return None
            fundamentals = fetch_fundamentals(session, crumb, symbol)
            last_price = float(hist["Close"].iloc[-1])
            return {
                "symbol": symbol,
                "price": last_price,
                "history": hist,
                "name": symbol,
                "sector": None,
                **fundamentals,
            }
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(backoff_sec * (attempt + 1))


def fetch_universe(symbols: list[str] | None = None, pause_sec: float = 0.5) -> list[dict]:
    """Fetch all symbols in the universe, skipping failures."""
    symbols = symbols or NIFTY50
    session = make_session()
    crumb = get_crumb(session)
    results = []
    for sym in symbols:
        data = fetch_stock(session, crumb, sym)
        if data is not None:
            results.append(data)
        time.sleep(pause_sec)
    return results
