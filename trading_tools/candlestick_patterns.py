#!/usr/bin/env python3
"""
CANDLESTICK PATTERN RECOGNITION MODULE
Identify classic candlestick patterns for trading signals

Patterns Included:
- Doji (indecision)
- Hammer & Inverted Hammer (reversal)
- Shooting Star (bearish reversal)
- Engulfing (bullish/bearish)
- Morning Star & Evening Star (reversal)
- Harami (potential reversal)
- Marubozu (strong momentum)
- Three White Soldiers / Three Black Crows
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import yfinance as yf
from datetime import datetime, timedelta


class CandlestickPatternRecognizer:
    """Recognize candlestick patterns in stock data"""

    def __init__(self, ticker: str, period: str = "1mo", interval: str = "1d"):
        """
        Initialize with stock data

        Args:
            ticker: Stock symbol
            period: Data period (5d, 1mo, 3mo)
            interval: Data interval (1d, 1h, 15m)
        """
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data = None

    def fetch_data(self) -> bool:
        """Fetch stock data from yfinance"""
        try:
            stock = yf.Ticker(self.ticker)
            self.data = stock.history(period=self.period, interval=self.interval)

            if self.data.empty or len(self.data) < 3:
                return False

            return True

        except Exception as e:
            print(f"Error fetching data for {self.ticker}: {e}")
            return False

    def is_doji(self, idx: int, threshold: float = 0.1) -> bool:
        """
        Identify Doji pattern (open ≈ close, indecision)

        Args:
            idx: Candle index
            threshold: Body size threshold (% of range)
        """
        try:
            candle = self.data.iloc[idx]
            body = abs(candle['Close'] - candle['Open'])
            range_size = candle['High'] - candle['Low']

            if range_size == 0:
                return False

            body_percent = body / range_size

            return body_percent <= threshold

        except:
            return False

    def is_hammer(self, idx: int) -> bool:
        """
        Identify Hammer pattern (bullish reversal at bottom)
        - Small body at top
        - Long lower shadow (2x body)
        - Little to no upper shadow
        """
        try:
            candle = self.data.iloc[idx]

            body = abs(candle['Close'] - candle['Open'])
            lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
            upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
            range_size = candle['High'] - candle['Low']

            if range_size == 0:
                return False

            # Conditions for hammer
            body_percent = body / range_size
            lower_shadow_ratio = lower_shadow / body if body > 0 else 0
            upper_shadow_ratio = upper_shadow / range_size

            is_hammer = (
                body_percent < 0.3 and  # Small body
                lower_shadow_ratio >= 2 and  # Long lower shadow
                upper_shadow_ratio < 0.1  # Little upper shadow
            )

            return is_hammer

        except:
            return False

    def is_inverted_hammer(self, idx: int) -> bool:
        """
        Identify Inverted Hammer pattern (bullish reversal)
        - Small body at bottom
        - Long upper shadow (2x body)
        - Little to no lower shadow
        """
        try:
            candle = self.data.iloc[idx]

            body = abs(candle['Close'] - candle['Open'])
            lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
            upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
            range_size = candle['High'] - candle['Low']

            if range_size == 0:
                return False

            body_percent = body / range_size
            upper_shadow_ratio = upper_shadow / body if body > 0 else 0
            lower_shadow_ratio = lower_shadow / range_size

            is_inv_hammer = (
                body_percent < 0.3 and
                upper_shadow_ratio >= 2 and
                lower_shadow_ratio < 0.1
            )

            return is_inv_hammer

        except:
            return False

    def is_shooting_star(self, idx: int) -> bool:
        """
        Identify Shooting Star pattern (bearish reversal at top)
        - Small body at bottom
        - Long upper shadow (2x body)
        - Little to no lower shadow
        - Appears after uptrend
        """
        try:
            if idx < 1:
                return False

            candle = self.data.iloc[idx]
            prev_candle = self.data.iloc[idx - 1]

            # Check for uptrend
            in_uptrend = candle['Close'] > prev_candle['Open']

            if not in_uptrend:
                return False

            # Same as inverted hammer but in uptrend
            return self.is_inverted_hammer(idx)

        except:
            return False

    def is_bullish_engulfing(self, idx: int) -> bool:
        """
        Identify Bullish Engulfing pattern
        - Previous candle: small bearish
        - Current candle: large bullish that engulfs previous
        """
        try:
            if idx < 1:
                return False

            current = self.data.iloc[idx]
            previous = self.data.iloc[idx - 1]

            # Previous candle is bearish
            prev_bearish = previous['Close'] < previous['Open']

            # Current candle is bullish
            curr_bullish = current['Close'] > current['Open']

            # Current engulfs previous
            engulfs = (
                current['Open'] <= previous['Close'] and
                current['Close'] >= previous['Open']
            )

            return prev_bearish and curr_bullish and engulfs

        except:
            return False

    def is_bearish_engulfing(self, idx: int) -> bool:
        """
        Identify Bearish Engulfing pattern
        - Previous candle: small bullish
        - Current candle: large bearish that engulfs previous
        """
        try:
            if idx < 1:
                return False

            current = self.data.iloc[idx]
            previous = self.data.iloc[idx - 1]

            # Previous candle is bullish
            prev_bullish = previous['Close'] > previous['Open']

            # Current candle is bearish
            curr_bearish = current['Close'] < current['Open']

            # Current engulfs previous
            engulfs = (
                current['Open'] >= previous['Close'] and
                current['Close'] <= previous['Open']
            )

            return prev_bullish and curr_bearish and engulfs

        except:
            return False

    def is_morning_star(self, idx: int) -> bool:
        """
        Identify Morning Star pattern (bullish reversal)
        - 3 candles: large bearish, small body, large bullish
        """
        try:
            if idx < 2:
                return False

            first = self.data.iloc[idx - 2]
            second = self.data.iloc[idx - 1]
            third = self.data.iloc[idx]

            # First candle: large bearish
            first_bearish = first['Close'] < first['Open']
            first_large = abs(first['Close'] - first['Open']) > (first['High'] - first['Low']) * 0.6

            # Second candle: small body (star)
            second_small = abs(second['Close'] - second['Open']) < (second['High'] - second['Low']) * 0.3

            # Third candle: large bullish
            third_bullish = third['Close'] > third['Open']
            third_large = abs(third['Close'] - third['Open']) > (third['High'] - third['Low']) * 0.6

            # Third closes above midpoint of first
            third_recovers = third['Close'] > (first['Open'] + first['Close']) / 2

            return first_bearish and first_large and second_small and third_bullish and third_large and third_recovers

        except:
            return False

    def is_evening_star(self, idx: int) -> bool:
        """
        Identify Evening Star pattern (bearish reversal)
        - 3 candles: large bullish, small body, large bearish
        """
        try:
            if idx < 2:
                return False

            first = self.data.iloc[idx - 2]
            second = self.data.iloc[idx - 1]
            third = self.data.iloc[idx]

            # First candle: large bullish
            first_bullish = first['Close'] > first['Open']
            first_large = abs(first['Close'] - first['Open']) > (first['High'] - first['Low']) * 0.6

            # Second candle: small body (star)
            second_small = abs(second['Close'] - second['Open']) < (second['High'] - second['Low']) * 0.3

            # Third candle: large bearish
            third_bearish = third['Close'] < third['Open']
            third_large = abs(third['Close'] - third['Open']) > (third['High'] - third['Low']) * 0.6

            # Third closes below midpoint of first
            third_reverses = third['Close'] < (first['Open'] + first['Close']) / 2

            return first_bullish and first_large and second_small and third_bearish and third_large and third_reverses

        except:
            return False

    def is_bullish_harami(self, idx: int) -> bool:
        """
        Identify Bullish Harami pattern
        - Previous: large bearish
        - Current: small bullish inside previous body
        """
        try:
            if idx < 1:
                return False

            current = self.data.iloc[idx]
            previous = self.data.iloc[idx - 1]

            # Previous: large bearish
            prev_bearish = previous['Close'] < previous['Open']
            prev_body = abs(previous['Close'] - previous['Open'])

            # Current: small bullish
            curr_bullish = current['Close'] > current['Open']
            curr_body = abs(current['Close'] - current['Open'])

            # Current is inside previous body
            inside = (
                current['Open'] > previous['Close'] and
                current['Close'] < previous['Open'] and
                curr_body < prev_body * 0.5
            )

            return prev_bearish and curr_bullish and inside

        except:
            return False

    def is_marubozu(self, idx: int) -> bool:
        """
        Identify Marubozu pattern (strong momentum, no shadows)
        - Body = 95%+ of total range
        """
        try:
            candle = self.data.iloc[idx]

            body = abs(candle['Close'] - candle['Open'])
            range_size = candle['High'] - candle['Low']

            if range_size == 0:
                return False

            body_percent = body / range_size

            is_bullish_marubozu = body_percent >= 0.95 and candle['Close'] > candle['Open']
            is_bearish_marubozu = body_percent >= 0.95 and candle['Close'] < candle['Open']

            return is_bullish_marubozu or is_bearish_marubozu

        except:
            return False

    def is_three_white_soldiers(self, idx: int) -> bool:
        """
        Identify Three White Soldiers pattern (strong bullish)
        - 3 consecutive large bullish candles
        - Each opens within previous body
        - Each closes higher
        """
        try:
            if idx < 2:
                return False

            first = self.data.iloc[idx - 2]
            second = self.data.iloc[idx - 1]
            third = self.data.iloc[idx]

            # All bullish
            all_bullish = (
                first['Close'] > first['Open'] and
                second['Close'] > second['Open'] and
                third['Close'] > third['Open']
            )

            # Progressive closes
            progressive = second['Close'] > first['Close'] and third['Close'] > second['Close']

            # Opens within previous body
            opens_inside = (
                first['Open'] < second['Open'] < first['Close'] and
                second['Open'] < third['Open'] < second['Close']
            )

            return all_bullish and progressive and opens_inside

        except:
            return False

    def is_three_black_crows(self, idx: int) -> bool:
        """
        Identify Three Black Crows pattern (strong bearish)
        - 3 consecutive large bearish candles
        - Each opens within previous body
        - Each closes lower
        """
        try:
            if idx < 2:
                return False

            first = self.data.iloc[idx - 2]
            second = self.data.iloc[idx - 1]
            third = self.data.iloc[idx]

            # All bearish
            all_bearish = (
                first['Close'] < first['Open'] and
                second['Close'] < second['Open'] and
                third['Close'] < third['Open']
            )

            # Progressive closes
            progressive = second['Close'] < first['Close'] and third['Close'] < second['Close']

            # Opens within previous body
            opens_inside = (
                first['Close'] < second['Open'] < first['Open'] and
                second['Close'] < third['Open'] < second['Open']
            )

            return all_bearish and progressive and opens_inside

        except:
            return False

    def scan_all_patterns(self) -> Dict:
        """
        Scan for all candlestick patterns

        Returns:
            dict with found patterns and their signals
        """
        if not self.fetch_data():
            return None

        # Use most recent candles
        idx = len(self.data) - 1

        patterns_found = []

        # Bullish patterns
        if self.is_hammer(idx):
            patterns_found.append({
                'name': 'Hammer',
                'type': 'BULLISH',
                'strength': 'STRONG',
                'emoji': '🔨',
                'description': 'Bullish reversal at bottom'
            })

        if self.is_inverted_hammer(idx):
            patterns_found.append({
                'name': 'Inverted Hammer',
                'type': 'BULLISH',
                'strength': 'MODERATE',
                'emoji': '🔨',
                'description': 'Potential bullish reversal'
            })

        if self.is_bullish_engulfing(idx):
            patterns_found.append({
                'name': 'Bullish Engulfing',
                'type': 'BULLISH',
                'strength': 'STRONG',
                'emoji': '🟢',
                'description': 'Strong bullish reversal'
            })

        if self.is_morning_star(idx):
            patterns_found.append({
                'name': 'Morning Star',
                'type': 'BULLISH',
                'strength': 'VERY_STRONG',
                'emoji': '⭐',
                'description': 'Major bullish reversal'
            })

        if self.is_bullish_harami(idx):
            patterns_found.append({
                'name': 'Bullish Harami',
                'type': 'BULLISH',
                'strength': 'MODERATE',
                'emoji': '📈',
                'description': 'Potential bullish reversal'
            })

        if self.is_three_white_soldiers(idx):
            patterns_found.append({
                'name': 'Three White Soldiers',
                'type': 'BULLISH',
                'strength': 'VERY_STRONG',
                'emoji': '🚀',
                'description': 'Strong sustained uptrend'
            })

        # Bearish patterns
        if self.is_shooting_star(idx):
            patterns_found.append({
                'name': 'Shooting Star',
                'type': 'BEARISH',
                'strength': 'STRONG',
                'emoji': '💫',
                'description': 'Bearish reversal at top'
            })

        if self.is_bearish_engulfing(idx):
            patterns_found.append({
                'name': 'Bearish Engulfing',
                'type': 'BEARISH',
                'strength': 'STRONG',
                'emoji': '🔴',
                'description': 'Strong bearish reversal'
            })

        if self.is_evening_star(idx):
            patterns_found.append({
                'name': 'Evening Star',
                'type': 'BEARISH',
                'strength': 'VERY_STRONG',
                'emoji': '🌙',
                'description': 'Major bearish reversal'
            })

        if self.is_three_black_crows(idx):
            patterns_found.append({
                'name': 'Three Black Crows',
                'type': 'BEARISH',
                'strength': 'VERY_STRONG',
                'emoji': '📉',
                'description': 'Strong sustained downtrend'
            })

        # Neutral patterns
        if self.is_doji(idx):
            patterns_found.append({
                'name': 'Doji',
                'type': 'NEUTRAL',
                'strength': 'WEAK',
                'emoji': '⚖️',
                'description': 'Indecision, possible reversal'
            })

        if self.is_marubozu(idx):
            candle = self.data.iloc[idx]
            is_bullish = candle['Close'] > candle['Open']
            patterns_found.append({
                'name': 'Marubozu',
                'type': 'BULLISH' if is_bullish else 'BEARISH',
                'strength': 'STRONG',
                'emoji': '💪',
                'description': f"Strong {'bullish' if is_bullish else 'bearish'} momentum"
            })

        # Calculate overall signal
        bullish_count = sum(1 for p in patterns_found if p['type'] == 'BULLISH')
        bearish_count = sum(1 for p in patterns_found if p['type'] == 'BEARISH')

        if bullish_count > bearish_count:
            overall_signal = 'BULLISH'
            signal_emoji = '📈'
        elif bearish_count > bullish_count:
            overall_signal = 'BEARISH'
            signal_emoji = '📉'
        else:
            overall_signal = 'NEUTRAL'
            signal_emoji = '➡️'

        return {
            'ticker': self.ticker,
            'patterns_found': patterns_found,
            'pattern_count': len(patterns_found),
            'bullish_patterns': bullish_count,
            'bearish_patterns': bearish_count,
            'overall_signal': overall_signal,
            'signal_emoji': signal_emoji
        }


def quick_pattern_scan(ticker: str) -> Dict:
    """
    Quick function to scan for all candlestick patterns

    Args:
        ticker: Stock symbol

    Returns:
        dict with found patterns
    """
    recognizer = CandlestickPatternRecognizer(ticker, period="1mo", interval="1d")
    return recognizer.scan_all_patterns()


if __name__ == "__main__":
    # Test with example ticker
    print("Testing Candlestick Pattern Recognition...")
    print("=" * 60)

    result = quick_pattern_scan("PTON")

    if result:
        print(f"\n🕯️ Candlestick Analysis for {result['ticker']}")
        print(f"Overall Signal: {result['signal_emoji']} {result['overall_signal']}")
        print(f"Patterns Found: {result['pattern_count']}")

        if result['patterns_found']:
            print("\n📋 Detected Patterns:")
            for pattern in result['patterns_found']:
                print(f"  {pattern['emoji']} {pattern['name']}: {pattern['description']} ({pattern['type']} - {pattern['strength']})")
        else:
            print("\n➡️ No significant patterns detected")

        print("\n" + "=" * 60)
        print("✅ Candlestick Pattern Recognition Working!")
    else:
        print("❌ Error running pattern recognition")
