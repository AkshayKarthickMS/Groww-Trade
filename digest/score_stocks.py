"""Scores stocks on technical + fundamental signals. Produces a ranked heuristic
list with visible reasoning. This is NOT a prediction of future winners —
see README for what this score can and can't tell you.
"""
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi_series = 100 - (100 / (1 + rs))
    return float(rsi_series.iloc[-1]) if not rsi_series.empty else float("nan")


def technical_signals(hist: pd.DataFrame) -> dict:
    close = hist["Close"]
    ma50 = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
    last = close.iloc[-1]
    momentum_1m = (last / close.iloc[-21] - 1) * 100 if len(close) > 21 else None
    return {
        "rsi14": rsi(close),
        "above_ma50": bool(last > ma50) if pd.notna(ma50) else None,
        "above_ma200": bool(last > ma200) if ma200 is not None and pd.notna(ma200) else None,
        "momentum_1m_pct": momentum_1m,
    }


def fundamental_score(stock: dict) -> tuple[float, list[str]]:
    """Returns (score 0-100, reasons). Simple weighted heuristic, fully transparent."""
    score = 50.0
    reasons = []

    pe = stock.get("trailing_pe")
    if pe is not None and pe > 0:
        if pe < 20:
            score += 10
            reasons.append(f"P/E {pe:.1f} is reasonably low")
        elif pe > 50:
            score -= 10
            reasons.append(f"P/E {pe:.1f} is high (expensive relative to earnings)")

    roe = stock.get("roe")
    if roe is not None:
        if roe > 0.15:
            score += 10
            reasons.append(f"ROE {roe*100:.1f}% is strong")
        elif roe < 0.05:
            score -= 10
            reasons.append(f"ROE {roe*100:.1f}% is weak")

    dte = stock.get("debt_to_equity")
    if dte is not None:
        if dte < 50:
            score += 5
            reasons.append(f"Debt/Equity {dte:.0f} is low")
        elif dte > 150:
            score -= 10
            reasons.append(f"Debt/Equity {dte:.0f} is high (leverage risk)")

    eg = stock.get("earnings_growth")
    if eg is not None:
        if eg > 0.15:
            score += 10
            reasons.append(f"Earnings growing {eg*100:.1f}% y/y")
        elif eg < 0:
            score -= 10
            reasons.append(f"Earnings declined {eg*100:.1f}% y/y")

    return score, reasons


def technical_score(tech: dict) -> tuple[float, list[str]]:
    score = 50.0
    reasons = []

    r = tech.get("rsi14")
    if r is not None and r == r:  # not NaN
        if r < 30:
            score += 10
            reasons.append(f"RSI {r:.0f} suggests oversold (possible bounce, also possible falling knife)")
        elif r > 70:
            score -= 10
            reasons.append(f"RSI {r:.0f} suggests overbought")

    if tech.get("above_ma200"):
        score += 10
        reasons.append("Price above 200-day average (long-term uptrend)")
    elif tech.get("above_ma200") is False:
        score -= 5
        reasons.append("Price below 200-day average (long-term downtrend)")

    m = tech.get("momentum_1m_pct")
    if m is not None:
        if m > 5:
            score += 5
            reasons.append(f"Up {m:.1f}% over last month (momentum)")
        elif m < -10:
            score -= 5
            reasons.append(f"Down {m:.1f}% over last month")

    return score, reasons


def score_universe(stocks: list[dict], max_price: float = 500.0) -> list[dict]:
    """Filters by price cap, scores each stock, returns sorted list (best first)."""
    ranked = []
    for s in stocks:
        if s["price"] > max_price:
            continue
        tech = technical_signals(s["history"])
        f_score, f_reasons = fundamental_score(s)
        t_score, t_reasons = technical_score(tech)
        total = round((f_score + t_score) / 2, 1)
        ranked.append({
            **s,
            "technical": tech,
            "score": total,
            "reasons": f_reasons + t_reasons,
        })
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked
