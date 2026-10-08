"""Fetches the current Nifty 500 constituent list from NSE's official
archive (a plain CSV, not behind the Akamai bot-protection that blocks
option-chain and some other endpoints). Replaces the old hardcoded
Nifty 50 list so the universe stays current automatically."""
import io
import csv

NIFTY500_CSV_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"


def fetch_nifty500_symbols(session) -> list[str]:
    resp = session.get(NIFTY500_CSV_URL, timeout=15)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.text))
    return [row["Symbol"].strip() for row in reader if row.get("Symbol")]
