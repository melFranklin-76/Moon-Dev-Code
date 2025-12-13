#!/usr/bin/env python3
"""
Ross Cameron 5-Pillar Strategy Backtester
Tests momentum day trading strategy on historical data

Based on Ross Cameron's Rules:
1. Price: $2-$20
2. Float: <20M shares
3. Relative Volume: 5x+
4. Percentage Gain: 10%+
5. News Catalyst: Breaking news
6. MACD Positive (entry validation)

Targets:
- Win Rate: 75%+
- P/L Ratio: 2:1
- Sharp Ratio: 2.0+ (Moon Dev standard)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import yfinance as yf


class RossCameronBacktest:
    def __init__(self,
                 starting_balance: float = 2000,
                 risk_per_trade: float = 0.10,
                 min_price: float = 2.0,
                 max_price: float = 20.0):
        """
        Initialize Ross Cameron strategy backtester

        Args:
            starting_balance: Starting account balance
            risk_per_trade: Risk per trade as decimal (0.10 = 10%)
            min_price: Minimum stock price
            max_price: Maximum stock price
        """
        self.starting_balance = starting_balance
        self.current_balance = starting_balance
        self.risk_per_trade = risk_per_trade
        self.min_price = min_price
        self.max_price = max_price

        self.trades = []
        self.daily_balances = []

    def fetch_historical_data(self, ticker: str, period: str = "1mo") -> pd.DataFrame:
        """
        Fetch historical price data for a stock

        Args:
            ticker: Stock symbol
            period: Time period (1mo, 3mo, 6mo, 1y)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval="5m")  # 5-minute bars for intraday

            if df.empty:
                return None

            # Calculate MACD
            df = self._calculate_macd(df)

            # Calculate relative volume
            df['Rel_Volume'] = df['Volume'] / df['Volume'].rolling(window=20).mean()

            return df

        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD indicator"""
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal

        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Histogram'] = histogram
        df['MACD_Positive'] = df['MACD_Histogram'] > 0

        return df

    def identify_pullback_pattern(self, df: pd.DataFrame, idx: int) -> bool:
        """
        Identify Ross Cameron's pullback pattern
        Surge → Pullback → New High

        Args:
            df: OHLCV DataFrame
            idx: Current bar index

        Returns:
            True if pullback pattern detected
        """
        if idx < 10:  # Need history
            return False

        # Look back 10 bars
        lookback = df.iloc[idx-10:idx]

        # Check for surge (big green candle)
        surge_bars = lookback[lookback['Close'] > lookback['Open'] * 1.02]  # 2%+ green candle
        if surge_bars.empty:
            return False

        # Check for pullback (red candles after surge)
        last_surge_idx = surge_bars.index[-1]
        after_surge = df.loc[last_surge_idx:idx]

        if len(after_surge) < 3:
            return False

        # Pullback = at least one red candle
        pullback_bars = after_surge[after_surge['Close'] < after_surge['Open']]
        if pullback_bars.empty:
            return False

        # Current bar trying to make new high
        current_high = df.loc[idx, 'High']
        recent_high = lookback['High'].max()

        return current_high >= recent_high * 0.98  # Within 2% of recent high

    def simulate_trade(self,
                      ticker: str,
                      entry_price: float,
                      entry_time: datetime,
                      df: pd.DataFrame,
                      idx: int) -> Dict:
        """
        Simulate a trade with Ross's rules

        Args:
            ticker: Stock symbol
            entry_price: Entry price
            entry_time: Entry timestamp
            df: OHLCV DataFrame
            idx: Entry bar index

        Returns:
            Trade result dictionary
        """
        # Calculate position size (10% risk, 2% stop loss)
        stop_loss_pct = 0.02  # 2% stop
        risk_dollars = self.current_balance * self.risk_per_trade
        shares = int(risk_dollars / (entry_price * stop_loss_pct))

        # Buying power constraint (98% for Webull)
        max_shares = int((self.current_balance * 0.98) / entry_price)
        shares = min(shares, max_shares)

        if shares == 0:
            return None

        # Set profit targets (Ross's levels)
        stop_loss = entry_price * 0.98  # 2% stop
        target_1 = entry_price * 1.05  # 5% target
        target_2 = entry_price * 1.10  # 10% target

        # Simulate forward (max 30 minutes hold time)
        max_bars = min(idx + 6, len(df))  # 6 bars = 30 min (5-min bars)

        exit_price = None
        exit_time = None
        exit_reason = None

        for i in range(idx + 1, max_bars):
            bar = df.iloc[i]

            # Check stop loss
            if bar['Low'] <= stop_loss:
                exit_price = stop_loss
                exit_time = df.index[i]
                exit_reason = "STOP_LOSS"
                break

            # Check profit targets
            if bar['High'] >= target_2:
                exit_price = target_2
                exit_time = df.index[i]
                exit_reason = "TARGET_2"
                break
            elif bar['High'] >= target_1:
                exit_price = target_1
                exit_time = df.index[i]
                exit_reason = "TARGET_1"
                break

            # Check MACD turning negative (exit signal)
            if bar['MACD_Positive'] == False:
                exit_price = bar['Close']
                exit_time = df.index[i]
                exit_reason = "MACD_NEGATIVE"
                break

        # If no exit trigger, exit at end of hold time
        if exit_price is None:
            exit_price = df.iloc[max_bars - 1]['Close']
            exit_time = df.index[max_bars - 1]
            exit_reason = "TIME_LIMIT"

        # Calculate P&L
        gross_pnl = (exit_price - entry_price) * shares
        net_pnl = gross_pnl  # Commission-free broker (Webull)

        # Update balance
        self.current_balance += net_pnl

        trade = {
            'ticker': ticker,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'shares': shares,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'exit_reason': exit_reason,
            'result': 'WIN' if net_pnl > 0 else 'LOSS',
            'hold_minutes': (exit_time - entry_time).total_seconds() / 60
        }

        self.trades.append(trade)
        self.daily_balances.append({
            'date': entry_time.date(),
            'balance': self.current_balance
        })

        return trade

    def backtest_ticker(self, ticker: str, period: str = "1mo") -> List[Dict]:
        """
        Backtest Ross's strategy on a single ticker

        Args:
            ticker: Stock symbol
            period: Time period to test

        Returns:
            List of trades executed
        """
        print(f"\n📊 Backtesting {ticker}...")

        df = self.fetch_historical_data(ticker, period)

        if df is None or df.empty:
            print(f"   ❌ No data available")
            return []

        ticker_trades = []

        # Scan for entry signals
        for idx in range(10, len(df)):
            bar = df.iloc[idx]

            # Filter 1: Price range
            if not (self.min_price <= bar['Close'] <= self.max_price):
                continue

            # Filter 2: MACD positive
            if not bar['MACD_Positive']:
                continue

            # Filter 3: Relative volume (5x+)
            if pd.isna(bar['Rel_Volume']) or bar['Rel_Volume'] < 5.0:
                continue

            # Filter 4: Pullback pattern
            if not self.identify_pullback_pattern(df, idx):
                continue

            # Valid entry signal - simulate trade
            trade = self.simulate_trade(
                ticker=ticker,
                entry_price=bar['Close'],
                entry_time=df.index[idx],
                df=df,
                idx=idx
            )

            if trade:
                ticker_trades.append(trade)
                result_emoji = "✅" if trade['result'] == 'WIN' else "❌"
                print(f"   {result_emoji} Trade: Entry ${trade['entry_price']:.2f} → Exit ${trade['exit_price']:.2f} | P&L: ${trade['net_pnl']:+.2f}")

        print(f"   Total trades: {len(ticker_trades)}")
        return ticker_trades

    def backtest_watchlist(self, tickers: List[str], period: str = "1mo"):
        """
        Backtest Ross's strategy on multiple tickers

        Args:
            tickers: List of stock symbols
            period: Time period to test
        """
        print(f"\n{'='*80}")
        print(f"🚀 BACKTESTING ROSS CAMERON 5-PILLAR STRATEGY")
        print(f"{'='*80}")
        print(f"Starting Balance: ${self.starting_balance:,.2f}")
        print(f"Risk Per Trade: {self.risk_per_trade * 100}%")
        print(f"Period: {period}")
        print(f"{'='*80}")

        for ticker in tickers:
            self.backtest_ticker(ticker, period)

        # Display results
        self.display_results()

    def display_results(self):
        """Display backtest results"""
        if not self.trades:
            print("\n❌ No trades executed during backtest")
            return

        df = pd.DataFrame(self.trades)

        wins = df[df['result'] == 'WIN']
        losses = df[df['result'] == 'LOSS']

        total_trades = len(df)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0

        total_pnl = df['net_pnl'].sum()
        avg_win = wins['net_pnl'].mean() if not wins.empty else 0
        avg_loss = losses['net_pnl'].mean() if not losses.empty else 0
        pl_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        # Calculate sharp ratio (simplified)
        returns = df['net_pnl'] / self.starting_balance
        sharp_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0

        # Calculate max drawdown
        balances = [self.starting_balance]
        for trade in self.trades:
            balances.append(balances[-1] + trade['net_pnl'])

        peak = balances[0]
        max_dd = 0
        for balance in balances:
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100
            if dd > max_dd:
                max_dd = dd

        print(f"\n{'='*80}")
        print(f"📈 BACKTEST RESULTS")
        print(f"{'='*80}")

        print(f"\n💰 ACCOUNT PERFORMANCE:")
        print(f"   Starting Balance: ${self.starting_balance:,.2f}")
        print(f"   Ending Balance: ${self.current_balance:,.2f}")
        print(f"   Total P&L: ${total_pnl:+,.2f}")
        print(f"   Return: {(total_pnl / self.starting_balance * 100):+.2f}%")

        print(f"\n📊 TRADE STATISTICS:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Winning Trades: {win_count}")
        print(f"   Losing Trades: {loss_count}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Target: 75% (Ross Cameron standard)")

        print(f"\n💵 PROFIT & LOSS:")
        print(f"   Average Win: ${avg_win:,.2f}")
        print(f"   Average Loss: ${avg_loss:,.2f}")
        print(f"   P/L Ratio: {pl_ratio:.2f}:1")
        print(f"   Target: 2:1 (Ross Cameron standard)")

        print(f"\n📉 RISK METRICS:")
        print(f"   Max Drawdown: {max_dd:.2f}%")
        print(f"   Sharp Ratio: {sharp_ratio:.2f}")
        print(f"   Target: 2.0+ (Moon Dev standard)")

        print(f"\n⏱️  HOLD TIME:")
        print(f"   Average Hold: {df['hold_minutes'].mean():.1f} minutes")
        print(f"   Max Hold: {df['hold_minutes'].max():.1f} minutes")

        # Exit reason breakdown
        print(f"\n🚪 EXIT REASONS:")
        exit_counts = df['exit_reason'].value_counts()
        for reason, count in exit_counts.items():
            print(f"   {reason}: {count} ({count/total_trades*100:.1f}%)")

        print(f"\n{'='*80}")

        # Performance assessment
        print(f"\n💡 STRATEGY ASSESSMENT:")
        if win_rate >= 75 and pl_ratio >= 2.0 and sharp_ratio >= 2.0:
            print(f"   ✅ EXCELLENT: Strategy meets all targets!")
            print(f"   Ready for live trading automation.")
        elif win_rate >= 75 and pl_ratio >= 1.5:
            print(f"   ✅ GOOD: Strategy shows promise.")
            print(f"   Consider refining exit rules to improve P/L ratio.")
        elif win_rate >= 60:
            print(f"   ⚠️  MODERATE: Strategy has potential but needs work.")
            print(f"   Focus on improving setup quality and entry timing.")
        else:
            print(f"   ❌ POOR: Strategy underperforming.")
            print(f"   Review entry criteria and risk management rules.")

        print(f"\n{'='*80}\n")

    def plot_results(self, save_path: str = "backtest_results.png"):
        """Plot backtest results"""
        if not self.trades:
            print("\n❌ No trades to plot")
            return

        df = pd.DataFrame(self.trades)

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

        # Plot 1: Equity curve
        balances = [self.starting_balance]
        for trade in self.trades:
            balances.append(balances[-1] + trade['net_pnl'])

        ax1.plot(balances, linewidth=2)
        ax1.axhline(y=self.starting_balance, color='gray', linestyle='--', alpha=0.5)
        ax1.set_title('Equity Curve', fontweight='bold')
        ax1.set_xlabel('Trade Number')
        ax1.set_ylabel('Account Balance ($)')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Win/Loss distribution
        colors = ['green' if x == 'WIN' else 'red' for x in df['result']]
        ax2.bar(range(len(df)), df['net_pnl'], color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_title('Trade P&L Distribution', fontweight='bold')
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('P&L ($)')
        ax2.grid(True, alpha=0.3)

        # Plot 3: Exit reasons
        exit_counts = df['exit_reason'].value_counts()
        ax3.pie(exit_counts.values, labels=exit_counts.index, autopct='%1.1f%%')
        ax3.set_title('Exit Reasons', fontweight='bold')

        # Plot 4: Hold time distribution
        ax4.hist(df['hold_minutes'], bins=20, color='blue', alpha=0.7, edgecolor='black')
        ax4.set_title('Hold Time Distribution', fontweight='bold')
        ax4.set_xlabel('Hold Time (minutes)')
        ax4.set_ylabel('Frequency')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 Chart saved to {save_path}")
        plt.close()


def main():
    """Example usage"""
    # Initialize backtester
    backtester = RossCameronBacktest(
        starting_balance=2000,
        risk_per_trade=0.10,
        min_price=2.0,
        max_price=20.0
    )

    # Example watchlist (momentum stocks)
    watchlist = [
        'AMD', 'NVDA', 'TSLA', 'AAPL', 'MSFT'
    ]

    print("\n⚠️  NOTE: This backtester uses 5-minute intraday data.")
    print("For best results, use stocks that have shown recent momentum.\n")

    # Run backtest
    backtester.backtest_watchlist(watchlist, period="1mo")

    # Plot results
    # backtester.plot_results()


if __name__ == "__main__":
    main()
