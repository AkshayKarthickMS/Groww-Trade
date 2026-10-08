"""Orchestrates the daily digest: fetch -> score -> build email -> send."""
import sys

from fetch_data import fetch_universe
from score_stocks import score_universe
from build_email import build_html
from send_email import send_digest_email

MAX_PRICE = 500.0


def main(dry_run: bool = False) -> None:
    print("Fetching stock universe (Nifty 500)...")
    stocks = fetch_universe()
    print(f"Fetched {len(stocks)} stocks successfully.")

    ranked = score_universe(stocks, max_price=MAX_PRICE)
    print(f"{len(ranked)} stocks priced <= Rs.{MAX_PRICE:.0f}.")

    universe_note = (
        f"Scanned {len(stocks)} Nifty 500 stocks; {len(ranked)} passed the "
        f"₹{MAX_PRICE:.0f} price filter."
    )
    html = build_html(ranked, universe_note)

    if dry_run:
        with open("preview.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Dry run: wrote preview.html instead of sending email.")
        return

    print("Sending email...")
    send_digest_email(html)
    print("Done.")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
