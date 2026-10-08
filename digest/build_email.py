"""Builds the HTML email body from scored stocks."""
from datetime import date

DISCLAIMER = (
    "This is an automated heuristic screen based on public technical and fundamental "
    "data (Yahoo Finance / NSE). It is NOT investment advice, NOT a prediction of future "
    "performance, and does NOT guarantee any return. Scores are transparent weighted "
    "formulas you can inspect in score_stocks.py — they rank today's data, they do "
    "not know the future. Markets carry real risk of loss. You are responsible for "
    "every decision you make with this information."
)


def render_stock_row(stock: dict) -> str:
    reasons_html = "".join(f"<li>{r}</li>" for r in stock["reasons"])
    return f"""
    <tr style="border-bottom:1px solid #ddd;">
      <td style="padding:8px;"><b>{stock['symbol']}</b><br><span style="color:#666;font-size:12px;">{stock.get('name','')}</span></td>
      <td style="padding:8px;">₹{stock['price']:.2f}</td>
      <td style="padding:8px;"><b>{stock['score']}</b>/100</td>
      <td style="padding:8px;"><ul style="margin:0;padding-left:18px;font-size:13px;">{reasons_html}</ul></td>
    </tr>
    """


def build_html(ranked_stocks: list[dict], universe_note: str, top_n: int = 25) -> str:
    today = date.today().isoformat()
    top = ranked_stocks[:top_n]

    if top:
        rows = "".join(render_stock_row(s) for s in top)
        stock_table = f"""
        <table style="width:100%;border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;">
          <thead>
            <tr style="background:#f0f0f0;text-align:left;">
              <th style="padding:8px;">Stock</th><th style="padding:8px;">Price</th>
              <th style="padding:8px;">Score</th><th style="padding:8px;">Why</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        """
    else:
        stock_table = (
            "<p><i>No stocks in the scanned universe passed the ₹500 price filter today.</i></p>"
        )

    return f"""
    <html><body style="font-family:Arial,sans-serif;">
      <h2>Daily Market Digest — {today}</h2>
      <p style="background:#fff3cd;border:1px solid #ffeeba;padding:10px;border-radius:6px;">
        <b>Disclaimer:</b> {DISCLAIMER}
      </p>
      <p style="color:#666;font-size:13px;">{universe_note}</p>

      <h3>Stock Screen (price ≤ ₹500, ranked by heuristic score, top {top_n})</h3>
      {stock_table}
    </body></html>
    """
