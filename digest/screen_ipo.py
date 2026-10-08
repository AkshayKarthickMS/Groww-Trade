"""Best-effort fetch of upcoming/current NSE IPOs from public NSE endpoints.
NSE's site actively rate-limits/blocks bots, so this frequently returns
nothing — the email will say so explicitly rather than silently omit it.
"""
import requests

NSE_HOME = "https://www.nseindia.com"
NSE_IPO_API = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def fetch_upcoming_ipos() -> dict:
    """Returns {'ok': bool, 'ipos': [...], 'note': str}."""
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get(NSE_HOME, timeout=10)  # warm up cookies
        resp = session.get(NSE_IPO_API, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        ipos = data if isinstance(data, list) else data.get("data", [])
        # NSE's "ipo" category also includes debt/bond issues (series "DEBT") —
        # filter to equity issues (series "EQ" or "SME") since those are what
        # an equity investor actually means by "IPO".
        equity_ipos = [i for i in ipos if i.get("series") in ("EQ", "SME")]
        return {"ok": True, "ipos": equity_ipos, "note": ""}
    except Exception as e:
        return {
            "ok": False,
            "ipos": [],
            "note": f"IPO data unavailable today (NSE blocked/changed the endpoint: {e}). "
                    f"Check groww.in/ipo manually for current listings.",
        }
