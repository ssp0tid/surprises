#!/usr/bin/env python3
"""Tickertape - Terminal Portfolio Tracker"""

import csv
import json
import os
import signal
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import List, Optional, Tuple

import click
import requests
import yfinance as yf
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# ASCII sparkline characters (low to high)
SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def make_sparkline(prices: List[float], width: int = 12) -> str:
    """Create an ASCII sparkline from price data."""
    if not prices or len(prices) < 2:
        return "─" * width

    # Normalize prices to 0-8 range
    min_p = min(prices)
    max_p = max(prices)

    if max_p == min_p:
        return "─" * width

    normalized = [(p - min_p) / (max_p - min_p) * 8 for p in prices[-width:]]
    return "".join(SPARKLINE_CHARS[int(n)] for n in normalized)


console = Console()


# ============================================================
# Data Models
# ============================================================


class AssetType(Enum):
    STOCK = "stock"
    CRYPTO = "crypto"


class Holding:
    """Represents a single portfolio holding."""

    def __init__(
        self,
        id: str,
        type: AssetType,
        symbol: str,
        shares: float,
        cost_basis: float,
        added_at: str,
        notes: str = "",
    ):
        self.id = id
        self.type = type
        self.symbol = symbol.upper()
        self.shares = shares
        self.cost_basis = cost_basis
        self.added_at = added_at
        self.notes = notes

    @classmethod
    def from_dict(cls, data: dict) -> "Holding":
        return cls(
            id=data["id"],
            type=AssetType(data["type"]),
            symbol=data["symbol"],
            shares=float(data["shares"]),
            cost_basis=float(data["cost_basis"]),
            added_at=data["added_at"],
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "symbol": self.symbol,
            "shares": self.shares,
            "cost_basis": self.cost_basis,
            "added_at": self.added_at,
            "notes": self.notes,
        }


class HoldingWithQuote:
    """Holding enriched with current market data."""

    def __init__(
        self, holding: Holding, current_price: float, price_history: List[float]
    ):
        self.holding = holding
        self.current_price = current_price
        self.price_history = price_history
        self.total_value = current_price * holding.shares
        self.pnl = self.total_value - holding.cost_basis
        self.pnl_percent = (
            (self.pnl / holding.cost_basis * 100) if holding.cost_basis > 0 else 0.0
        )

    @property
    def symbol(self) -> str:
        return self.holding.symbol

    @property
    def shares(self) -> float:
        return self.holding.shares

    @property
    def cost_basis(self) -> float:
        return self.holding.cost_basis


# ============================================================
# Portfolio Storage
# ============================================================


class Portfolio:
    """Manages portfolio persistence to ~/.tickertape/portfolio.json"""

    VERSION = "1.0"

    def __init__(self):
        self.data_dir = Path.home() / ".tickertape"
        self.portfolio_file = self.data_dir / "portfolio.json"
        self.holdings: List[Holding] = []
        self._ensure_data_dir()
        self._load()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            console.print(
                f"[red]Error: Cannot create {self.data_dir}. Check permissions.[/red]"
            )
            sys.exit(1)

    def _load(self):
        """Load portfolio from JSON file."""
        if not self.portfolio_file.exists():
            self.holdings = []
            self._save()
            return

        try:
            with open(self.portfolio_file, "r") as f:
                data = json.load(f)

            if data.get("version") != self.VERSION:
                console.print(
                    f"[yellow]Warning: Portfolio version mismatch. Migrating...[/yellow]"
                )

            self.holdings = [Holding.from_dict(h) for h in data.get("holdings", [])]
        except json.JSONDecodeError:
            # Backup corrupt file and create fresh
            backup_name = f"{self.portfolio_file}.backup.{int(time.time())}"
            console.print(
                f"[yellow]Warning: Corrupt portfolio file. Backing up to {backup_name}[/yellow]"
            )
            self.portfolio_file.rename(backup_name)
            self.holdings = []
            self._save()
        except Exception as e:
            console.print(f"[red]Error loading portfolio: {e}[/red]")
            sys.exit(1)

    def _save(self):
        """Save portfolio to JSON file."""
        try:
            data = {
                "version": self.VERSION,
                "holdings": [h.to_dict() for h in self.holdings],
            }
            with open(self.portfolio_file, "w") as f:
                json.dump(data, f, indent=2)
        except PermissionError:
            console.print(
                f"[red]Error: Cannot write to {self.portfolio_file}. Check permissions.[/red]"
            )
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error saving portfolio: {e}[/red]")
            sys.exit(1)

    def add(self, holding: Holding):
        """Add a new holding to the portfolio."""
        # Check for duplicate
        for existing in self.holdings:
            if existing.symbol == holding.symbol:
                console.print(
                    f"[yellow]Symbol {holding.symbol} already exists.[/yellow]"
                )
                if click.confirm("Update existing holding?"):
                    existing.shares = holding.shares
                    existing.cost_basis = holding.cost_basis
                    existing.notes = holding.notes
                    self._save()
                    console.print(f"[green]Updated {holding.symbol}[/green]")
                    return
                else:
                    console.print("[yellow]Cancelled.[/yellow]")
                    return

        self.holdings.append(holding)
        self._save()
        console.print(f"[green]Added {holding.symbol}[/green]")

    def remove(self, symbol: str) -> bool:
        """Remove a holding by symbol (case-insensitive)."""
        symbol = symbol.upper()
        for i, holding in enumerate(self.holdings):
            if holding.symbol == symbol:
                removed = self.holdings.pop(i)
                self._save()
                console.print(f"[green]Removed {removed.symbol}[/green]")
                return True

        console.print(f"[red]Symbol {symbol} not found in portfolio.[/red]")
        return False

    def find_by_symbol(self, symbol: str) -> Optional[Holding]:
        """Find a holding by symbol (case-insensitive)."""
        symbol = symbol.upper()
        for holding in self.holdings:
            if holding.symbol == symbol:
                return holding
        return None

    def get_all(self) -> List[Holding]:
        """Get all holdings."""
        return self.holdings.copy()


