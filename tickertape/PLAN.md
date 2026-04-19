# Tickertape - Terminal Portfolio Tracker

## Project Overview

**Purpose**: A terminal-based portfolio tracker with live dashboard showing stocks and crypto holdings.

**Tech Stack**:
- Python 3.10+
- `rich` - Terminal UI with colors, tables, sparklines
- `yfinance` - Stock/crypto price data (Yahoo Finance)
- `requests` - CoinGecko API for crypto prices
- `click` - CLI framework
- `requests-cache` - Rate limiting / caching

**Target Users**: Developers and traders who prefer terminal interfaces.

---

## File Structure

```
tickertape/
├── tickertape.py       # Single-file application (all logic)
├── requirements.txt    # Dependencies
├── README.md          # Usage documentation
└── ~/.tickertape/     # Data directory (auto-created)
    └── portfolio.json  # Portfolio data storage
```

---

## Data Models

### Portfolio JSON Schema (`~/.tickertape/portfolio.json`)

```json
{
  "version": "1.0",
  "holdings": [
    {
      "id": "uuid-v4",
      "type": "stock" | "crypto",
      "symbol": "AAPL" | "btc",
      "shares": 100.5,
      "cost_basis": 15000.00,
      "added_at": "2024-01-15T10:30:00Z",
      "notes": "optional notes"
    }
  ]
}
```

### In-Memory Holdings Record

```python
@dataclass
class Holding:
    id: str
    type: AssetType  # STOCK, CRYPTO
    symbol: str
    shares: float
    cost_basis: float
    added_at: datetime
    notes: str = ""

@dataclass
class HoldingWithQuote:
    holding: Holding
    current_price: float
    total_value: float
    pnl: float
    pnl_percent: float
    price_history: List[float]  # For sparkline
```

---

## CLI Commands

### `add` - Add a holding
```
tickertape add <symbol> --shares <qty> --cost <amount> [--type stock|crypto] [--notes <text>]

Examples:
  tickertape add AAPL --shares 50 --cost 7500
  tickertape add btc --shares 0.5 --cost 25000 --type crypto
```

**Behavior**:
- Validate symbol (basic regex check)
- Validate shares > 0
- Validate cost_basis >= 0
- Check for duplicate symbol, prompt to update or cancel
- Generate UUID for new holding
- Save to portfolio.json

### `remove` - Remove a holding
```
tickertape remove <symbol> [--yes]

Examples:
  tickertape remove AAPL
  tickertape remove btc --yes  # Skip confirmation
```

**Behavior**:
- Fuzzy match symbol (case-insensitive)
- Require `--yes` or confirm prompt to delete
- Remove from holdings list, re-save

### `list` - List all holdings
```
tickertape list [--format table|json] [--sort symbol|value|pnl]

Examples:
  tickertape list
  tickertape list --format json
  tickertape list --sort pnl
```

**Behavior**:
- Fetch live prices for all holdings
- Display table with: Symbol, Shares, Cost Basis, Current Price, Value, P&L
- Color-coded P&L (green/red)
- Sort by specified column

### `dashboard` - Live dashboard (default command)
```
tickertape dashboard [--refresh <seconds>] [--compact]

Examples:
  tickertape dashboard           # Default refresh every 5s
  tickertape dashboard --refresh 10
  tickertape dashboard --compact
```

**Behavior**:
- Auto-refresh loop (configurable interval)
- Shows live prices, P&L, sparklines
- Summary bar with total value and overall P&L
- Keyboard controls: `q` to quit, `r` to refresh now

### `export` - Export to CSV
```
tickertape export [--output <file.csv>] [--include-notes]

Examples:
  tickertape export
  tickertape export --output my_portfolio.csv
```

**Behavior**:
- Default filename: `portfolio_export_YYYYMMDD_HHMMSS.csv`
- Default location: current directory
- Columns: symbol, type, shares, cost_basis, current_price, value, pnl, pnl_percent, notes

---

## Dashboard Design

### Layout (Terminal ~80x24 minimum)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TICKERTAPE PORTFOLIO TRACKER                              [Ctrl+C] Quit     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SYMBOL   SHARES    COST      PRICE     VALUE      P&L        TREND        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  AAPL     50.00    $7,500   $182.50   $9,125    +$1,625     ▁▂▃▄▅▆▇        │
│           +21.67%                         (+21.67%)                          │
│                                                                             │
│  GOOGL   10.00    $1,500   $141.80   $1,418    -$82.00     ▇▆▅▄▃▂▁        │
│           -5.47%                          (-5.47%)                           │
│                                                                             │
│  BTC      0.50   $25,000  $43,250   $21,625   -$3,375     ▁▂▃▄▅▆▇        │
│          -13.50%                         (-13.50%)                           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ TOTAL VALUE: $32,168    TOTAL COST: $34,000    TOTAL P&L: -$1,832 (-5.39%) │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Color Scheme

| Element | Color | Rich Style |
|---------|-------|------------|
| Profit/P&L positive | Green | `color="green"` |
| Loss/P&L negative | Red | `color="red"` |
| Header row | Cyan/Bold | `color="cyan" bold=True` |
| Summary bar | Yellow | `color="yellow"` |
| Sparkline (up) | Green | `color="green"` |
| Sparkline (down) | Red | `color="red"` |
| Muted text | Dim | `style="dim"` |

