#!/usr/bin/env python3
"""
MACD and Volume Analyzer
Based on Ross Cameron's Entry Criteria

Analyzes:
- MACD status (positive/negative, crossing)
- Volume profile (buying vs selling pressure)
- Topping tails (reversal signals)
- Entry quality based on Ross's rules
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class MACDVolumeAnalyzer:
    def __init__(self, ticker: str):
        """
        Initialize analyzer for a specific stock

        Args:
            ticker: Stock symbol to analyze
        """
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(ticker)

    def calculate_macd(self, df: pd.DataFrame,
                       fast_period: int = 12,
                       slow_period: int = 26,
                       signal_period: int = 9) -> pd.DataFrame:
        """
        Calculate MACD indicator

        Args:
            df: DataFrame with price data
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)

        Returns:
            DataFrame with MACD columns added
        """
        # Calculate EMAs
        ema_fast = df['Close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow_period, adjust=False).mean()

        # MACD line
        df['MACD'] = ema_fast - ema_slow

        # Signal line
        df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()

        # Histogram
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        return df

    def analyze_volume_profile(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze volume profile for buying vs selling pressure

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with volume analysis
        """
        # Determine if candle is bullish or bearish
        df['Bullish'] = df['Close'] > df['Open']

        # Split volume into buying and selling
        df['Buy_Volume'] = df.apply(
            lambda row: row['Volume'] if row['Bullish'] else 0, axis=1
        )
        df['Sell_Volume'] = df.apply(
            lambda row: row['Volume'] if not row['Bullish'] else 0, axis=1
        )

        # Detect topping tails (high volume + upper wick)
        df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
        df['Body_Size'] = abs(df['Close'] - df['Open'])
        df['Topping_Tail'] = (
            (df['Upper_Wick'] > df['Body_Size'] * 2) &
            (df['Volume'] > df['Volume'].rolling(20).mean())
        )

        return df

    def get_current_setup(self, period: str = "1d", interval: str = "5m") -> dict:
        """
        Get current setup analysis for potential entry

        Args:
            period: Data period (default "1d" for today)
            interval: Candle interval (default "5m")

        Returns:
            dict with setup analysis
        """
        try:
            # Get intraday data
            df = self.stock.history(period=period, interval=interval)

            if df.empty:
                return {'error': 'No data available'}

            # Calculate indicators
            df = self.calculate_macd(df)
            df = self.analyze_volume_profile(df)

            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None

            # Check MACD status
            macd_positive = latest['MACD_Hist'] > 0
            macd_crossing_down = False

            if prev is not None:
                macd_crossing_down = (
                    prev['MACD_Hist'] > 0 and latest['MACD_Hist'] < 0
                )

            # Calculate recent volume profile
            recent_bars = df.tail(10)
            total_buy_vol = recent_bars['Buy_Volume'].sum()
            total_sell_vol = recent_bars['Sell_Volume'].sum()

            volume_ratio = (
                total_buy_vol / total_sell_vol if total_sell_vol > 0 else float('inf')
            )

            # Check for recent topping tail
            recent_topping = recent_bars['Topping_Tail'].any()

            # Determine setup quality
            setup_quality = self._evaluate_setup(
                macd_positive,
                macd_crossing_down,
                volume_ratio,
                recent_topping
            )

            return {
                'ticker': self.ticker,
                'current_price': round(latest['Close'], 2),
                'macd_histogram': round(latest['MACD_Hist'], 4),
                'macd_positive': macd_positive,
                'macd_crossing_down': macd_crossing_down,
                'volume_ratio_buy_sell': round(volume_ratio, 2),
                'recent_topping_tail': recent_topping,
                'current_volume': int(latest['Volume']),
                'setup_quality': setup_quality,
                'recommendation': self._get_recommendation(setup_quality)
            }

        except Exception as e:
            return {'error': str(e)}

    def _evaluate_setup(self,
                       macd_positive: bool,
                       macd_crossing_down: bool,
                       volume_ratio: float,
                       topping_tail: bool) -> str:
        """Evaluate setup quality based on Ross's criteria"""

        # Must have positive MACD
        if not macd_positive:
            return "❌ NO TRADE - MACD Negative"

        # MACD crossing down is a bad sign
        if macd_crossing_down:
            return "❌ NO TRADE - MACD Crossing Down"

        # Topping tail indicates reversal
        if topping_tail:
            return "⚠️  CAUTION - Recent Topping Tail"

        # Good volume profile (more buying than selling)
        if volume_ratio > 2.0:
            return "✅ EXCELLENT - Strong Buying Pressure"
        elif volume_ratio > 1.0:
            return "✓ GOOD - Decent Buying Pressure"
        else:
            return "⚠️  CAUTION - More Selling Than Buying"

    def _get_recommendation(self, quality: str) -> str:
        """Get trading recommendation based on setup quality"""
        if "EXCELLENT" in quality:
            return "TAKE THE TRADE - A+ Setup"
        elif "GOOD" in quality:
            return "CONSIDER - Decent Setup"
        elif "CAUTION" in quality:
            return "BE CAREFUL - Watch Closely"
        else:
            return "DO NOT TRADE - Wait for Better Setup"

    def display_analysis(self, setup: dict):
        """Display setup analysis in formatted output"""
        if 'error' in setup:
            print(f"\n❌ Error: {setup['error']}")
            return

        print(f"\n{'='*70}")
        print(f"MACD & VOLUME ANALYSIS - {self.ticker}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

        print(f"\n💰 CURRENT PRICE: ${setup['current_price']:.2f}")

        print(f"\n📊 MACD STATUS:")
        macd_emoji = "✅" if setup['macd_positive'] else "❌"
        print(f"   {macd_emoji} MACD Histogram: {setup['macd_histogram']:.4f}")
        print(f"   Status: {'POSITIVE ✓' if setup['macd_positive'] else 'NEGATIVE ✗'}")

        if setup['macd_crossing_down']:
            print(f"   ⚠️  WARNING: MACD Crossing Down!")

        print(f"\n📈 VOLUME PROFILE:")
        print(f"   Buy/Sell Ratio: {setup['volume_ratio_buy_sell']:.2f}x")

        if setup['volume_ratio_buy_sell'] > 2.0:
            print(f"   ✅ Strong buying pressure")
        elif setup['volume_ratio_buy_sell'] > 1.0:
            print(f"   ✓ More buying than selling")
        else:
            print(f"   ❌ More selling than buying")

        if setup['recent_topping_tail']:
            print(f"   ⚠️  WARNING: Recent topping tail detected!")

        print(f"\n🎯 SETUP EVALUATION:")
        print(f"   Quality: {setup['setup_quality']}")
        print(f"   Recommendation: {setup['recommendation']}")

        print(f"\n{'='*70}\n")

    def quick_check(self) -> bool:
        """
        Quick boolean check: Is this a valid Ross Cameron setup?

        Returns:
            True if setup meets criteria, False otherwise
        """
        setup = self.get_current_setup()

        if 'error' in setup:
            return False

        # Must have positive MACD
        if not setup['macd_positive']:
            return False

        # Must not be crossing down
        if setup['macd_crossing_down']:
            return False

        # Should have more buying than selling
        if setup['volume_ratio_buy_sell'] < 1.0:
            return False

        # Should not have recent topping tail
        if setup['recent_topping_tail']:
            return False

        return True


def main():
    """Example usage"""
    print("\n" + "="*70)
    print("MACD & VOLUME ANALYZER")
    print("Based on Ross Cameron's Entry Criteria")
    print("="*70)

    # Example: Analyze a stock
    ticker = input("\nEnter ticker symbol to analyze: ").strip().upper()

    if not ticker:
        ticker = "AAPL"  # Default for demo
        print(f"Using default ticker: {ticker}")

    analyzer = MACDVolumeAnalyzer(ticker)

    # Get and display analysis
    setup = analyzer.get_current_setup()
    analyzer.display_analysis(setup)

    # Quick check
    is_valid = analyzer.quick_check()
    print(f"\n🎯 FINAL VERDICT:")
    if is_valid:
        print(f"   ✅ {ticker} meets Ross Cameron's entry criteria")
        print(f"   Consider taking the trade if it's a pullback setup")
    else:
        print(f"   ❌ {ticker} does NOT meet entry criteria")
        print(f"   Wait for a better setup")

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
