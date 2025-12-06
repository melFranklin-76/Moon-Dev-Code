#!/usr/bin/env python3
"""
OPTIONS POSITION CALCULATOR - Professional Grade
Ross Cameron 5-Pillar Strategy Optimized for Options Trading

Features:
- Smart contract quantity calculation based on risk
- Greeks analysis (Delta, Theta, Gamma, Vega)
- Multiple strike price comparison
- Bid/ask spread analysis
- Break-even calculator
- Risk/reward visualization
- Position sizing for small accounts ($2K-$10K)

Based on:
- Ross Cameron's momentum day trading strategy
- Professional options trading risk management
- Small account protection (max 5% risk per trade)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math


class OptionsPositionCalculator:
    def __init__(self, account_balance: float = 2000, max_risk_percent: float = 5.0):
        """
        Initialize Options Position Calculator

        Args:
            account_balance: Current account balance
            max_risk_percent: Max risk per trade (default 5% for options)
        """
        self.account_balance = account_balance
        self.max_risk_percent = max_risk_percent
        self.max_risk_dollars = account_balance * (max_risk_percent / 100)

        print(f"\n{'='*80}")
        print(f"💰 OPTIONS POSITION CALCULATOR")
        print(f"{'='*80}")
        print(f"Account Balance: ${self.account_balance:,.2f}")
        print(f"Max Risk per Trade: {self.max_risk_percent}% (${self.max_risk_dollars:,.2f})")
        print(f"{'='*80}\n")

    def get_option_chain(self, ticker: str, expiration_date: str = None) -> pd.DataFrame:
        """
        Fetch option chain for a ticker

        Args:
            ticker: Stock symbol
            expiration_date: Expiration date (YYYY-MM-DD) or None for nearest

        Returns:
            DataFrame with calls option chain
        """
        try:
            stock = yf.Ticker(ticker)

            # Get available expiration dates
            expirations = stock.options

            if not expirations:
                print(f"❌ No options available for {ticker}")
                return None

            # Use specified expiration or nearest one
            if expiration_date:
                exp_date = expiration_date
            else:
                # Find nearest weekly expiration (within 7 days)
                today = datetime.now()
                nearest_exp = None
                for exp in expirations:
                    exp_dt = datetime.strptime(exp, '%Y-%m-%d')
                    days_away = (exp_dt - today).days
                    if 0 <= days_away <= 7:
                        nearest_exp = exp
                        break

                if not nearest_exp:
                    nearest_exp = expirations[0]  # Use first available

                exp_date = nearest_exp

            # Get option chain for expiration
            opt_chain = stock.option_chain(exp_date)
            calls = opt_chain.calls

            # Add calculated fields
            calls['expiration'] = exp_date
            calls['daysToExpiration'] = (datetime.strptime(exp_date, '%Y-%m-%d') - datetime.now()).days
            calls['spread'] = calls['ask'] - calls['bid']
            calls['spreadPercent'] = (calls['spread'] / calls['ask'] * 100).round(2)

            return calls

        except Exception as e:
            print(f"❌ Error fetching options for {ticker}: {e}")
            return None

    def calculate_greeks_simple(self,
                                stock_price: float,
                                strike: float,
                                premium: float,
                                days_to_expiration: int) -> Dict[str, float]:
        """
        Calculate simplified Greeks for educational purposes

        Note: These are approximations for educational use.
        For live trading, use broker's Greeks or professional options pricing library.

        Args:
            stock_price: Current stock price
            strike: Option strike price
            premium: Option premium (price)
            days_to_expiration: Days until expiration

        Returns:
            Dictionary with approximate Greeks
        """
        # Intrinsic value
        intrinsic = max(0, stock_price - strike)

        # Extrinsic (time) value
        extrinsic = premium - intrinsic

        # Delta approximation (how much option moves per $1 stock move)
        # ITM options: 0.6-1.0, ATM: ~0.5, OTM: 0.0-0.4
        moneyness = stock_price / strike
        if moneyness >= 1.05:  # 5% ITM
            delta = 0.70 + (moneyness - 1.05) * 2
            delta = min(delta, 0.95)
        elif moneyness >= 0.95:  # ATM range
            delta = 0.50
        else:  # OTM
            delta = 0.30 * moneyness

        # Theta approximation (daily time decay)
        # More decay as expiration approaches
        if days_to_expiration > 0:
            theta = -extrinsic / days_to_expiration
        else:
            theta = -premium  # Last day, all extrinsic value lost

        # Gamma approximation (rate of delta change)
        # Highest for ATM options
        if 0.95 <= moneyness <= 1.05:  # ATM
            gamma = 0.05
        else:
            gamma = 0.02

        # Vega approximation (sensitivity to IV changes)
        # Higher for longer-dated options
        vega = extrinsic * 0.1 * (days_to_expiration / 30)

        return {
            'delta': round(delta, 3),
            'theta': round(theta, 3),
            'gamma': round(gamma, 3),
            'vega': round(vega, 3),
            'intrinsic': round(intrinsic, 2),
            'extrinsic': round(extrinsic, 2)
        }

    def analyze_strike(self,
                      ticker: str,
                      strike: float,
                      expiration: str,
                      stock_price: float) -> Dict:
        """
        Analyze a specific strike price

        Args:
            ticker: Stock symbol
            strike: Strike price to analyze
            expiration: Expiration date
            stock_price: Current stock price

        Returns:
            Analysis dictionary
        """
        # Get option chain
        chain = self.get_option_chain(ticker, expiration)

        if chain is None or chain.empty:
            return None

        # Find the strike
        strike_data = chain[chain['strike'] == strike]

        if strike_data.empty:
            print(f"❌ Strike ${strike} not found")
            return None

        row = strike_data.iloc[0]

        # Calculate Greeks
        greeks = self.calculate_greeks_simple(
            stock_price=stock_price,
            strike=strike,
            premium=row['lastPrice'],
            days_to_expiration=row['daysToExpiration']
        )

        # Position sizing
        premium = row['ask']  # Use ask price (what you'll pay)
        contracts = int(self.max_risk_dollars / (premium * 100))
        contracts = max(1, contracts)  # At least 1 contract

        total_cost = premium * contracts * 100

        # Break-even calculation
        break_even = strike + premium

        # Profit targets (10%, 20%, 30% stock moves)
        targets = []
        for pct in [10, 20, 30]:
            target_stock_price = stock_price * (1 + pct/100)
            target_intrinsic = max(0, target_stock_price - strike)
            # Assume some time decay
            days_passed = min(3, row['daysToExpiration'] // 2)
            remaining_extrinsic = max(0, greeks['extrinsic'] - (abs(greeks['theta']) * days_passed))
            target_premium = target_intrinsic + remaining_extrinsic

            profit = (target_premium - premium) * contracts * 100
            profit_pct = (target_premium / premium - 1) * 100

            targets.append({
                'stock_move_pct': pct,
                'target_stock_price': target_stock_price,
                'target_premium': target_premium,
                'profit': profit,
                'profit_pct': profit_pct,
                'account_growth': (profit / self.account_balance) * 100
            })

        analysis = {
            'ticker': ticker,
            'stock_price': stock_price,
            'strike': strike,
            'expiration': expiration,
            'days_to_expiration': row['daysToExpiration'],
            'bid': row['bid'],
            'ask': row['ask'],
            'last': row['lastPrice'],
            'spread': row['spread'],
            'spread_pct': row['spreadPercent'],
            'volume': row['volume'],
            'open_interest': row['openInterest'],
            'implied_volatility': row['impliedVolatility'],
            'greeks': greeks,
            'recommended_contracts': contracts,
            'total_cost': total_cost,
            'max_loss': total_cost,
            'break_even': break_even,
            'break_even_move_pct': ((break_even / stock_price) - 1) * 100,
            'profit_targets': targets
        }

        return analysis

    def compare_strikes(self,
                       ticker: str,
                       expiration: str,
                       stock_price: float,
                       strikes: List[float] = None) -> pd.DataFrame:
        """
        Compare multiple strike prices

        Args:
            ticker: Stock symbol
            expiration: Expiration date
            stock_price: Current stock price
            strikes: List of strikes to compare (or None for auto-select)

        Returns:
            DataFrame comparing strikes
        """
        # Get option chain
        chain = self.get_option_chain(ticker, expiration)

        if chain is None or chain.empty:
            return None

        # Auto-select strikes if not provided
        if strikes is None:
            # Select: 1 ITM, 1 ATM, 1 OTM
            strikes = []

            # ITM: strike below stock price
            itm = chain[chain['strike'] < stock_price * 0.95].sort_values('strike', ascending=False)
            if not itm.empty:
                strikes.append(itm.iloc[0]['strike'])

            # ATM: strike near stock price
            atm = chain[(chain['strike'] >= stock_price * 0.95) &
                       (chain['strike'] <= stock_price * 1.05)].sort_values(
                           lambda x: abs(x - stock_price))
            if not atm.empty:
                strikes.append(atm.iloc[0]['strike'])

            # OTM: strike above stock price
            otm = chain[chain['strike'] > stock_price * 1.05].sort_values('strike')
            if not otm.empty:
                strikes.append(otm.iloc[0]['strike'])

        # Analyze each strike
        comparisons = []
        for strike in strikes:
            analysis = self.analyze_strike(ticker, strike, expiration, stock_price)
            if analysis:
                comparisons.append({
                    'Strike': f"${strike}",
                    'Type': 'ITM' if strike < stock_price else ('ATM' if abs(strike - stock_price) < stock_price * 0.05 else 'OTM'),
                    'Premium': f"${analysis['ask']:.2f}",
                    'Delta': analysis['greeks']['delta'],
                    'Theta': f"${analysis['greeks']['theta']:.2f}",
                    'Spread': f"${analysis['spread']:.2f} ({analysis['spread_pct']:.1f}%)",
                    'Contracts': analysis['recommended_contracts'],
                    'Cost': f"${analysis['total_cost']:.2f}",
                    'Break-even': f"${analysis['break_even']:.2f} (+{analysis['break_even_move_pct']:.1f}%)",
                    '10% Move Profit': f"${analysis['profit_targets'][0]['profit']:.0f} ({analysis['profit_targets'][0]['profit_pct']:.0f}%)",
                    '20% Move Profit': f"${analysis['profit_targets'][1]['profit']:.0f} ({analysis['profit_targets'][1]['profit_pct']:.0f}%)",
                })

        return pd.DataFrame(comparisons)

    def display_analysis(self, analysis: Dict):
        """Display comprehensive analysis"""
        if not analysis:
            return

        print(f"\n{'='*80}")
        print(f"📊 OPTIONS ANALYSIS: {analysis['ticker']}")
        print(f"{'='*80}\n")

        # Stock info
        print(f"📈 STOCK INFORMATION:")
        print(f"   Current Price: ${analysis['stock_price']:.2f}")
        print(f"")

        # Contract details
        print(f"📋 CONTRACT DETAILS:")
        print(f"   Strike: ${analysis['strike']}")
        print(f"   Expiration: {analysis['expiration']} ({analysis['days_to_expiration']} days)")
        print(f"   Type: {'ITM' if analysis['strike'] < analysis['stock_price'] else 'OTM'}")
        print(f"")

        # Pricing
        print(f"💰 PRICING:")
        print(f"   Bid: ${analysis['bid']:.2f}")
        print(f"   Ask: ${analysis['ask']:.2f}")
        print(f"   Last: ${analysis['last']:.2f}")
        print(f"   Spread: ${analysis['spread']:.2f} ({analysis['spread_pct']:.1f}%)")

        if analysis['spread_pct'] > 10:
            print(f"   ⚠️  WARNING: Wide spread! May be hard to exit")
        elif analysis['spread_pct'] < 5:
            print(f"   ✅ GOOD: Tight spread, liquid option")
        print(f"")

        # Liquidity
        print(f"💧 LIQUIDITY:")
        print(f"   Volume: {analysis['volume']:,}")
        print(f"   Open Interest: {analysis['open_interest']:,}")

        if analysis['open_interest'] < 100:
            print(f"   ⚠️  WARNING: Low open interest, may be illiquid")
        elif analysis['open_interest'] > 500:
            print(f"   ✅ EXCELLENT: High liquidity")
        print(f"")

        # Greeks
        g = analysis['greeks']
        print(f"🔢 THE GREEKS:")
        print(f"   Delta: {g['delta']:.3f} (option moves ${g['delta']:.2f} per $1 stock move)")
        print(f"   Theta: ${g['theta']:.2f}/day (you lose ${abs(g['theta']):.2f} every day)")
        print(f"   Gamma: {g['gamma']:.3f} (delta acceleration)")
        print(f"   Intrinsic: ${g['intrinsic']:.2f} | Extrinsic: ${g['extrinsic']:.2f}")
        print(f"")

        # Position sizing
        print(f"🎯 RECOMMENDED POSITION:")
        print(f"   Contracts: {analysis['recommended_contracts']}")
        print(f"   Total Cost: ${analysis['total_cost']:.2f}")
        print(f"   Max Loss: ${analysis['max_loss']:.2f} (100% of premium)")
        print(f"   % of Account: {(analysis['total_cost'] / self.account_balance * 100):.1f}%")
        print(f"")

        # Break-even
        print(f"⚖️  BREAK-EVEN:")
        print(f"   Stock must reach: ${analysis['break_even']:.2f}")
        print(f"   Stock must move: +{analysis['break_even_move_pct']:.1f}%")
        print(f"")

        # Profit targets
        print(f"💵 PROFIT TARGETS:")
        for target in analysis['profit_targets']:
            print(f"\n   If stock moves +{target['stock_move_pct']}% to ${target['target_stock_price']:.2f}:")
            print(f"   Option premium: ${target['target_premium']:.2f}")
            print(f"   Profit: ${target['profit']:.0f} (+{target['profit_pct']:.0f}% on options)")
            print(f"   Account Growth: +{target['account_growth']:.1f}%")

            if target['account_growth'] >= 10:
                print(f"   ✅ HITS 10% ACCOUNT GOAL!")

        print(f"\n{'='*80}\n")

    def quick_scan(self, ticker: str, stock_price: float = None) -> Dict:
        """
        Quick scan for best option to trade

        Args:
            ticker: Stock symbol
            stock_price: Current stock price (or fetch automatically)

        Returns:
            Analysis of recommended option
        """
        # Get stock price if not provided
        if stock_price is None:
            try:
                stock = yf.Ticker(ticker)
                stock_price = stock.info['currentPrice']
            except:
                print(f"❌ Could not fetch price for {ticker}")
                return None

        # Get nearest weekly expiration
        chain = self.get_option_chain(ticker)

        if chain is None or chain.empty:
            return None

        expiration = chain.iloc[0]['expiration']

        # Find best strike: slightly ITM or ATM
        # Ross Cameron preference: ITM options with high delta
        target_strike = stock_price * 0.98  # 2% ITM

        best_strike = chain.iloc[(chain['strike'] - target_strike).abs().argsort()[:1]]['strike'].values[0]

        # Analyze this strike
        analysis = self.analyze_strike(ticker, best_strike, expiration, stock_price)

        return analysis


def main():
    """Example usage"""
    print("\n🚀 ROSS CAMERON OPTIONS POSITION CALCULATOR")
    print("Optimized for Small Account Momentum Trading\n")

    # Initialize calculator
    calc = OptionsPositionCalculator(account_balance=2800, max_risk_percent=5.0)

    # Example: Analyze PTON options
    ticker = input("Enter ticker symbol (or press Enter for demo with PTON): ").strip().upper()
    if not ticker:
        ticker = "PTON"
        stock_price = 6.05
        print(f"\n📊 Demo Mode: Analyzing {ticker} at ${stock_price}")
    else:
        try:
            stock = yf.Ticker(ticker)
            stock_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
            print(f"\n📊 Current {ticker} price: ${stock_price:.2f}")
        except:
            print(f"❌ Error fetching {ticker} price")
            return

    # Quick scan for best option
    print(f"\n🔍 Finding best option for {ticker}...\n")
    analysis = calc.quick_scan(ticker, stock_price)

    if analysis:
        calc.display_analysis(analysis)

        # Show comparison
        print(f"\n📊 COMPARING DIFFERENT STRIKES:")
        comparison = calc.compare_strikes(ticker, analysis['expiration'], stock_price)
        if comparison is not None:
            print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
