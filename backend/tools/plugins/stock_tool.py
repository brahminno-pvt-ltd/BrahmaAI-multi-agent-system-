"""
BrahmaAI Plugin Example: Stock Price Tool
Demonstrates how to build and register a custom tool plugin.

To enable this tool:
1. Copy this file to backend/tools/stock_tool.py
2. In backend/tools/registry.py, add:
      from backend.tools.stock_tool import StockPriceTool
      registry.register_class(StockPriceTool)
3. Restart the backend — the Planner will discover it automatically.

This example uses the free yfinance library. Install with:
    pip install yfinance
"""

import logging
from typing import Any

from backend.tools.registry import BaseTool

logger = logging.getLogger(__name__)


class StockPriceTool(BaseTool):
    """
    Stock Price Tool: Fetches real-time stock prices and basic financials.
    Uses yfinance (free, no API key required).
    """

    name = "stock_price"
    description = (
        "Look up current stock price, market cap, P/E ratio, and 52-week range "
        "for any publicly traded company by ticker symbol."
    )
    args = {
        "ticker":  "str: Stock ticker symbol (e.g. AAPL, MSFT, TSLA)",
        "period":  "str: History period — 1d, 5d, 1mo, 3mo, 1y (default: 1d)",
    }

    async def execute(
        self,
        ticker: str,
        period: str = "1d",
        **kwargs: Any,
    ) -> dict[str, Any]:
        ticker = ticker.upper().strip()
        logger.info(f"[StockPriceTool] Fetching: {ticker}")

        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)

            if hist.empty:
                return {
                    "status": "error",
                    "ticker": ticker,
                    "error": f"No data found for ticker: {ticker}",
                    "output": f"Could not find stock data for {ticker}. Check the ticker symbol.",
                }

            current_price = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            summary = {
                "ticker":        ticker,
                "name":          info.get("longName", ticker),
                "price":         round(current_price, 2),
                "change":        round(change, 2),
                "change_pct":    round(change_pct, 2),
                "currency":      info.get("currency", "USD"),
                "market_cap":    info.get("marketCap"),
                "pe_ratio":      info.get("trailingPE"),
                "52w_high":      info.get("fiftyTwoWeekHigh"),
                "52w_low":       info.get("fiftyTwoWeekLow"),
                "volume":        int(hist["Volume"].iloc[-1]),
                "avg_volume":    info.get("averageVolume"),
                "sector":        info.get("sector", "N/A"),
                "industry":      info.get("industry", "N/A"),
            }

            direction = "▲" if change >= 0 else "▼"
            output = (
                f"📈 {summary['name']} ({ticker})\n"
                f"Price: ${summary['price']} {direction} {summary['change']:+.2f} "
                f"({summary['change_pct']:+.2f}%)\n"
                f"Market Cap: ${summary['market_cap']:,.0f}\n" if summary['market_cap'] else ""
                f"P/E Ratio: {summary['pe_ratio']:.2f}\n" if summary['pe_ratio'] else ""
                f"52W Range: ${summary['52w_low']} – ${summary['52w_high']}\n"
                f"Volume: {summary['volume']:,}\n"
                f"Sector: {summary['sector']} · {summary['industry']}"
            )

            return {
                "status":  "success",
                "ticker":  ticker,
                "summary": summary,
                "output":  output,
            }

        except ImportError:
            return self._mock_response(ticker)
        except Exception as e:
            logger.error(f"[StockPriceTool] Error for {ticker}: {e}")
            return {
                "status": "error",
                "ticker": ticker,
                "error":  str(e),
                "output": f"Failed to fetch data for {ticker}: {e}",
            }

    def _mock_response(self, ticker: str) -> dict[str, Any]:
        """Demo response when yfinance is not installed."""
        return {
            "status": "success",
            "ticker": ticker,
            "output": (
                f"📈 {ticker} (Mock Data)\n"
                f"Price: $150.00 ▲ +2.50 (+1.69%)\n"
                f"Market Cap: $2,400,000,000,000\n"
                f"52W Range: $120.00 – $185.00\n"
                f"Note: Install yfinance for real data: pip install yfinance"
            ),
            "summary": {
                "ticker": ticker,
                "price": 150.0,
                "change": 2.5,
                "change_pct": 1.69,
                "note": "mock data — install yfinance",
            },
        }
