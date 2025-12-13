#!/usr/bin/env python3
"""
5-Pillar Stock Scanner
Based on Ross Cameron's Warrior Trading Strategy

Scans for stocks that meet all 5 criteria:
1. Price: $2-$20 (adjustable for small accounts)
2. Float: Under 20M shares (preferably under 5M)
3. Relative Volume: 5x above average
4. Percentage Gain: Up at least 10%
5. News Catalyst: Breaking news (manual verification)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import List, Dict
import json

class FivePillarScanner:
    def __init__(self,
                 min_price: float = 2.0,
                 max_price: float = 20.0,
                 max_float: float = 20_000_000,
                 min_rel_volume: float = 5.0,
                 min_gain_percent: float = 10.0):
        """
        Initialize scanner with 5-pillar criteria

        Args:
            min_price: Minimum stock price (default $2)
            max_price: Maximum stock price (default $20)
            max_float: Maximum float in shares (default 20M)
            min_rel_volume: Minimum relative volume multiplier (default 5x)
            min_gain_percent: Minimum percentage gain (default 10%)
        """
        self.min_price = min_price
        self.max_price = max_price
        self.max_float = max_float
        self.min_rel_volume = min_rel_volume
        self.min_gain_percent = min_gain_percent

    def get_stock_data(self, ticker: str) -> Dict:
        """Fetch stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="5d")

            if hist.empty or len(hist) < 2:
                return None

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]

            # Calculate percentage change
            pct_change = ((current_price - prev_close) / prev_close) * 100

            # Get volume data
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].iloc[:-1].mean()
            rel_volume = current_volume / avg_volume if avg_volume > 0 else 0

            # Get float (shares outstanding)
            float_shares = info.get('floatShares', info.get('sharesOutstanding', float('inf')))

            return {
                'ticker': ticker,
                'price': current_price,
                'pct_change': pct_change,
                'volume': current_volume,
                'avg_volume': avg_volume,
                'rel_volume': rel_volume,
                'float': float_shares,
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'name': info.get('longName', ticker)
            }
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def meets_criteria(self, stock_data: Dict) -> tuple[bool, List[str]]:
        """
        Check if stock meets all 5 pillar criteria

        Returns:
            tuple: (passes, list of failed criteria)
        """
        if not stock_data:
            return False, ["No data available"]

        failed = []

        # Pillar 1: Price Range
        if not (self.min_price <= stock_data['price'] <= self.max_price):
            failed.append(f"Price ${stock_data['price']:.2f} not in range ${self.min_price}-${self.max_price}")

        # Pillar 2: Float
        if stock_data['float'] > self.max_float:
            failed.append(f"Float {stock_data['float']/1_000_000:.1f}M exceeds {self.max_float/1_000_000:.1f}M")

        # Pillar 3: Relative Volume
        if stock_data['rel_volume'] < self.min_rel_volume:
            failed.append(f"Rel Volume {stock_data['rel_volume']:.1f}x below {self.min_rel_volume}x")

        # Pillar 4: Percentage Gain
        if stock_data['pct_change'] < self.min_gain_percent:
            failed.append(f"Gain {stock_data['pct_change']:.1f}% below {self.min_gain_percent}%")

        # Pillar 5: News - requires manual verification
        # This is flagged for user to check

        passes = len(failed) == 0
        return passes, failed

    def scan_watchlist(self, tickers: List[str]) -> pd.DataFrame:
        """
        Scan a list of tickers for 5-pillar criteria

        Args:
            tickers: List of stock ticker symbols

        Returns:
            DataFrame of stocks that pass the scan
        """
        results = []

        print(f"\n{'='*80}")
        print(f"5-PILLAR SCANNER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"Criteria:")
        print(f"  • Price: ${self.min_price} - ${self.max_price}")
        print(f"  • Float: < {self.max_float/1_000_000:.0f}M shares")
        print(f"  • Rel Volume: > {self.min_rel_volume}x")
        print(f"  • Gain: > {self.min_gain_percent}%")
        print(f"  • News: Manual verification required")
        print(f"{'='*80}\n")

        for ticker in tickers:
            print(f"Scanning {ticker}...", end=" ")
            stock_data = self.get_stock_data(ticker)

            if stock_data:
                passes, failed = self.meets_criteria(stock_data)

                if passes:
                    print("✓ PASSED ALL PILLARS")
                    stock_data['status'] = 'PASS'
                    stock_data['failed_criteria'] = ''
                    results.append(stock_data)
                else:
                    print(f"✗ Failed: {', '.join(failed)}")
            else:
                print("✗ No data")

        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('pct_change', ascending=False)
            return df
        else:
            return pd.DataFrame()

    def display_results(self, df: pd.DataFrame):
        """Display scan results in a formatted table"""
        if df.empty:
            print("\n❌ No stocks met the 5-pillar criteria")
            return

        print(f"\n{'='*80}")
        print(f"✅ {len(df)} STOCK(S) PASSED THE 5-PILLAR SCAN")
        print(f"{'='*80}\n")

        for idx, row in df.iterrows():
            print(f"🎯 {row['ticker']} - {row['name']}")
            print(f"   Price: ${row['price']:.2f}")
            print(f"   Gain: +{row['pct_change']:.2f}%")
            print(f"   Float: {row['float']/1_000_000:.2f}M shares")
            print(f"   Rel Volume: {row['rel_volume']:.2f}x")
            print(f"   Volume: {row['volume']:,.0f} (Avg: {row['avg_volume']:,.0f})")
            print(f"   ⚠️  CHECK FOR NEWS CATALYST (Pillar 5)")
            print()


def main():
    """Example usage"""
    # Initialize scanner with small account settings
    # For very small accounts, you might want $2-$4 with float < 5M
    scanner = FivePillarScanner(
        min_price=2.0,
        max_price=20.0,
        max_float=20_000_000,  # 20M shares
        min_rel_volume=5.0,
        min_gain_percent=10.0
    )

    # Example watchlist - replace with your own or use a market scanner API
    # These are just examples - in real use, you'd get this from Webull screener
    # or another data source
    sample_tickers = [
        'PTON', 'AMC', 'GME', 'BBBY', 'SNDL',
        'NAKD', 'OCGN', 'PROG', 'ATER', 'BBIG'
    ]

    print("\n⚠️  NOTE: This is a demo with sample tickers.")
    print("For live trading, get the top gainers list from Webull screener")
    print("or use the Day Trade Dash scanner.\n")

    # Scan the watchlist
    results = scanner.scan_watchlist(sample_tickers)

    # Display results
    scanner.display_results(results)

    # Save results to CSV
    if not results.empty:
        filename = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        results.to_csv(filename, index=False)
        print(f"\n💾 Results saved to {filename}")


if __name__ == "__main__":
    main()