# ============================================================
# Price Services
# ============================================================

# Crypto symbol to CoinGecko ID mapping
CRYPTO_SYMBOL_MAP = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "doge": "dogecoin",
    "ada": "cardano",
    "xrp": "ripple",
    "dot": "polkadot",
    "avax": "avalanche-2",
    "matic": "matic-network",
    "link": "chainlink",
    "uni": "uniswap",
    "atom": "cosmos",
    "ltc": "litecoin",
    "bch": "bitcoin-cash",
    "xlm": "stellar",
    "algo": "algorand",
    "vet": "vechain",
    "icp": "internet-computer",
    "fil": "filecoin",
    "trx": "tron",
    "etc": "ethereum-classic",
    "xmr": "monero",
    "aave": "aave",
    "mkr": "maker",
    "shib": "shiba-inu",
    "pepe": "pepe",
}

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# Rate limiting
_request_session = None
_last_request_time = 0
MIN_REQUEST_INTERVAL = 0.5  # seconds


def _rate_limit():
    """Apply rate limiting between API requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def _retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """Retry a function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2**attempt)
            console.print(f"[yellow]Request failed, retrying in {delay}s...[/yellow]")
            time.sleep(delay)


def get_stock_price(symbol: str) -> Tuple[float, List[float]]:
    """Fetch stock price and history using yfinance."""
    symbol = symbol.upper()

    def _fetch():
        _rate_limit()
        ticker = yf.Ticker(symbol)

        info = ticker.fast_info
        price = info.last_price

        if price is None or price <= 0:
            raise ValueError(f"Unable to get valid price for {symbol}")

        hist = ticker.history(period="7d")
        if hist.empty:
            return price, [price] * 20

        price_history = hist["Close"].dropna().tolist()
        if not price_history:
            return price, [price] * 20

        while len(price_history) < 20:
            price_history.insert(0, price_history[0])

        return price, price_history[-20:]

    return _retry_with_backoff(_fetch)


def get_crypto_price(symbol: str) -> Tuple[float, List[float]]:
    """Fetch crypto price and history using CoinGecko."""
    symbol = symbol.lower()

    coin_id = CRYPTO_SYMBOL_MAP.get(symbol)
    if not coin_id:
        raise ValueError(f"Unknown crypto symbol: {symbol}")

    def _fetch():
        _rate_limit()

        # Get current price
        url = f"{COINGECKO_BASE}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        resp = requests.get(url, params=params, timeout=10)

        if resp.status_code == 429:
            raise requests.exceptions.RequestException("Rate limited")

        resp.raise_for_status()
        data = resp.json()
        price = data[coin_id]["usd"]

        # Get 7-day sparkline data
        url = f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": "7", "interval": "hourly"}
        resp = requests.get(url, params=params, timeout=10)

        if resp.status_code == 429:
            raise requests.exceptions.RequestException("Rate limited")

        resp.raise_for_status()
        prices = resp.json().get("prices", [])
        if not prices:
            return price, [price] * 20
        price_history = [p[1] for p in prices]

        while len(price_history) < 20:
            price_history.insert(0, price_history[0])

        return price, price_history[-20:]

    return _retry_with_backoff(_fetch)


def get_price(holding: Holding) -> Tuple[float, List[float]]:
    """Fetch price for a holding based on its type."""
    if holding.type == AssetType.CRYPTO:
        return get_crypto_price(holding.symbol)
    else:
        return get_stock_price(holding.symbol)


