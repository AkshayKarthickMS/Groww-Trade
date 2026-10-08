# Daily Market Digest

An automated email that screens Nifty 50 stocks priced at or below ₹500 using
public technical (RSI, moving averages, momentum) and fundamental (P/E, ROE,
debt/equity, earnings growth) data, plus a best-effort upcoming-IPO list.
Runs every weekday morning via GitHub Actions and emails you the results.

## What this is — and isn't

- This is a **transparent heuristic ranking**, not a prediction engine. Every
  score is a weighted formula you can read in `digest/score_stocks.py`.
- It does **not** place trades. It only emails you information — you decide
  everything in Groww yourself.
- Short-term trading carries real risk of loss. Nothing here guarantees a
  return, and past technical/fundamental signals do not reliably predict
  short-term price moves. Treat this as one input, not a verdict.
- The ₹500 price cap is a personal budget filter, not a value indicator —
  see the P/E and ROE figures in the email for actual valuation signals.

## One-time setup

### 1. Generate a Gmail App Password
You cannot use your normal Gmail password for this — Google requires a
dedicated "app password" for scripts.
1. Go to https://myaccount.google.com/apppasswords
2. If prompted, enable 2-Step Verification first (required for app passwords).
3. Create an app password named "market-digest". Copy the 16-character code.

### 2. Create a GitHub repository
```
git init
git add .
git commit -m "Initial commit: daily market digest agent"
```
Then create a **private** repo on github.com and push:
```
git remote add origin https://github.com/<your-username>/<repo-name>.git
git branch -M main
git push -u origin main
```

### 3. Add secrets to the GitHub repo
In the repo: Settings → Secrets and variables → Actions → New repository secret.
Add three secrets:
- `GMAIL_ADDRESS` = akshaykarthick486@gmail.com
- `GMAIL_APP_PASSWORD` = the 16-character app password from step 1
- `DIGEST_RECIPIENT` = akshaykarthick486@gmail.com (or wherever you want it sent)

### 4. Test it
Go to the repo's "Actions" tab → "Daily Market Digest" workflow →
"Run workflow" (manual trigger) to send yourself a test email immediately,
without waiting for the 7 AM schedule.

## Running locally (optional, for testing before pushing)
```
pip install -r requirements.txt
cd digest
set GMAIL_ADDRESS=youremail@gmail.com
set GMAIL_APP_PASSWORD=your16charcode
python main.py --dry-run   # writes preview.html instead of emailing
python main.py             # actually sends the email
```

## Adjusting the scope
- Universe: edit `digest/nifty50_symbols.py` to add/remove symbols, or widen
  to Nifty 500 if the ₹500 filter leaves too few results (most Nifty 50
  stocks trade above ₹500, so expect a short list some days).
- Price cap: `MAX_PRICE` in `digest/main.py`.
- Schedule: the cron line in `.github/workflows/daily_digest.yml`.
- Scoring weights: `digest/score_stocks.py` — every weight is a plain number
  you can change and see the effect of immediately.
