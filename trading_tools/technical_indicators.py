#!/usr/bin/env python3
"""
TECHNICAL INDICATORS MODULE
Complete suite of technical analysis indicators for trading

Includes:
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- Moving Averages (9, 20, 50, 200)
- ATR (Average True Range)
- VWAP (Volume Weighted Average Price)
- Volume Profile
- Bollinger Bands
- Stochastic Oscillator
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import yfinance as yf
from datetime import datetime, timedelta


class TechnicalIndicators:
    """Calculate all technical indicators for a stock"""

    def __init__(self, ticker: str, period: str = "1mo", interval: str = "1d"):
        """
        Initialize with stock data

        Args:
            ticker: Stock symbol
            period: Data period (1mo, 3mo, 6mo, 1y)
            interval: Data interval (1m, 5m, 15m, 1h, 1d)
        """
        self.ticker = ticker
        self.period = period
        self.interval = interval
        self.data = None
        self.current_price = None

    def fetch_data(self) -> bool:
        """Fetch stock data from yfinance"""
        try:
            stock = yf.Ticker(self.ticker)
            self.data = stock.history(period=self.period, interval=self.interval)

            if self.data.empty:
                return False

            self.current_price = self.data['Close'].iloc[-1]
            return True

        except Exception as e:
            print(f"Error fetching data for {self.ticker}: {e}")
            return False

    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        Calculate MACD indicator

        Returns:
            dict with macd_line, signal_line, histogram, is_positive
        """
        if self.data is None or len(self.data) < slow:
            return None

        try:
            # Calculate EMAs
            ema_fast = self.data['Close'].ewm(span=fast, adjust=False).mean()
            ema_slow = self.data['Close'].ewm(span=slow, adjust=False).mean()

            # MACD line = Fast EMA - Slow EMA
            macd_line = ema_fast - ema_slow

            # Signal line = 9-period EMA of MACD
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()

            # Histogram = MACD - Signal
            histogram = macd_line - signal_line

            return {
                'macd_line': round(macd_line.iloc[-1], 4),
                'signal_line': round(signal_line.iloc[-1], 4),
                'histogram': round(histogram.iloc[-1], 4),
                'is_positive': histogram.iloc[-1] > 0,
                'is_bullish': macd_line.iloc[-1] > signal_line.iloc[-1]
            }

        except Exception as e:
            print(f"Error calculating MACD: {e}")
            return None

    def calculate_rsi(self, period: int = 14) -> Dict:
        """
        Calculate RSI (Relative Strength Index)

        Returns:
            dict with rsi_value, signal (overbought/oversold/neutral)
        """
        if self.data is None or len(self.data) < period + 1:
            return None

        try:
            # Calculate price changes
            delta = self.data['Close'].diff()

            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            # Calculate RS and RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1]

            # Determine signal
            if current_rsi >= 70:
                signal = "OVERBOUGHT"
                color = "🔴"
            elif current_rsi <= 30:
                signal = "OVERSOLD"
                color = "🟢"
            else:
                signal = "NEUTRAL"
                color = "🟡"

            return {
                'rsi': round(current_rsi, 2),
                'signal': signal,
                'color': color,
                'bullish': current_rsi < 50,  # Below 50 = potential upside
                'bearish': current_rsi > 70   # Above 70 = potential reversal
            }

        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return None

    def calculate_moving_averages(self) -> Dict:
        """
        Calculate key moving averages (9, 20, 50, 200 EMA)

        Returns:
            dict with all MAs and trend signals
        """
        if self.data is None:
            return None

        try:
            current_price = self.data['Close'].iloc[-1]

            results = {}

            # Calculate EMAs
            for period in [9, 20, 50, 200]:
                if len(self.data) >= period:
                    ema = self.data['Close'].ewm(span=period, adjust=False).mean().iloc[-1]
                    results[f'ema_{period}'] = round(ema, 2)
                    results[f'above_ema_{period}'] = current_price > ema
                else:
                    results[f'ema_{period}'] = None
                    results[f'above_ema_{period}'] = None

            # Trend analysis
            if results['ema_9'] and results['ema_20'] and results['ema_50']:
                # Golden cross = short MA > long MA (bullish)
                if results['ema_9'] > results['ema_20'] > results['ema_50']:
                    results['trend'] = "STRONG_BULL"
                    results['trend_emoji'] = "🚀"
                elif results['ema_9'] > results['ema_20']:
                    results['trend'] = "BULL"
                    results['trend_emoji'] = "📈"
                elif results['ema_9'] < results['ema_20'] < results['ema_50']:
                    results['trend'] = "STRONG_BEAR"
                    results['trend_emoji'] = "📉"
                else:
                    results['trend'] = "NEUTRAL"
                    results['trend_emoji'] = "➡️"
            else:
                results['trend'] = "INSUFFICIENT_DATA"
                results['trend_emoji'] = "❓"

            return results

        except Exception as e:
            print(f"Error calculating moving averages: {e}")
            return None

    def calculate_atr(self, period: int = 14) -> Dict:
        """
        Calculate ATR (Average True Range) for volatility

        Returns:
            dict with atr_value, atr_percent, stop_loss_distance
        """
        if self.data is None or len(self.data) < period + 1:
            return None

        try:
            high = self.data['High']
            low = self.data['Low']
            close = self.data['Close']

            # Calculate True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())

            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # ATR = Average of True Range
            atr = true_range.rolling(window=period).mean().iloc[-1]

            current_price = close.iloc[-1]
            atr_percent = (atr / current_price) * 100

            # Stop loss suggestions (1x, 1.5x, 2x ATR)
            stop_loss_1x = current_price - atr
            stop_loss_1_5x = current_price - (atr * 1.5)
            stop_loss_2x = current_price - (atr * 2)

            return {
                'atr': round(atr, 2),
                'atr_percent': round(atr_percent, 2),
                'stop_loss_1x_atr': round(stop_loss_1x, 2),
                'stop_loss_1_5x_atr': round(stop_loss_1_5x, 2),
                'stop_loss_2x_atr': round(stop_loss_2x, 2),
                'volatility_level': 'HIGH' if atr_percent > 5 else 'MEDIUM' if atr_percent > 2 else 'LOW'
            }

        except Exception as e:
            print(f"Error calculating ATR: {e}")
            return None

    def calculate_vwap(self) -> Dict:
        """
        Calculate VWAP (Volume Weighted Average Price)

        Returns:
            dict with vwap, current_vs_vwap
        """
        if self.data is None or len(self.data) == 0:
            return None

        try:
            # For intraday, use today's data only
            # For daily, use recent period
            typical_price = (self.data['High'] + self.data['Low'] + self.data['Close']) / 3
            vwap = (typical_price * self.data['Volume']).cumsum() / self.data['Volume'].cumsum()

            current_vwap = vwap.iloc[-1]
            current_price = self.data['Close'].iloc[-1]

            distance_from_vwap = ((current_price - current_vwap) / current_vwap) * 100

            if distance_from_vwap > 2:
                signal = "ABOVE_VWAP"
                emoji = "🟢"
            elif distance_from_vwap < -2:
                signal = "BELOW_VWAP"
                emoji = "🔴"
            else:
                signal = "AT_VWAP"
                emoji = "🟡"

            return {
                'vwap': round(current_vwap, 2),
                'current_price': round(current_price, 2),
                'distance_percent': round(distance_from_vwap, 2),
                'signal': signal,
                'emoji': emoji
            }

        except Exception as e:
            print(f"Error calculating VWAP: {e}")
            return None

    def calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2) -> Dict:
        """
        Calculate Bollinger Bands

        Returns:
            dict with upper_band, middle_band, lower_band, position
        """
        if self.data is None or len(self.data) < period:
            return None

        try:
            # Middle band = 20-day SMA
            middle_band = self.data['Close'].rolling(window=period).mean()

            # Standard deviation
            std = self.data['Close'].rolling(window=period).std()

            # Upper and lower bands
            upper_band = middle_band + (std * std_dev)
            lower_band = middle_band - (std * std_dev)

            current_price = self.data['Close'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_middle = middle_band.iloc[-1]
            current_lower = lower_band.iloc[-1]

            # Determine position
            bandwidth = ((current_upper - current_lower) / current_middle) * 100

            if current_price >= current_upper:
                position = "ABOVE_UPPER"
                signal = "OVERBOUGHT"
                emoji = "🔴"
            elif current_price <= current_lower:
                position = "BELOW_LOWER"
                signal = "OVERSOLD"
                emoji = "🟢"
            else:
                position = "INSIDE_BANDS"
                signal = "NEUTRAL"
                emoji = "🟡"

            return {
                'upper_band': round(current_upper, 2),
                'middle_band': round(current_middle, 2),
                'lower_band': round(current_lower, 2),
                'bandwidth_percent': round(bandwidth, 2),
                'position': position,
                'signal': signal,
                'emoji': emoji
            }

        except Exception as e:
            print(f"Error calculating Bollinger Bands: {e}")
            return None

    def calculate_stochastic(self, k_period: int = 14, d_period: int = 3) -> Dict:
        """
        Calculate Stochastic Oscillator

        Returns:
            dict with %K, %D, signal
        """
        if self.data is None or len(self.data) < k_period:
            return None

        try:
            # %K = (Current Close - Lowest Low) / (Highest High - Lowest Low) * 100
            low_min = self.data['Low'].rolling(window=k_period).min()
            high_max = self.data['High'].rolling(window=k_period).max()

            k_percent = 100 * ((self.data['Close'] - low_min) / (high_max - low_min))

            # %D = 3-period SMA of %K
            d_percent = k_percent.rolling(window=d_period).mean()

            current_k = k_percent.iloc[-1]
            current_d = d_percent.iloc[-1]

            # Determine signal
            if current_k > 80 and current_d > 80:
                signal = "OVERBOUGHT"
                emoji = "🔴"
            elif current_k < 20 and current_d < 20:
                signal = "OVERSOLD"
                emoji = "🟢"
            else:
                signal = "NEUTRAL"
                emoji = "🟡"

            return {
                'k_percent': round(current_k, 2),
                'd_percent': round(current_d, 2),
                'signal': signal,
                'emoji': emoji,
                'bullish_crossover': current_k > current_d and current_k < 50
            }

        except Exception as e:
            print(f"Error calculating Stochastic: {e}")
            return None

    def get_all_indicators(self) -> Dict:
        """
        Calculate ALL indicators at once

        Returns:
            dict with all indicator results
        """
        if not self.fetch_data():
            return None

        return {
            'ticker': self.ticker,
            'current_price': round(self.current_price, 2) if self.current_price else None,
            'macd': self.calculate_macd(),
            'rsi': self.calculate_rsi(),
            'moving_averages': self.calculate_moving_averages(),
            'atr': self.calculate_atr(),
            'vwap': self.calculate_vwap(),
            'bollinger_bands': self.calculate_bollinger_bands(),
            'stochastic': self.calculate_stochastic()
        }

    def get_trade_signal(self) -> Dict:
        """
        Combine all indicators to generate overall trade signal

        Returns:
            dict with overall signal, score, reasons
        """
        indicators = self.get_all_indicators()

        if not indicators:
            return None

        bullish_signals = []
        bearish_signals = []
        score = 0

        # MACD
        macd = indicators.get('macd')
        if macd:
            if macd['is_positive'] and macd['is_bullish']:
                bullish_signals.append("MACD Positive & Bullish")
                score += 2
            elif not macd['is_positive']:
                bearish_signals.append("MACD Negative")
                score -= 2

        # RSI
        rsi = indicators.get('rsi')
        if rsi:
            if rsi['signal'] == 'OVERSOLD':
                bullish_signals.append(f"RSI Oversold ({rsi['rsi']})")
                score += 2
            elif rsi['signal'] == 'OVERBOUGHT':
                bearish_signals.append(f"RSI Overbought ({rsi['rsi']})")
                score -= 2

        # Moving Averages
        mas = indicators.get('moving_averages')
        if mas:
            if mas['trend'] in ['STRONG_BULL', 'BULL']:
                bullish_signals.append(f"Trend: {mas['trend']}")
                score += 3 if mas['trend'] == 'STRONG_BULL' else 2
            elif mas['trend'] == 'STRONG_BEAR':
                bearish_signals.append(f"Trend: {mas['trend']}")
                score -= 3

        # Bollinger Bands
        bb = indicators.get('bollinger_bands')
        if bb:
            if bb['signal'] == 'OVERSOLD':
                bullish_signals.append("Below Lower BB")
                score += 1
            elif bb['signal'] == 'OVERBOUGHT':
                bearish_signals.append("Above Upper BB")
                score -= 1

        # VWAP
        vwap = indicators.get('vwap')
        if vwap:
            if vwap['signal'] == 'BELOW_VWAP':
                bullish_signals.append("Below VWAP (bounce potential)")
                score += 1

        # Stochastic
        stoch = indicators.get('stochastic')
        if stoch:
            if stoch['signal'] == 'OVERSOLD':
                bullish_signals.append("Stochastic Oversold")
                score += 1
            elif stoch['signal'] == 'OVERBOUGHT':
                bearish_signals.append("Stochastic Overbought")
                score -= 1

        # Overall signal
        if score >= 5:
            overall = "STRONG_BUY"
            emoji = "🚀"
            color = "#00FF00"
        elif score >= 3:
            overall = "BUY"
            emoji = "📈"
            color = "#90EE90"
        elif score <= -5:
            overall = "STRONG_SELL"
            emoji = "🛑"
            color = "#FF0000"
        elif score <= -3:
            overall = "SELL"
            emoji = "📉"
            color = "#FFA500"
        else:
            overall = "NEUTRAL"
            emoji = "➡️"
            color = "#FFFF00"

        return {
            'signal': overall,
            'score': score,
            'emoji': emoji,
            'color': color,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'bullish_count': len(bullish_signals),
            'bearish_count': len(bearish_signals)
        }


def quick_analysis(ticker: str) -> Dict:
    """
    Quick function to get all indicators for a ticker

    Args:
        ticker: Stock symbol

    Returns:
        dict with all indicators and trade signal
    """
    analyzer = TechnicalIndicators(ticker, period="3mo", interval="1d")
    indicators = analyzer.get_all_indicators()

    if not indicators:
        return None

    signal = analyzer.get_trade_signal()
    indicators['trade_signal'] = signal

    return indicators


if __name__ == "__main__":
    # Test with example ticker
    print("Testing Technical Indicators Module...")
    print("=" * 60)

    result = quick_analysis("PTON")

    if result:
        print(f"\n📊 Analysis for {result['ticker']}")
        print(f"Current Price: ${result['current_price']}")

        if result['trade_signal']:
            signal = result['trade_signal']
            print(f"\n{signal['emoji']} OVERALL SIGNAL: {signal['signal']} (Score: {signal['score']})")

            if signal['bullish_signals']:
                print("\n✅ Bullish Signals:")
                for s in signal['bullish_signals']:
                    print(f"  • {s}")

            if signal['bearish_signals']:
                print("\n❌ Bearish Signals:")
                for s in signal['bearish_signals']:
                    print(f"  • {s}")

        print("\n" + "=" * 60)
        print("✅ Technical Indicators Module Working!")
    else:
        print("❌ Error running analysis")