def fetch_all_quotes(holdings: List[Holding]) -> List[HoldingWithQuote]:
    """Fetch quotes for all holdings."""
    results = []
    has_errors = False

    for holding in holdings:
        try:
            price, history = get_price(holding)
            results.append(HoldingWithQuote(holding, price, history))
        except Exception as e:
            console.print(f"[red]Error fetching {holding.symbol}: {e}[/red]")
            results.append(HoldingWithQuote(holding, 0.0, []))
            has_errors = True

    if has_errors:
        console.print("[dim]Some prices unavailable. Values may be incorrect.[/dim]")

    return results


# ============================================================
# CLI Commands
# ============================================================


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Tickertape - Terminal Portfolio Tracker"""
    pass


@cli.command()
@click.argument("symbol")
@click.option("--shares", type=float, required=True, help="Number of shares/coins")
@click.option("--cost", type=float, required=True, help="Total cost basis")
@click.option(
    "--type",
    "asset_type",
    type=click.Choice(["stock", "crypto"]),
    default="stock",
    help="Asset type",
)
@click.option("--notes", default="", help="Optional notes")
def add(symbol: str, shares: float, cost: float, asset_type: str, notes: str):
    """Add a holding to the portfolio."""
    # Input validation
    if shares <= 0:
        console.print("[red]Error: Shares must be greater than 0.[/red]")
        sys.exit(1)

    if cost < 0:
        console.print("[red]Error: Cost basis must be 0 or greater.[/red]")
        sys.exit(1)

    import re

    if not re.match(r"^[A-Za-z0-9.\-]{1,10}$", symbol):
        console.print("[red]Error: Invalid symbol format.[/red]")
        sys.exit(1)

    holding = Holding(
        id=str(uuid.uuid4()),
        type=AssetType.CRYPTO if asset_type == "crypto" else AssetType.STOCK,
        symbol=symbol.upper(),
        shares=shares,
        cost_basis=cost,
        added_at=datetime.now(datetime.UTC).isoformat(),
        notes=notes,
    )

    portfolio = Portfolio()
    portfolio.add(holding)


@cli.command()
@click.argument("symbol")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def remove(symbol: str, yes: bool):
    """Remove a holding from the portfolio."""
    if not yes:
        if not click.confirm(f"Remove {symbol.upper()} from portfolio?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return

    portfolio = Portfolio()
    if not portfolio.remove(symbol):
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--sort",
    type=click.Choice(["symbol", "value", "pnl"]),
    default="symbol",
    help="Sort by",
)
def list(output_format: str, sort: str):
    """List all holdings with current values."""
    portfolio = Portfolio()
    holdings = portfolio.get_all()

    if not holdings:
        console.print(
            "[yellow]Portfolio is empty. Use 'tickertape add' to add holdings.[/yellow]"
        )
        return

    # Fetch quotes
    quotes = fetch_all_quotes(holdings)

    # Sort
    if sort == "value":
        quotes.sort(key=lambda q: q.total_value, reverse=True)
    elif sort == "pnl":
        quotes.sort(key=lambda q: q.pnl, reverse=True)
    else:
        quotes.sort(key=lambda q: q.symbol)

    if output_format == "json":
        data = []
        for q in quotes:
            data.append(
                {
                    "symbol": q.symbol,
                    "type": q.holding.type.value,
                    "shares": q.shares,
                    "cost_basis": q.cost_basis,
                    "current_price": q.current_price,
                    "value": q.total_value,
                    "pnl": q.pnl,
                    "pnl_percent": q.pnl_percent,
                    "notes": q.holding.notes,
                }
            )
        console.print_json(json.dumps(data))
    else:
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Symbol", style="white")
        table.add_column("Shares", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Value", justify="right")
        table.add_column("P&L", justify="right")

        for q in quotes:
            pnl_style = "green" if q.pnl > 0 else "red" if q.pnl < 0 else "dim"
            pnl_text = f"${q.pnl:,.2f} ({q.pnl_percent:+.2f}%)"

            table.add_row(
                q.symbol,
                f"{q.shares:.2f}",
                f"${q.cost_basis:,.2f}",
                f"${q.current_price:,.2f}",
                f"${q.total_value:,.2f}",
                Text(pnl_text, style=pnl_style),
            )

        console.print(table)

        # Summary
        total_value = sum(q.total_value for q in quotes)
        total_cost = sum(q.cost_basis for q in quotes)
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        pnl_style = "green" if total_pnl > 0 else "red" if total_pnl < 0 else "dim"
        console.print(f"\n[bold]Total Value:[/bold] ${total_value:,.2f}")
        console.print(f"[bold]Total Cost:[/bold] ${total_cost:,.2f}")
        console.print(
            Text(
                f"[bold]Total P&L:[/bold] ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%)",
                style=pnl_style,
            )
        )


@cli.command()
@click.option("--refresh", type=int, default=5, help="Refresh interval in seconds")
@click.option("--compact", is_flag=True, help="Compact view")
def dashboard(refresh: int, compact: bool):
    """Live dashboard with auto-refresh."""
    portfolio = Portfolio()
    holdings = portfolio.get_all()

    if not holdings:
        console.print(
            "[yellow]Portfolio is empty. Use 'tickertape add' to add holdings.[/yellow]"
        )
        return

    stop_event = False

    def signal_handler(signum, frame):
        nonlocal stop_event
        stop_event = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while not stop_event:
        # Clear screen
        console.clear()

        # Header
        console.print("[bold cyan]TICKERTAPE PORTFOLIO TRACKER[/bold cyan]")
        console.print("[dim]Press 'q' to quit, 'r' to refresh[/dim]\n")

        # Fetch quotes
        quotes = fetch_all_quotes(holdings)

        if compact:
            # Compact table
            table = Table(show_header=True, box=None)
            table.add_column("Sym")
            table.add_column("Shares", justify="right")
            table.add_column("Value", justify="right")
            table.add_column("P&L", justify="right")

            for q in quotes:
                pnl_style = "green" if q.pnl > 0 else "red" if q.pnl < 0 else "dim"
                pnl_text = f"${q.pnl:+.0f}"

                # Mini sparkline
                spark = ""
                if len(q.price_history) >= 2:
                    trend = "▲" if q.price_history[-1] >= q.price_history[0] else "▼"
                    spark = f" [{trend}]"

                table.add_row(
                    q.symbol,
                    f"{q.shares:.2f}",
                    f"${q.total_value:,.0f}",
                    Text(pnl_text + spark, style=pnl_style),
                )

            console.print(table)
        else:
            # Full table with sparklines
            table = Table(show_header=True)
            table.add_column("Symbol")
            table.add_column("Shares", justify="right")
            table.add_column("Cost", justify="right")
            table.add_column("Price", justify="right")
            table.add_column("Value", justify="right")
            table.add_column("P&L", justify="right")
            table.add_column("Trend")

            for q in quotes:
                pnl_style = "green" if q.pnl > 0 else "red" if q.pnl < 0 else "dim"
                pnl_text = f"${q.pnl:,.2f}\n({q.pnl_percent:+.2f}%)"

                sparkline = make_sparkline(q.price_history, width=12)
                trend_color = (
                    "green"
                    if q.price_history and q.price_history[-1] >= q.price_history[0]
                    else "dim"
                )

                table.add_row(
                    q.symbol,
                    f"{q.shares:.2f}",
                    f"${q.cost_basis:,.2f}",
                    f"${q.current_price:,.2f}",
                    f"${q.total_value:,.2f}",
                    Text(pnl_text, style=pnl_style),
                    Text(sparkline, style=trend_color),
                )

            console.print(table)

        # Summary bar
        total_value = sum(q.total_value for q in quotes)
        total_cost = sum(q.cost_basis for q in quotes)
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        pnl_style = "green" if total_pnl > 0 else "red" if total_pnl < 0 else "dim"
        summary = f"TOTAL: ${total_value:,.2f} | Cost: ${total_cost:,.2f} | P&L: "
        summary += Text(f"${total_pnl:,.2f} ({total_pnl_pct:+.2f}%)", style=pnl_style)
        console.print(Panel(summary, style="yellow"))

        # Check for quit
        try:
            if console.input("\nPress 'q' to quit, Enter to refresh...") == "q":
                break
        except:
            break

        time.sleep(refresh)


@cli.command()
@click.option("--output", type=click.Path(), help="Output CSV file")
@click.option("--include-notes", is_flag=True, help="Include notes column")
def export(output: Optional[str], include_notes: bool):
    """Export portfolio to CSV."""
    portfolio = Portfolio()
    holdings = portfolio.get_all()

    if not holdings:
        console.print("[yellow]Portfolio is empty. Nothing to export.[/yellow]")
        return

    # Fetch quotes
    quotes = fetch_all_quotes(holdings)

    # Default filename
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"portfolio_export_{timestamp}.csv"

    # Build CSV
    fieldnames = [
        "symbol",
        "type",
        "shares",
        "cost_basis",
        "current_price",
        "value",
        "pnl",
        "pnl_percent",
    ]
    if include_notes:
        fieldnames.append("notes")

    try:
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for q in quotes:
                row = {
                    "symbol": q.symbol,
                    "type": q.holding.type.value,
                    "shares": q.shares,
                    "cost_basis": q.cost_basis,
                    "current_price": q.current_price,
                    "value": q.total_value,
                    "pnl": q.pnl,
                    "pnl_percent": q.pnl_percent,
                }
                if include_notes:
                    row["notes"] = q.holding.notes

                writer.writerow(row)

        console.print(f"[green]Exported to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error exporting: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
