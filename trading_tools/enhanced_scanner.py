#!/usr/bin/env python3
"""
Enhanced 5-Pillar Stock Scanner with Short Interest
Based on Ross Cameron's Day 5 insights

Now includes:
- Price, Float, Volume, Gain, News (original 5 pillars)
- Short Interest % (key catalyst for big moves)
- Float sweet spot detection (~750K shares)
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List, Dict
import json


class EnhancedFivePillarScanner:
    def __init__(self,
                 min_price: float = 2.0,
                 max_price: float = 20.0,
                 max_float: float = 20_000_000,
                 min_rel_volume: float = 5.0,
                 min_gain_percent: float = 10.0,
                 min_short_interest: float = 20.0):  # New!
        """
        Initialize enhanced scanner with short interest

        Args:
            min_price: Minimum stock price (default $2)
            max_price: Maximum stock price (default $20)
            max_float: Maximum float in shares (default 20M)
            min_rel_volume: Minimum relative volume multiplier (default 5x)
            min_gain_percent: Minimum percentage gain (default 10%)
            min_short_interest: Minimum short interest % (default 20%)
        """
        self.min_price = min_price
        self.max_price = max_price
        self.max_float = max_float
        self.min_rel_volume = min_rel_volume
        self.min_gain_percent = min_gain_percent
        self.min_short_interest = min_short_interest

    def get_short_interest(self, ticker: str) -> float:
        """
        Get short interest percentage for a stock

        Args:
            ticker: Stock symbol

        Returns:
            Short interest as percentage of float
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Short interest can be found in different fields
            short_ratio = info.get('shortRatio', 0)
            short_percent = info.get('shortPercentOfFloat', 0)

            # Convert to percentage if needed
            if short_percent > 0:
                return short_percent * 100 if short_percent < 1 else short_percent

            return 0
        except:
            return 0

    def get_stock_data(self, ticker: str) -> Dict:
        """Fetch stock data including short interest"""
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

            # Get short interest
            short_interest = self.get_short_interest(ticker)

            # Check if in sweet spot (Ross's 750K insight)
            in_sweet_spot = 500_000 <= float_shares <= 1_000_000

            return {
                'ticker': ticker,
                'price': current_price,
                'pct_change': pct_change,
                'volume': current_volume,
                'avg_volume': avg_volume,
                'rel_volume': rel_volume,
                'float': float_shares,
                'short_interest': short_interest,
                'in_sweet_spot': in_sweet_spot,
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'name': info.get('longName', ticker)
            }
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def meets_criteria(self, stock_data: Dict) -> tuple[bool, List[str]]:
        """
        Check if stock meets enhanced criteria including short interest

        Returns:
            tuple: (passes, list of failed criteria)
        """
        if not stock_data:
            return False, ["No data available"]

        failed = []
        bonus = []

        # Pillar 1: Price Range
        if not (self.min_price <= stock_data['price'] <= self.max_price):
            failed.append(f"Price ${stock_data['price']:.2f} not in range ${self.min_price}-${self.max_price}")

        # Pillar 2: Float
        if stock_data['float'] > self.max_float:
            failed.append(f"Float {stock_data['float']/1_000_000:.1f}M exceeds {self.max_float/1_000_000:.1f}M")

        # Sweet spot bonus!
        if stock_data['in_sweet_spot']:
            bonus.append("🎯 SWEET SPOT: Float ~750K (explosive potential!)")

        # Pillar 3: Relative Volume
        if stock_data['rel_volume'] < self.min_rel_volume:
            failed.append(f"Rel Volume {stock_data['rel_volume']:.1f}x below {self.min_rel_volume}x")

        # Pillar 4: Percentage Gain
        if stock_data['pct_change'] < self.min_gain_percent:
            failed.append(f"Gain {stock_data['pct_change']:.1f}% below {self.min_gain_percent}%")

        # Pillar 6: SHORT INTEREST (New!)
        if stock_data['short_interest'] < self.min_short_interest:
            failed.append(f"Short Interest {stock_data['short_interest']:.1f}% below {self.min_short_interest}%")
        elif stock_data['short_interest'] >= 35:
            bonus.append(f"🔥 HIGH SHORT INTEREST: {stock_data['short_interest']:.1f}% (squeeze potential!)")

        # Pillar 5: News - requires manual verification
        # This is flagged for user to check

        passes = len(failed) == 0
        return passes, failed, bonus

    def scan_watchlist(self, tickers: List[str]) -> pd.DataFrame:
        """
        Scan a list of tickers for enhanced criteria

        Args:
            tickers: List of stock ticker symbols

        Returns:
            DataFrame of stocks that pass the scan
        """
        results = []

        print(f"\n{'='*80}")
        print(f"ENHANCED 5-PILLAR SCANNER + SHORT INTEREST")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"Criteria:")
        print(f"  • Price: ${self.min_price} - ${self.max_price}")
        print(f"  • Float: < {self.max_float/1_000_000:.0f}M shares (Sweet Spot: ~750K)")
        print(f"  • Rel Volume: > {self.min_rel_volume}x")
        print(f"  • Gain: > {self.min_gain_percent}%")
        print(f"  • Short Interest: > {self.min_short_interest}%")
        print(f"  • News: Manual verification required")
        print(f"{'='*80}\n")

        for ticker in tickers:
            print(f"Scanning {ticker}...", end=" ")
            stock_data = self.get_stock_data(ticker)

            if stock_data:
                passes, failed, bonus = self.meets_criteria(stock_data)

                if passes:
                    print("✓ PASSED ALL CRITERIA")
                    if bonus:
                        for b in bonus:
                            print(f"  {b}")
                    stock_data['status'] = 'PASS'
                    stock_data['failed_criteria'] = ''
                    stock_data['bonus'] = ' | '.join(bonus)
                    results.append(stock_data)
                else:
                    print(f"✗ Failed: {', '.join(failed)}")
            else:
                print("✗ No data")

        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('short_interest', ascending=False)  # Sort by short interest!
            return df
        else:
            return pd.DataFrame()

    def display_results(self, df: pd.DataFrame):
        """Display scan results with short interest"""
        if df.empty:
            print("\n❌ No stocks met the enhanced criteria")
            return

        print(f"\n{'='*80}")
        print(f"✅ {len(df)} STOCK(S) PASSED THE ENHANCED SCAN")
        print(f"{'='*80}\n")

        for idx, row in df.iterrows():
            print(f"🎯 {row['ticker']} - {row['name']}")
            print(f"   Price: ${row['price']:.2f}")
            print(f"   Gain: +{row['pct_change']:.2f}%")
            print(f"   Float: {row['float']/1_000_000:.2f}M shares", end="")
            if row['in_sweet_spot']:
                print(" 🎯 SWEET SPOT!")
            else:
                print()
            print(f"   🔥 Short Interest: {row['short_interest']:.2f}%")
            print(f"   Rel Volume: {row['rel_volume']:.2f}x")
            print(f"   Volume: {row['volume']:,.0f} (Avg: {row['avg_volume']:,.0f})")
            if row.get('bonus'):
                print(f"   💡 {row['bonus']}")
            print(f"   ⚠️  CHECK FOR NEWS CATALYST")
            print()


def main():
    """Example usage"""
    # Initialize enhanced scanner
    scanner = EnhancedFivePillarScanner(
        min_price=2.0,
        max_price=20.0,
        max_float=20_000_000,  # 20M shares
        min_rel_volume=5.0,
        min_gain_percent=10.0,
        min_short_interest=20.0  # Looking for high short interest like Ross
    )

    # Example watchlist
    sample_tickers = [
        'PTON', 'AMC', 'GME', 'BBBY', 'SNDL',
        'NAKD', 'OCGN', 'PROG', 'ATER', 'BBIG'
    ]

    print("\n⚠️  NOTE: This is a demo with sample tickers.")
    print("For live trading, get the top gainers list from Webull screener\n")

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
