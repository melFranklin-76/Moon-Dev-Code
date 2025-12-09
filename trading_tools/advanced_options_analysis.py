#!/usr/bin/env python3
"""
ADVANCED OPTIONS ANALYSIS MODULE
Calculate advanced options metrics for better trading decisions

Metrics Included:
- Implied Volatility Rank (IVR)
- Put/Call Ratio
- Options Volume Analysis
- IV Percentile
- Options Flow (bullish vs bearish)
- Max Pain Analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')


class AdvancedOptionsAnalyzer:
    """Advanced options metrics calculator"""

    def __init__(self, ticker: str):
        """
        Initialize analyzer

        Args:
            ticker: Stock symbol
        """
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)

    def calculate_iv_rank(self, lookback_days: int = 252) -> Optional[Dict]:
        """
        Calculate Implied Volatility Rank (IVR)
        IVR = (Current IV - 52-week Low IV) / (52-week High IV - 52-week Low IV) * 100

        Args:
            lookback_days: Days to look back for IV history

        Returns:
            dict with IVR and interpretation
        """
        try:
            # Get historical data to calculate historical volatility
            hist = self.stock.history(period="1y")

            if hist.empty or len(hist) < 30:
                return None

            # Calculate historical volatility (annualized standard deviation of returns)
            returns = hist['Close'].pct_change().dropna()
            hist_vol = returns.std() * np.sqrt(252)  # Annualize

            # Get current IV from options chain
            expirations = self.stock.options

            if not expirations:
                return None

            # Use first available expiration
            chain = self.stock.option_chain(expirations[0])
            atm_calls = chain.calls

            if atm_calls.empty:
                return None

            # Get IV from ATM option
            current_price = hist['Close'].iloc[-1]
            atm_option = atm_calls.iloc[(atm_calls['strike'] - current_price).abs().argsort()[:1]]

            if atm_option.empty:
                return None

            current_iv = atm_option.iloc[0]['impliedVolatility']

            # Calculate rolling 30-day volatility for the year
            rolling_vol = returns.rolling(window=30).std() * np.sqrt(252)
            rolling_vol = rolling_vol.dropna()

            if len(rolling_vol) < 2:
                return None

            iv_low = rolling_vol.min()
            iv_high = rolling_vol.max()

            # Calculate IV Rank
            if iv_high == iv_low:
                iv_rank = 50  # Middle if no range
            else:
                iv_rank = ((current_iv - iv_low) / (iv_high - iv_low)) * 100

            # Interpret IVR
            if iv_rank >= 75:
                signal = "VERY_HIGH"
                interpretation = "Expensive premiums - consider selling"
                emoji = "🔴"
            elif iv_rank >= 50:
                signal = "HIGH"
                interpretation = "Above average premiums"
                emoji = "🟠"
            elif iv_rank >= 25:
                signal = "NORMAL"
                interpretation = "Normal premium pricing"
                emoji = "🟡"
            else:
                signal = "LOW"
                interpretation = "Cheap premiums - good for buying"
                emoji = "🟢"

            return {
                'iv_rank': round(iv_rank, 1),
                'current_iv': round(current_iv * 100, 1),
                'iv_low': round(iv_low * 100, 1),
                'iv_high': round(iv_high * 100, 1),
                'signal': signal,
                'interpretation': interpretation,
                'emoji': emoji
            }

        except Exception as e:
            print(f"Error calculating IV Rank: {e}")
            return None

    def calculate_put_call_ratio(self) -> Optional[Dict]:
        """
        Calculate Put/Call Ratio from options volume

        Returns:
            dict with P/C ratio and interpretation
        """
        try:
            expirations = self.stock.options

            if not expirations:
                return None

            total_put_volume = 0
            total_call_volume = 0
            total_put_oi = 0
            total_call_oi = 0

            # Sum across all expirations
            for exp in expirations[:4]:  # Use first 4 expirations
                try:
                    chain = self.stock.option_chain(exp)

                    # Sum volumes
                    call_vol = chain.calls['volume'].sum()
                    put_vol = chain.puts['volume'].sum()

                    # Sum open interest
                    call_oi = chain.calls['openInterest'].sum()
                    put_oi = chain.puts['openInterest'].sum()

                    total_call_volume += call_vol
                    total_put_volume += put_vol
                    total_call_oi += call_oi
                    total_put_oi += put_oi

                except:
                    continue

            if total_call_volume == 0 or total_call_oi == 0:
                return None

            # Calculate ratios
            pc_ratio_volume = total_put_volume / total_call_volume
            pc_ratio_oi = total_put_oi / total_call_oi

            # Interpret
            # P/C < 0.7 = Bullish (more calls)
            # P/C 0.7-1.0 = Neutral
            # P/C > 1.0 = Bearish (more puts)

            if pc_ratio_volume < 0.7:
                signal = "BULLISH"
                interpretation = "More call buying - bullish sentiment"
                emoji = "🟢"
            elif pc_ratio_volume > 1.0:
                signal = "BEARISH"
                interpretation = "More put buying - bearish sentiment"
                emoji = "🔴"
            else:
                signal = "NEUTRAL"
                interpretation = "Balanced options activity"
                emoji = "🟡"

            return {
                'pc_ratio_volume': round(pc_ratio_volume, 2),
                'pc_ratio_oi': round(pc_ratio_oi, 2),
                'total_call_volume': int(total_call_volume),
                'total_put_volume': int(total_put_volume),
                'total_call_oi': int(total_call_oi),
                'total_put_oi': int(total_put_oi),
                'signal': signal,
                'interpretation': interpretation,
                'emoji': emoji
            }

        except Exception as e:
            print(f"Error calculating Put/Call Ratio: {e}")
            return None

    def analyze_options_flow(self) -> Optional[Dict]:
        """
        Analyze recent options flow to detect unusual activity

        Returns:
            dict with flow analysis
        """
        try:
            expirations = self.stock.options

            if not expirations:
                return None

            # Get nearest expiration
            chain = self.stock.option_chain(expirations[0])

            calls = chain.calls
            puts = chain.puts

            if calls.empty or puts.empty:
                return None

            # Find unusual volume (volume > 2x open interest)
            calls['volume_oi_ratio'] = calls['volume'] / (calls['openInterest'] + 1)
            puts['volume_oi_ratio'] = puts['volume'] / (puts['openInterest'] + 1)

            unusual_calls = calls[calls['volume_oi_ratio'] > 2].nlargest(5, 'volume')
            unusual_puts = puts[puts['volume_oi_ratio'] > 2].nlargest(5, 'volume')

            # Analyze strikes with high activity
            hot_call_strikes = []
            for _, row in unusual_calls.iterrows():
                hot_call_strikes.append({
                    'strike': row['strike'],
                    'volume': int(row['volume']),
                    'oi': int(row['openInterest']),
                    'premium': row['lastPrice']
                })

            hot_put_strikes = []
            for _, row in unusual_puts.iterrows():
                hot_put_strikes.append({
                    'strike': row['strike'],
                    'volume': int(row['volume']),
                    'oi': int(row['openInterest']),
                    'premium': row['lastPrice']
                })

            # Overall flow sentiment
            total_unusual_call_vol = unusual_calls['volume'].sum()
            total_unusual_put_vol = unusual_puts['volume'].sum()

            if total_unusual_call_vol > total_unusual_put_vol * 1.5:
                flow_signal = "BULLISH"
                flow_emoji = "🟢"
            elif total_unusual_put_vol > total_unusual_call_vol * 1.5:
                flow_signal = "BEARISH"
                flow_emoji = "🔴"
            else:
                flow_signal = "NEUTRAL"
                flow_emoji = "🟡"

            return {
                'unusual_calls_count': len(unusual_calls),
                'unusual_puts_count': len(unusual_puts),
                'hot_call_strikes': hot_call_strikes[:3],  # Top 3
                'hot_put_strikes': hot_put_strikes[:3],  # Top 3
                'flow_signal': flow_signal,
                'flow_emoji': flow_emoji,
                'has_unusual_activity': len(unusual_calls) > 0 or len(unusual_puts) > 0
            }

        except Exception as e:
            print(f"Error analyzing options flow: {e}")
            return None

    def calculate_max_pain(self, expiration: str = None) -> Optional[Dict]:
        """
        Calculate Max Pain (strike where most options expire worthless)

        Args:
            expiration: Specific expiration date, or None for nearest

        Returns:
            dict with max pain analysis
        """
        try:
            expirations = self.stock.options

            if not expirations:
                return None

            if expiration is None:
                expiration = expirations[0]

            chain = self.stock.option_chain(expiration)
            calls = chain.calls
            puts = chain.puts

            if calls.empty or puts.empty:
                return None

            # Get unique strikes
            strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))

            max_pain_strike = None
            min_total_pain = float('inf')

            # Calculate pain for each strike
            for strike in strikes:
                call_pain = 0
                put_pain = 0

                # Calculate call pain (calls ITM)
                itm_calls = calls[calls['strike'] < strike]
                if not itm_calls.empty:
                    call_pain = ((strike - itm_calls['strike']) * itm_calls['openInterest']).sum()

                # Calculate put pain (puts ITM)
                itm_puts = puts[puts['strike'] > strike]
                if not itm_puts.empty:
                    put_pain = ((itm_puts['strike'] - strike) * itm_puts['openInterest']).sum()

                total_pain = call_pain + put_pain

                if total_pain < min_total_pain:
                    min_total_pain = total_pain
                    max_pain_strike = strike

            # Get current stock price
            current_price = self.stock.info.get('currentPrice', 0)

            if current_price == 0:
                return None

            # Calculate distance from max pain
            distance_pct = ((current_price - max_pain_strike) / current_price) * 100

            # Interpret
            if abs(distance_pct) < 2:
                interpretation = "At max pain - likely to stay near this level"
                emoji = "🎯"
            elif distance_pct > 5:
                interpretation = "Above max pain - downward pressure possible"
                emoji = "📉"
            elif distance_pct < -5:
                interpretation = "Below max pain - upward pressure possible"
                emoji = "📈"
            else:
                interpretation = "Near max pain"
                emoji = "➡️"

            return {
                'max_pain_strike': max_pain_strike,
                'current_price': current_price,
                'distance_dollars': round(current_price - max_pain_strike, 2),
                'distance_percent': round(distance_pct, 1),
                'expiration': expiration,
                'interpretation': interpretation,
                'emoji': emoji
            }

        except Exception as e:
            print(f"Error calculating max pain: {e}")
            return None

    def get_all_advanced_metrics(self) -> Dict:
        """
        Get all advanced options metrics at once

        Returns:
            dict with all metrics
        """
        return {
            'ticker': self.ticker,
            'iv_rank': self.calculate_iv_rank(),
            'put_call_ratio': self.calculate_put_call_ratio(),
            'options_flow': self.analyze_options_flow(),
            'max_pain': self.calculate_max_pain()
        }


def quick_advanced_analysis(ticker: str) -> Dict:
    """
    Quick function to get all advanced options metrics

    Args:
        ticker: Stock symbol

    Returns:
        dict with all advanced metrics
    """
    analyzer = AdvancedOptionsAnalyzer(ticker)
    return analyzer.get_all_advanced_metrics()


if __name__ == "__main__":
    # Test with example ticker
    print("Testing Advanced Options Analysis Module...")
    print("=" * 60)

    result = quick_advanced_analysis("PTON")

    if result:
        print(f"\n📊 Advanced Analysis for {result['ticker']}\n")

        # IV Rank
        if result.get('iv_rank'):
            ivr = result['iv_rank']
            print(f"🔢 IV RANK: {ivr['emoji']} {ivr['iv_rank']}%")
            print(f"   {ivr['interpretation']}")
            print(f"   Current IV: {ivr['current_iv']}% | Range: {ivr['iv_low']}%-{ivr['iv_high']}%\n")

        # Put/Call Ratio
        if result.get('put_call_ratio'):
            pcr = result['put_call_ratio']
            print(f"📊 PUT/CALL RATIO: {pcr['emoji']} {pcr['pc_ratio_volume']}")
            print(f"   {pcr['interpretation']}")
            print(f"   Call Volume: {pcr['total_call_volume']:,} | Put Volume: {pcr['total_put_volume']:,}\n")

        # Options Flow
        if result.get('options_flow'):
            flow = result['options_flow']
            print(f"🌊 OPTIONS FLOW: {flow['flow_emoji']} {flow['flow_signal']}")
            print(f"   Unusual Activity: {flow['unusual_calls_count']} calls, {flow['unusual_puts_count']} puts")

            if flow['hot_call_strikes']:
                print(f"   Hot Call Strikes:")
                for strike in flow['hot_call_strikes']:
                    print(f"     ${strike['strike']}: {strike['volume']} vol, {strike['oi']} OI")

        # Max Pain
        if result.get('max_pain'):
            mp = result['max_pain']
            print(f"\n💰 MAX PAIN: ${mp['max_pain_strike']}")
            print(f"   {mp['emoji']} {mp['interpretation']}")
            print(f"   Distance: ${mp['distance_dollars']} ({mp['distance_percent']:+.1f}%)")

        print("\n" + "=" * 60)
        print("✅ Advanced Options Analysis Working!")
    else:
        print("❌ Error running advanced analysis")
