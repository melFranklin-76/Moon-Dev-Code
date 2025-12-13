#!/usr/bin/env python3
"""
Weekly Progress Tracker
Based on Ross Cameron's 25% Weekly Growth Goal

Tracks:
- Weekly account growth (target: 25%)
- Daily progress toward weekly goal
- Projected end-of-week balance
- "Survive till you thrive" status
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Optional


class WeeklyProgressTracker:
    def __init__(self, journal_file: str = "trade_journal.json", starting_balance: float = 2000):
        """
        Initialize weekly progress tracker

        Args:
            journal_file: Path to trade journal JSON file
            starting_balance: Starting account balance
        """
        self.journal_file = Path(journal_file)
        self.starting_balance = starting_balance
        self.weekly_target = 0.25  # 25% weekly growth
        self.trades_df = self._load_trades()

    def _load_trades(self) -> pd.DataFrame:
        """Load trades from journal file"""
        if not self.journal_file.exists():
            return pd.DataFrame()

        with open(self.journal_file, 'r') as f:
            trades = json.load(f)

        if not trades:
            return pd.DataFrame()

        df = pd.DataFrame(trades)
        df['date'] = pd.to_datetime(df['date'])

        return df

    def get_current_week_data(self) -> dict:
        """Get data for current trading week (Monday-Friday)"""
        if self.trades_df.empty:
            return None

        # Get current week's Monday
        today = datetime.now()
        days_since_monday = today.weekday()  # 0 = Monday, 6 = Sunday
        week_start = today - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Filter trades for current week
        current_week = self.trades_df[self.trades_df['date'] >= week_start]

        if current_week.empty:
            return {
                'week_start': week_start,
                'trades_count': 0,
                'total_pnl': 0,
                'current_balance': self.starting_balance,
                'week_growth_pct': 0,
                'target_growth_pct': self.weekly_target * 100,
                'on_track': False
            }

        # Calculate weekly stats
        total_pnl = current_week['gross_pnl'].sum()
        current_balance = self.starting_balance + total_pnl
        week_growth_pct = (total_pnl / self.starting_balance) * 100

        # Calculate days into week
        trading_days_elapsed = len(current_week['date'].dt.date.unique())
        trading_days_total = 5  # Monday-Friday

        # Projected growth
        if trading_days_elapsed > 0:
            daily_avg_growth = week_growth_pct / trading_days_elapsed
            projected_weekly_growth = daily_avg_growth * trading_days_total
        else:
            projected_weekly_growth = 0

        # Check if on track
        on_track = projected_weekly_growth >= (self.weekly_target * 100)

        return {
            'week_start': week_start,
            'trades_count': len(current_week),
            'total_pnl': total_pnl,
            'current_balance': current_balance,
            'week_growth_pct': week_growth_pct,
            'target_growth_pct': self.weekly_target * 100,
            'trading_days_elapsed': trading_days_elapsed,
            'daily_avg_growth': daily_avg_growth if trading_days_elapsed > 0 else 0,
            'projected_weekly_growth': projected_weekly_growth,
            'on_track': on_track
        }

    def get_weekly_summary(self) -> pd.DataFrame:
        """Get summary of all weeks"""
        if self.trades_df.empty:
            return pd.DataFrame()

        df = self.trades_df.copy()
        df['week'] = df['date'].dt.to_period('W-FRI')  # Week ending Friday

        weekly = df.groupby('week').agg({
            'gross_pnl': 'sum',
            'trade_number': 'count'
        }).reset_index()

        weekly.columns = ['Week', 'P&L', 'Trades']
        weekly['Week'] = weekly['Week'].astype(str)

        # Calculate cumulative balance and growth
        weekly['Balance'] = self.starting_balance + weekly['P&L'].cumsum()
        weekly['Growth %'] = (weekly['Balance'] - self.starting_balance) / self.starting_balance * 100
        weekly['Weekly Growth %'] = (weekly['P&L'] / self.starting_balance) * 100
        weekly['Met Target'] = weekly['Weekly Growth %'] >= (self.weekly_target * 100)

        return weekly

    def display_current_week(self):
        """Display current week progress"""
        data = self.get_current_week_data()

        if not data:
            print("\n❌ No trading data available")
            return

        print(f"\n{'='*80}")
        print(f"📅 WEEKLY PROGRESS TRACKER")
        print(f"Week of {data['week_start'].strftime('%B %d, %Y')}")
        print(f"{'='*80}")

        print(f"\n🎯 WEEKLY TARGET:")
        print(f"   Growth Goal: {data['target_growth_pct']:.0f}% ({self.weekly_target * 100:.0f}% per week)")
        print(f"   Target P&L: ${self.starting_balance * self.weekly_target:,.2f}")
        print(f"   Target Balance: ${self.starting_balance * (1 + self.weekly_target):,.2f}")

        print(f"\n📊 CURRENT PROGRESS:")
        print(f"   Trading Days: {data['trading_days_elapsed']}/5")
        print(f"   Trades Taken: {data['trades_count']}")
        print(f"   Weekly P&L: ${data['total_pnl']:+,.2f}")
        print(f"   Current Balance: ${data['current_balance']:,.2f}")
        print(f"   Weekly Growth: {data['week_growth_pct']:+.2f}%")

        print(f"\n📈 PROJECTION:")
        print(f"   Daily Avg Growth: {data['daily_avg_growth']:+.2f}%")
        print(f"   Projected Weekly: {data['projected_weekly_growth']:+.2f}%")

        status_emoji = "✅" if data['on_track'] else "❌"
        status_text = "ON TRACK" if data['on_track'] else "BELOW TARGET"

        print(f"\n{status_emoji} STATUS: {status_text}")

        if not data['on_track']:
            shortfall = (self.weekly_target * 100) - data['projected_weekly_growth']
            print(f"   ⚠️  Need to improve by {shortfall:.2f}% to hit target")
            print(f"   💡 Focus on A+ setups only!")
        else:
            print(f"   🎉 Keep up the great work!")

        print(f"\n{'='*80}\n")

    def display_weekly_summary(self):
        """Display summary of all weeks"""
        weekly = self.get_weekly_summary()

        if weekly.empty:
            print("\n❌ No weekly data available")
            return

        print(f"\n{'='*80}")
        print(f"📊 ALL WEEKS SUMMARY")
        print(f"{'='*80}\n")

        for idx, row in weekly.iterrows():
            status = "✅" if row['Met Target'] else "❌"
            print(f"{status} Week of {row['Week']}")
            print(f"   Trades: {row['Trades']} | P&L: ${row['P&L']:+,.2f}")
            print(f"   Balance: ${row['Balance']:,.2f} | Growth: {row['Weekly Growth %']:+.2f}%")
            print()

        print(f"{'='*80}")
        print(f"📈 OVERALL STATS:")
        print(f"   Total Weeks: {len(weekly)}")
        print(f"   Weeks Hit Target: {weekly['Met Target'].sum()}/{len(weekly)}")
        print(f"   Success Rate: {(weekly['Met Target'].sum() / len(weekly) * 100):.1f}%")
        print(f"   Final Balance: ${weekly['Balance'].iloc[-1]:,.2f}")
        print(f"   Total Growth: {weekly['Growth %'].iloc[-1]:+.2f}%")
        print(f"{'='*80}\n")

    def what_if_scenarios(self, current_balance: float):
        """Show what-if scenarios for rest of week"""
        data = self.get_current_week_data()

        if not data:
            print("\n❌ No trading data available")
            return

        days_remaining = 5 - data['trading_days_elapsed']

        if days_remaining <= 0:
            print("\n✅ Week complete!")
            return

        print(f"\n{'='*80}")
        print(f"🔮 WHAT-IF SCENARIOS")
        print(f"{days_remaining} Trading Day(s) Remaining")
        print(f"{'='*80}")

        # Current trajectory
        target_balance = self.starting_balance * (1 + self.weekly_target)
        needed_pnl = target_balance - current_balance

        print(f"\n📊 TO HIT 25% WEEKLY TARGET:")
        print(f"   Current Balance: ${current_balance:,.2f}")
        print(f"   Target Balance: ${target_balance:,.2f}")
        print(f"   Total Needed: ${needed_pnl:,.2f}")

        if days_remaining > 0:
            daily_pnl_needed = needed_pnl / days_remaining
            daily_pct_needed = (daily_pnl_needed / current_balance) * 100

            print(f"\n   Per Day Needed: ${daily_pnl_needed:,.2f} ({daily_pct_needed:.2f}%)")

        # Scenarios
        scenarios = [
            ("Conservative", 0.05),
            ("Base Hit", 0.10),
            ("Good Day", 0.15),
            ("Great Day", 0.20)
        ]

        print(f"\n📈 DAILY GROWTH SCENARIOS:")
        for scenario_name, daily_growth in scenarios:
            projected_pnl = current_balance * daily_growth * days_remaining
            projected_balance = current_balance + projected_pnl
            projected_weekly_growth = ((projected_balance - self.starting_balance) / self.starting_balance) * 100

            status = "✅" if projected_weekly_growth >= 25 else "❌"

            print(f"\n   {status} {scenario_name} ({daily_growth * 100:.0f}% daily):")
            print(f"      End of Week Balance: ${projected_balance:,.2f}")
            print(f"      Weekly Growth: {projected_weekly_growth:+.2f}%")

        print(f"\n{'='*80}\n")

    def plot_weekly_progress(self, save_path: str = "weekly_progress.png"):
        """Plot weekly progress chart"""
        weekly = self.get_weekly_summary()

        if weekly.empty:
            print("\n❌ No data to plot")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Plot 1: Account Balance
        ax1.plot(weekly['Week'], weekly['Balance'], marker='o', linewidth=2, markersize=8)
        ax1.axhline(y=self.starting_balance, color='gray', linestyle='--', alpha=0.5, label='Starting Balance')
        ax1.set_title('Account Balance Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Week')
        ax1.set_ylabel('Balance ($)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot 2: Weekly Growth %
        colors = ['green' if x else 'red' for x in weekly['Met Target']]
        ax2.bar(weekly['Week'], weekly['Weekly Growth %'], color=colors, alpha=0.7)
        ax2.axhline(y=25, color='blue', linestyle='--', linewidth=2, label='25% Target')
        ax2.set_title('Weekly Growth %', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Week')
        ax2.set_ylabel('Growth %')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 Chart saved to {save_path}")
        plt.close()


def main():
    """Example usage"""
    # Initialize tracker
    tracker = WeeklyProgressTracker("my_trades.json", starting_balance=2000)

    # Display current week progress
    tracker.display_current_week()

    # Display all weeks summary
    tracker.display_weekly_summary()

    # What-if scenarios
    current_balance = 2800  # Example current balance
    tracker.what_if_scenarios(current_balance)


if __name__ == "__main__":
    main()
