#!/usr/bin/env python3
"""
Trade Journal - One Trade Per Day Strategy
Based on Ross Cameron's Small Account Challenge

Tracks:
- Entry/exit details
- MACD status at entry
- Volume profile
- Win/loss tracking
- Performance metrics
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional


class TradeJournal:
    def __init__(self, journal_file: str = "trade_journal.json"):
        """
        Initialize trade journal

        Args:
            journal_file: Path to journal file (default: trade_journal.json)
        """
        self.journal_file = Path(journal_file)
        self.trades = self._load_journal()

    def _load_journal(self) -> list:
        """Load existing journal or create new one"""
        if self.journal_file.exists():
            with open(self.journal_file, 'r') as f:
                return json.load(f)
        return []

    def _save_journal(self):
        """Save journal to file"""
        with open(self.journal_file, 'w') as f:
            json.dump(self.trades, f, indent=2)

    def add_trade(self,
                  ticker: str,
                  entry_price: float,
                  exit_price: float,
                  shares: int,
                  entry_time: str = None,
                  exit_time: str = None,
                  macd_positive: bool = True,
                  volume_profile: str = "Good",
                  pattern: str = "Pullback",
                  notes: str = "",
                  setup_quality: int = 5) -> dict:
        """
        Add a trade to the journal

        Args:
            ticker: Stock symbol
            entry_price: Entry price per share
            exit_price: Exit price per share
            shares: Number of shares
            entry_time: Time of entry (HH:MM format)
            exit_time: Time of exit (HH:MM format)
            macd_positive: Was MACD positive at entry?
            volume_profile: Volume profile description
            pattern: Candlestick pattern used
            notes: Additional notes
            setup_quality: Quality rating 1-5 (5 = best)

        Returns:
            dict: The trade record
        """
        if entry_time is None:
            entry_time = datetime.now().strftime("%H:%M")
        if exit_time is None:
            exit_time = datetime.now().strftime("%H:%M")

        # Calculate profit/loss
        gross_pnl = (exit_price - entry_price) * shares
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        position_value = entry_price * shares

        # Determine win/loss
        result = "WIN" if gross_pnl > 0 else "LOSS" if gross_pnl < 0 else "BREAKEVEN"

        trade = {
            'trade_number': len(self.trades) + 1,
            'date': datetime.now().strftime("%Y-%m-%d"),
            'ticker': ticker.upper(),
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'shares': shares,
            'position_value': round(position_value, 2),
            'gross_pnl': round(gross_pnl, 2),
            'pnl_percent': round(pnl_percent, 2),
            'result': result,
            'macd_positive': macd_positive,
            'volume_profile': volume_profile,
            'pattern': pattern,
            'setup_quality': setup_quality,
            'notes': notes
        }

        self.trades.append(trade)
        self._save_journal()

        print(f"\n✅ Trade #{trade['trade_number']} logged: {ticker} - {result}")
        print(f"   P&L: ${gross_pnl:.2f} ({pnl_percent:+.2f}%)")

        return trade

    def get_stats(self) -> dict:
        """Calculate performance statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'accuracy': 0,
                'total_pnl': 0,
                'avg_winner': 0,
                'avg_loser': 0,
                'profit_factor': 0,
                'largest_win': 0,
                'largest_loss': 0
            }

        df = pd.DataFrame(self.trades)

        wins = df[df['result'] == 'WIN']
        losses = df[df['result'] == 'LOSS']

        total_wins = len(wins)
        total_losses = len(losses)
        total_trades = len(df)

        accuracy = (total_wins / total_trades * 100) if total_trades > 0 else 0

        total_pnl = df['gross_pnl'].sum()
        avg_winner = wins['gross_pnl'].mean() if not wins.empty else 0
        avg_loser = losses['gross_pnl'].mean() if not losses.empty else 0

        gross_profits = wins['gross_pnl'].sum() if not wins.empty else 0
        gross_losses = abs(losses['gross_pnl'].sum()) if not losses.empty else 0

        profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else float('inf')

        largest_win = df['gross_pnl'].max() if not df.empty else 0
        largest_loss = df['gross_pnl'].min() if not df.empty else 0

        return {
            'total_trades': total_trades,
            'wins': total_wins,
            'losses': total_losses,
            'accuracy': round(accuracy, 1),
            'total_pnl': round(total_pnl, 2),
            'avg_winner': round(avg_winner, 2),
            'avg_loser': round(avg_loser, 2),
            'profit_factor': round(profit_factor, 2),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2),
            'gross_profits': round(gross_profits, 2),
            'gross_losses': round(gross_losses, 2)
        }

    def display_stats(self):
        """Display performance statistics"""
        stats = self.get_stats()

        print(f"\n{'='*60}")
        print(f"PERFORMANCE STATISTICS")
        print(f"{'='*60}")

        if stats['total_trades'] == 0:
            print("\n❌ No trades recorded yet")
            return

        print(f"\n📊 OVERVIEW:")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Wins: {stats['wins']} | Losses: {stats['losses']}")
        print(f"   Accuracy: {stats['accuracy']}% (Target: 75%)")

        print(f"\n💰 P&L:")
        print(f"   Total P&L: ${stats['total_pnl']:,.2f}")
        print(f"   Gross Profits: ${stats['gross_profits']:,.2f}")
        print(f"   Gross Losses: ${stats['gross_losses']:,.2f}")
        print(f"   Profit Factor: {stats['profit_factor']:.2f}x (Target: 2.0x)")

        print(f"\n📈 AVERAGES:")
        print(f"   Avg Winner: ${stats['avg_winner']:.2f}")
        print(f"   Avg Loser: ${stats['avg_loser']:.2f}")
        ratio = abs(stats['avg_winner'] / stats['avg_loser']) if stats['avg_loser'] != 0 else 0
        print(f"   Win/Loss Ratio: {ratio:.2f}:1 (Target: 2:1)")

        print(f"\n🎯 EXTREMES:")
        print(f"   Largest Win: ${stats['largest_win']:.2f}")
        print(f"   Largest Loss: ${stats['largest_loss']:.2f}")

        print(f"\n{'='*60}\n")

    def display_recent_trades(self, n: int = 10):
        """Display recent trades"""
        if not self.trades:
            print("\n❌ No trades recorded yet")
            return

        recent = self.trades[-n:]

        print(f"\n{'='*80}")
        print(f"RECENT TRADES (Last {min(n, len(self.trades))})")
        print(f"{'='*80}\n")

        for trade in reversed(recent):
            result_emoji = "✅" if trade['result'] == "WIN" else "❌" if trade['result'] == "LOSS" else "➖"
            macd_emoji = "✓" if trade['macd_positive'] else "✗"

            print(f"{result_emoji} Trade #{trade['trade_number']} - {trade['date']} - {trade['ticker']}")
            print(f"   Entry: ${trade['entry_price']:.2f} @ {trade['entry_time']} | Exit: ${trade['exit_price']:.2f} @ {trade['exit_time']}")
            print(f"   Shares: {trade['shares']:,} | P&L: ${trade['gross_pnl']:+.2f} ({trade['pnl_percent']:+.2f}%)")
            print(f"   MACD: {macd_emoji} | Volume: {trade['volume_profile']} | Pattern: {trade['pattern']}")
            if trade['notes']:
                print(f"   Notes: {trade['notes']}")
            print()

    def export_to_csv(self, filename: str = None):
        """Export journal to CSV"""
        if not self.trades:
            print("No trades to export")
            return

        if filename is None:
            filename = f"trades_{datetime.now().strftime('%Y%m%d')}.csv"

        df = pd.DataFrame(self.trades)
        df.to_csv(filename, index=False)
        print(f"\n💾 Journal exported to {filename}")


def main():
    """Example usage"""
    # Initialize journal
    journal = TradeJournal("my_trades.json")

    # Example: Log Ross's Day 3 trade (ATON)
    print("\n📝 Logging Example Trade...")

    journal.add_trade(
        ticker="ATON",
        entry_price=3.64,
        exit_price=4.03,
        shares=769,
        entry_time="07:05",
        exit_time="07:08",
        macd_positive=True,
        volume_profile="Strong buying, light selling",
        pattern="Pullback - Cup and Handle",
        notes="Perfect 5-pillar setup. Breaking news catalyst. Low float stock.",
        setup_quality=5
    )

    # Display recent trades
    journal.display_recent_trades(10)

    # Display statistics
    journal.display_stats()

    # Interactive mode example
    print("\n" + "="*60)
    print("To log your own trades, you can:")
    print("1. Use this script interactively")
    print("2. Import TradeJournal in your own script")
    print("3. Manually edit the JSON file")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
