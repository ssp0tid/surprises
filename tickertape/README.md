# Tickertape

Terminal portfolio tracker for stocks and crypto.

## Installation

```bash
pip install -r requirements.txt
```

Make the script executable:

```bash
chmod +x tickertape.py
```

Or install as a command:

```bash
pip install -e .
```

## Usage

Add a holding:
```bash
python tickertape.py add AAPL --shares 50 --cost 7500
python tickertape.py add btc --shares 0.5 --cost 25000 --type crypto
python tickertape.py add AAPL --shares 25 --cost 5000 --notes "Tax loss harvest"
```

List holdings:
```bash
python tickertape.py list
python tickertape.py list --format json
python tickertape.py list --sort pnl
```

Remove a holding:
```bash
python tickertape.py remove AAPL
python tickertape.py remove btc --yes
```

Live dashboard:
```bash
python tickertape.py dashboard
python tickertape.py dashboard --refresh 10
python tickertape.py dashboard --compact
```

Export to CSV:
```bash
python tickertape.py export
python tickertape.py export --output my_portfolio.csv
python tickertape.py export --include-notes
```

## Data

Portfolio stored in `~/.tickertape/portfolio.json`
