#!/usr/bin/env python3
"""
OPTIONS TRADE JOURNAL - Professional Grade
Track every options trade with complete details

Features:
- Options-specific fields (strike, expiration, premium, contracts)
- Greeks tracking at entry and exit
- Implied volatility (IV) monitoring
- Underlying stock movement tracking
- Time decay (theta) impact analysis
- Pattern recognition for options
- Export to CSV for analysis
- Performance metrics by option type

Based on Ross Cameron's momentum trading adapted for options
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os


class OptionsTradeJournal:
    def __init__(self, journal_file: str = "options_trades.json"):
        """
        Initialize Options Trade Journal

        Args:
            journal_file: Path to JSON file for storing trades
        """
        self.journal_file = Path(journal_file)
        self.trades = self._load_trades()

    def _load_trades(self) -> List[Dict]:
        """Load trades from JSON file"""
        if self.journal_file.exists():
            with open(self.journal_file, 'r') as f:
                return json.load(f)
        return []

    def _save_trades(self):
        """Save trades to JSON file"""
        with open(self.journal_file, 'w') as f:
            json.dump(self.trades, f, indent=2)

    def add_trade(self,
                  # Basic info
                  ticker: str,
                  date: str = None,

                  # Option contract details
                  strike: float = None,
                  expiration: str = None,
                  contract_type: str = "CALL",  # CALL or PUT

                  # Entry details
                  entry_premium: float = None,
                  entry_time: str = None,
                  contracts: int = 1,
                  entry_stock_price: float = None,

                  # Exit details
                  exit_premium: float = None,
                  exit_time: str = None,
                  exit_stock_price: float = None,

                  # Greeks at entry
                  entry_delta: float = None,
                  entry_theta: float = None,
                  entry_gamma: float = None,
                  entry_vega: float = None,
                  entry_iv: float = None,  # Implied volatility

                  # Greeks at exit (optional)
                  exit_delta: float = None,
                  exit_theta: float = None,
                  exit_iv: float = None,

                  # Strategy details
                  pattern: str = "Pullback",
                  macd_positive: bool = True,
                  setup_quality: int = 5,

                  # Risk management
                  days_to_expiration: int = None,
                  exit_reason: str = "TARGET_HIT",

                  # Notes
                  notes: str = "") -> Dict:
        """
        Add a new options trade to the journal

        Args:
            ticker: Stock symbol
            date: Trade date (YYYY-MM-DD) or None for today
            strike: Option strike price
            expiration: Option expiration date (YYYY-MM-DD)
            contract_type: "CALL" or "PUT"
            entry_premium: Premium paid per contract
            entry_time: Entry time (HH:MM)
            contracts: Number of contracts traded
            entry_stock_price: Stock price at entry
            exit_premium: Premium received per contract
            exit_time: Exit time (HH:MM)
            exit_stock_price: Stock price at exit
            entry_delta: Delta at entry
            entry_theta: Theta at entry
            entry_gamma: Gamma at entry
            entry_vega: Vega at entry
            entry_iv: Implied volatility at entry
            exit_delta: Delta at exit
            exit_theta: Theta at exit
            exit_iv: Implied volatility at exit
            pattern: Chart pattern (Pullback, Breakout, etc.)
            macd_positive: Was MACD positive at entry?
            setup_quality: Quality rating 1-5 stars
            days_to_expiration: Days until option expires
            exit_reason: Why you exited (TARGET_HIT, STOP_LOSS, etc.)
            notes: Additional notes

        Returns:
            Trade dictionary that was added
        """
        # Use today's date if not provided
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # Calculate P&L
        gross_pnl = (exit_premium - entry_premium) * contracts * 100
        net_pnl = gross_pnl  # Assume commission-free (Webull, Robinhood, etc.)

        # Calculate returns
        total_cost = entry_premium * contracts * 100
        return_pct = (gross_pnl / total_cost * 100) if total_cost > 0 else 0

        # Stock movement
        stock_move_pct = ((exit_stock_price / entry_stock_price) - 1) * 100 if entry_stock_price and exit_stock_price else None

        # Calculate hold time
        if entry_time and exit_time:
            try:
                entry_dt = datetime.strptime(f"{date} {entry_time}", '%Y-%m-%d %H:%M')
                exit_dt = datetime.strptime(f"{date} {exit_time}", '%Y-%m-%d %H:%M')
                hold_minutes = (exit_dt - entry_dt).total_seconds() / 60
            except:
                hold_minutes = None
        else:
            hold_minutes = None

        # Theta decay impact (how much you lost to time decay)
        if entry_theta and hold_minutes:
            theta_impact = entry_theta * (hold_minutes / (24 * 60)) * contracts * 100
        else:
            theta_impact = None

        # Determine result
        result = "WIN" if gross_pnl > 0 else "LOSS" if gross_pnl < 0 else "BREAK_EVEN"

        trade = {
            # Basic info
            'date': date,
            'ticker': ticker,

            # Contract details
            'contract_type': contract_type.upper(),
            'strike': strike,
            'expiration': expiration,
            'days_to_expiration': days_to_expiration,

            # Entry
            'entry_time': entry_time,
            'entry_premium': entry_premium,
            'entry_stock_price': entry_stock_price,
            'contracts': contracts,

            # Exit
            'exit_time': exit_time,
            'exit_premium': exit_premium,
            'exit_stock_price': exit_stock_price,
            'exit_reason': exit_reason,

            # P&L
            'gross_pnl': round(gross_pnl, 2),
            'net_pnl': round(net_pnl, 2),
            'return_pct': round(return_pct, 2),
            'result': result,

            # Stock movement
            'stock_move_pct': round(stock_move_pct, 2) if stock_move_pct else None,

            # Greeks at entry
            'entry_delta': entry_delta,
            'entry_theta': entry_theta,
            'entry_gamma': entry_gamma,
            'entry_vega': entry_vega,
            'entry_iv': entry_iv,

            # Greeks at exit
            'exit_delta': exit_delta,
            'exit_theta': exit_theta,
            'exit_iv': exit_iv,

            # Analysis
            'hold_minutes': round(hold_minutes, 1) if hold_minutes else None,
            'theta_impact': round(theta_impact, 2) if theta_impact else None,

            # Strategy
            'pattern': pattern,
            'macd_positive': macd_positive,
            'setup_quality': setup_quality,

            # Notes
            'notes': notes
        }

        self.trades.append(trade)
        self._save_trades()

        print(f"\n✅ Trade logged successfully!")
        print(f"   {ticker} ${strike} {contract_type} exp {expiration}")
        print(f"   {contracts} contracts @ ${entry_premium:.2f} → ${exit_premium:.2f}")
        print(f"   P&L: ${net_pnl:+,.2f} ({return_pct:+.1f}%)")
        print(f"   Result: {result}")

        return trade

    def view_trades(self, limit: int = None) -> pd.DataFrame:
        """
        View all trades as DataFrame

        Args:
            limit: Number of recent trades to show (None for all)

        Returns:
            DataFrame of trades
        """
        if not self.trades:
            print("\n📒 No trades logged yet")
            return pd.DataFrame()

        df = pd.DataFrame(self.trades)

        if limit:
            df = df.tail(limit)

        return df

    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        if not self.trades:
            return {}

        df = pd.DataFrame(self.trades)

        winners = df[df['result'] == 'WIN']
        losers = df[df['result'] == 'LOSS']

        total_trades = len(df)
        win_count = len(winners)
        loss_count = len(losers)

        stats = {
            'total_trades': total_trades,
            'winners': win_count,
            'losers': loss_count,
            'win_rate': (win_count / total_trades * 100) if total_trades > 0 else 0,

            'total_pnl': df['net_pnl'].sum(),
            'avg_pnl': df['net_pnl'].mean(),
            'avg_win': winners['net_pnl'].mean() if not winners.empty else 0,
            'avg_loss': losers['net_pnl'].mean() if not losers.empty else 0,

            'avg_return_pct': df['return_pct'].mean(),
            'avg_win_pct': winners['return_pct'].mean() if not winners.empty else 0,
            'avg_loss_pct': losers['return_pct'].mean() if not losers.empty else 0,

            'best_trade': df['net_pnl'].max(),
            'worst_trade': df['net_pnl'].min(),

            'avg_hold_time': df['hold_minutes'].mean() if 'hold_minutes' in df else None,

            'total_theta_decay': df['theta_impact'].sum() if 'theta_impact' in df else None,
        }

        # P/L ratio
        if stats['avg_loss'] != 0:
            stats['pl_ratio'] = abs(stats['avg_win'] / stats['avg_loss'])
        else:
            stats['pl_ratio'] = 0

        return stats

    def display_summary(self):
        """Display summary statistics"""
        if not self.trades:
            print("\n📒 No trades logged yet. Start trading and log your first trade!")
            return

        stats = self.get_summary_stats()

        print(f"\n{'='*80}")
        print(f"📊 OPTIONS TRADING PERFORMANCE SUMMARY")
        print(f"{'='*80}\n")

        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Winners: {stats['winners']} | Losers: {stats['losers']}")
        print(f"   Win Rate: {stats['win_rate']:.1f}%")

        if stats['win_rate'] >= 75:
            print(f"   ✅ EXCELLENT! Above Ross Cameron's 75% target")
        elif stats['win_rate'] >= 60:
            print(f"   ⚠️  GOOD! Getting closer to 75% target")
        else:
            print(f"   ❌ NEEDS WORK! Focus on 5-star setups only")

        print(f"\n💰 PROFIT & LOSS:")
        print(f"   Total P&L: ${stats['total_pnl']:+,.2f}")
        print(f"   Average P&L: ${stats['avg_pnl']:+,.2f}")
        print(f"   Average Win: ${stats['avg_win']:,.2f} (+{stats['avg_win_pct']:.1f}%)")
        print(f"   Average Loss: ${stats['avg_loss']:,.2f} ({stats['avg_loss_pct']:.1f}%)")
        print(f"   P/L Ratio: {stats['pl_ratio']:.2f}:1")

        if stats['pl_ratio'] >= 2.0:
            print(f"   ✅ EXCELLENT! Above 2:1 target")
        else:
            print(f"   ⚠️  NEEDS WORK! Target is 2:1 ratio")

        print(f"\n🏆 BEST & WORST:")
        print(f"   Best Trade: ${stats['best_trade']:+,.2f}")
        print(f"   Worst Trade: ${stats['worst_trade']:+,.2f}")

        if stats['avg_hold_time']:
            print(f"\n⏱️  HOLD TIME:")
            print(f"   Average Hold: {stats['avg_hold_time']:.1f} minutes")

            if stats['avg_hold_time'] <= 30:
                print(f"   ✅ GOOD! Quick scalps as planned")
            else:
                print(f"   ⚠️  HOLDING TOO LONG! Options decay, get in/out faster")

        if stats['total_theta_decay']:
            print(f"\n📉 THETA DECAY IMPACT:")
            print(f"   Total Lost to Time Decay: ${abs(stats['total_theta_decay']):,.2f}")
            print(f"   💡 This is money you lost just from holding over time")

        print(f"\n{'='*80}\n")

    def analyze_by_option_type(self) -> pd.DataFrame:
        """Analyze performance by option type (ITM/ATM/OTM)"""
        if not self.trades:
            return pd.DataFrame()

        df = pd.DataFrame(self.trades)

        # Classify options
        def classify_option(row):
            if row['entry_stock_price'] and row['strike']:
                if row['contract_type'] == 'CALL':
                    if row['strike'] < row['entry_stock_price'] * 0.98:
                        return 'ITM'
                    elif row['strike'] <= row['entry_stock_price'] * 1.02:
                        return 'ATM'
                    else:
                        return 'OTM'
            return 'Unknown'

        df['option_type'] = df.apply(classify_option, axis=1)

        # Group by option type
        analysis = df.groupby('option_type').agg({
            'net_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        analysis.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        analysis['Win Rate %'] = (analysis['Wins'] / analysis['Trades'] * 100).round(1)

        return analysis

    def analyze_by_days_to_expiration(self) -> pd.DataFrame:
        """Analyze performance by days to expiration"""
        if not self.trades:
            return pd.DataFrame()

        df = pd.DataFrame(self.trades)
        df = df[df['days_to_expiration'].notna()]

        if df.empty:
            return pd.DataFrame()

        # Classify by expiration
        def classify_expiration(days):
            if days <= 2:
                return '0-2 days'
            elif days <= 7:
                return '3-7 days'
            else:
                return '8+ days'

        df['exp_category'] = df['days_to_expiration'].apply(classify_expiration)

        # Group by expiration
        analysis = df.groupby('exp_category').agg({
            'net_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        analysis.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        analysis['Win Rate %'] = (analysis['Wins'] / analysis['Trades'] * 100).round(1)

        return analysis

    def export_to_csv(self, filename: str = "options_trades_export.csv"):
        """Export all trades to CSV"""
        if not self.trades:
            print("\n❌ No trades to export")
            return

        df = pd.DataFrame(self.trades)
        df.to_csv(filename, index=False)

        print(f"\n✅ Exported {len(df)} trades to {filename}")

    def interactive_add(self):
        """Interactive mode to add a trade"""
        print(f"\n{'='*80}")
        print(f"📝 ADD NEW OPTIONS TRADE")
        print(f"{'='*80}\n")

        # Basic info
        ticker = input("Ticker symbol: ").upper()
        contract_type = input("Contract type (CALL/PUT) [CALL]: ").upper() or "CALL"
        strike = float(input("Strike price: $"))
        expiration = input("Expiration date (YYYY-MM-DD): ")

        # Entry
        print(f"\n📊 ENTRY DETAILS:")
        entry_premium = float(input("Entry premium per contract: $"))
        contracts = int(input("Number of contracts: "))
        entry_stock_price = float(input("Stock price at entry: $"))
        entry_time = input("Entry time (HH:MM): ")

        # Exit
        print(f"\n📊 EXIT DETAILS:")
        exit_premium = float(input("Exit premium per contract: $"))
        exit_stock_price = float(input("Stock price at exit: $"))
        exit_time = input("Exit time (HH:MM): ")
        exit_reason = input("Exit reason (TARGET_HIT/STOP_LOSS/TIME_LIMIT/MACD_NEGATIVE): ").upper()

        # Greeks (optional)
        print(f"\n🔢 GREEKS (optional, press Enter to skip):")
        try:
            entry_delta = input("Entry Delta: ")
            entry_delta = float(entry_delta) if entry_delta else None

            entry_theta = input("Entry Theta: ")
            entry_theta = float(entry_theta) if entry_theta else None

            entry_iv = input("Entry IV: ")
            entry_iv = float(entry_iv) if entry_iv else None
        except:
            entry_delta = entry_theta = entry_iv = None

        # Strategy
        print(f"\n📈 STRATEGY DETAILS:")
        pattern = input("Pattern (Pullback/Breakout/etc.) [Pullback]: ") or "Pullback"
        macd_positive = input("MACD positive? (y/n) [y]: ").lower() != 'n'
        setup_quality = int(input("Setup quality (1-5 stars): "))

        # Days to expiration
        try:
            exp_date = datetime.strptime(expiration, '%Y-%m-%d')
            today = datetime.now()
            days_to_expiration = (exp_date - today).days
        except:
            days_to_expiration = None

        # Notes
        notes = input("Notes (optional): ")

        # Add trade
        self.add_trade(
            ticker=ticker,
            contract_type=contract_type,
            strike=strike,
            expiration=expiration,
            entry_premium=entry_premium,
            contracts=contracts,
            entry_stock_price=entry_stock_price,
            entry_time=entry_time,
            exit_premium=exit_premium,
            exit_stock_price=exit_stock_price,
            exit_time=exit_time,
            exit_reason=exit_reason,
            entry_delta=entry_delta,
            entry_theta=entry_theta,
            entry_iv=entry_iv,
            pattern=pattern,
            macd_positive=macd_positive,
            setup_quality=setup_quality,
            days_to_expiration=days_to_expiration,
            notes=notes
        )


def main():
    """Interactive menu"""
    journal = OptionsTradeJournal("my_options_trades.json")

    while True:
        print(f"\n{'='*80}")
        print(f"📒 OPTIONS TRADE JOURNAL")
        print(f"{'='*80}\n")

        print("1. Add a new trade")
        print("2. View all trades")
        print("3. View performance summary")
        print("4. Analyze by option type (ITM/ATM/OTM)")
        print("5. Analyze by expiration date")
        print("6. Export to CSV")
        print("7. Exit")

        choice = input("\nEnter your choice (1-7): ").strip()

        if choice == '1':
            journal.interactive_add()

        elif choice == '2':
            df = journal.view_trades()
            if not df.empty:
                print(f"\n{'='*80}")
                print(f"📊 ALL TRADES")
                print(f"{'='*80}\n")
                # Show key columns
                cols = ['date', 'ticker', 'strike', 'expiration', 'contracts',
                       'entry_premium', 'exit_premium', 'net_pnl', 'result']
                print(df[cols].to_string(index=False))

        elif choice == '3':
            journal.display_summary()

        elif choice == '4':
            analysis = journal.analyze_by_option_type()
            if not analysis.empty:
                print(f"\n{'='*80}")
                print(f"📊 PERFORMANCE BY OPTION TYPE")
                print(f"{'='*80}\n")
                print(analysis.to_string())
                print(f"\n💡 ITM = In-The-Money, ATM = At-The-Money, OTM = Out-of-The-Money")

        elif choice == '5':
            analysis = journal.analyze_by_days_to_expiration()
            if not analysis.empty:
                print(f"\n{'='*80}")
                print(f"📊 PERFORMANCE BY DAYS TO EXPIRATION")
                print(f"{'='*80}\n")
                print(analysis.to_string())

        elif choice == '6':
            journal.export_to_csv()

        elif choice == '7':
            print("\n👋 Happy trading!")
            break

        else:
            print("\n❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