### Sparkline Implementation

- Fetch 24-hour price history (or 7-day for crypto)
- For stocks: Use `yfinance` history with `period="7d"`
- For crypto: Use CoinGecko market chart data
- Render using `rich.sparkline.Sparkline` or custom ASCII art
- Truncate to last 15-20 data points for display

---

## API Integration

### Stock Prices (yfinance)

```python
import yfinance as yf

def get_stock_price(symbol: str) -> Tuple[float, List[float]]:
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    price = info.last_price

    # Get 7-day history for sparkline
    hist = ticker.history(period="7d")
    price_history = hist['Close'].tolist()[-20:]

    return price, price_history
```

**Rate Limits**: None (Yahoo Finance is generous), but implement 0.5s delay between requests.

### Crypto Prices (CoinGecko - Free Tier)

```python
import requests

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

def get_crypto_price(symbol: str) -> Tuple[float, List[float]]:
    # Symbol to ID mapping (common coins)
    symbol_map = {
        "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
        "doge": "dogecoin", "ada": "cardano", "xrp": "ripple"
    }

    coin_id = symbol_map.get(symbol.lower())
    if not coin_id:
        raise ValueError(f"Unknown crypto symbol: {symbol}")

    # Get current price
    url = f"{COINGECKO_BASE}/simple/price"
    params = {"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"}
    resp = requests.get(url, params=params)
    data = resp.json()
    price = data[coin_id]["usd"]

    # Get 7-day sparkline data
    url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
    resp = requests.get(url, params=params)
    prices = [p[1] for p in resp.json()["prices"]][-20:]

    return price, prices
```

**Rate Limits**: 10-50 calls/minute (free tier). Implement request caching (5-minute TTL).

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Invalid symbol | "Unknown symbol: XYZ. Please verify and try again." |
| API rate limit | "Rate limited. Waiting 60s..." with progress indicator |
| API timeout | Retry 3x with exponential backoff, then show cached/stale data |
| Network error | "Network error. Check connection." + offer to use cached prices |
| Empty portfolio | Show welcome message with `add` command hint |
| File permission error | "Cannot write to ~/.tickertape. Check permissions." |
| Invalid JSON in portfolio | Backup corrupt file, create fresh empty portfolio |

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Create `requirements.txt` with pinned versions
- [ ] Set up logging configuration
- [ ] Implement `Portfolio` class with JSON persistence
- [ ] Create data directory and portfolio.json initialization
- [ ] Implement `Holding` and `HoldingWithQuote` dataclasses

### Phase 2: CLI Foundation
- [ ] Set up Click CLI with main group and all commands
- [ ] Implement `add` command with validation
- [ ] Implement `remove` command with confirmation
- [ ] Implement `list` command with table output
- [ ] Implement `export` command with CSV generation

### Phase 3: Price Fetching
- [ ] Implement `StockPriceService` using yfinance
- [ ] Implement `CryptoPriceService` using CoinGecko
- [ ] Create unified `PriceService` interface
- [ ] Add request caching with TTL
- [ ] Implement retry logic with exponential backoff

### Phase 4: Dashboard
- [ ] Create dashboard layout with Rich Table
- [ ] Implement P&L calculation with colors
- [ ] Add sparkline rendering
- [ ] Implement auto-refresh loop
- [ ] Add keyboard controls (q=quit, r=refresh)
- [ ] Create summary statistics bar

### Phase 5: Polish
- [ ] Add proper error messages and exit codes
- [ ] Implement `--help` for all commands
- [ ] Add `--version` flag
- [ ] Create README.md with usage examples
- [ ] Add shell completion for symbols (optional)
- [ ] Implement `update` command to modify holdings

---

## Dependencies (requirements.txt)

```
click>=8.1.0
rich>=13.0.0
yfinance>=0.2.0
requests>=2.31.0
requests-cache>=1.1.0
```

---

## Key Implementation Details

### Auto-refresh Dashboard Loop

```python
import signal
import sys
from threading import Event

def run_dashboard(refresh_seconds=5):
    stop_event = Event()

    def handle_signal(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while not stop_event.is_set():
        clear_screen()
        fetch_and_render()
        time.sleep(refresh_seconds)
```

### Sparkline Rendering

```python
from rich.sparkline import Sparkline

def render_sparkline(prices: List[float]) -> str:
    if not prices:
        return "─" * 15
    data = (p - min(prices)) / (max(prices) - min(prices) + 0.001)
    return Sparkline(data)
```

### P&L Color Logic

```python
def get_pnl_style(pnl: float) -> Style:
    if pnl > 0:
        return Style(color="green", bold=True)
    elif pnl < 0:
        return Style(color="red", bold=True)
    return Style(dim=True)
```

---

## Testing Considerations

- Mock yfinance and CoinGecko responses for unit tests
- Test portfolio CRUD operations with temporary files
- Test error scenarios (network failure, invalid input)
- Test CSV export format correctness
- Manual testing on various terminal sizes

---

## Future Enhancements (Out of Scope for V1)

- Portfolio grouping/categorization
- Price alerts
- Transaction history
- Multiple portfolios
- Chart (bar/line) for portfolio over time
- International market support
