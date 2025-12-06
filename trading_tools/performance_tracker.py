#!/usr/bin/env python3
"""
Performance Metrics Tracker
Based on Ross Cameron's Critical Metrics Dashboard

Analyzes:
- Accuracy (target 75%)
- Profit/Loss ratio (target 2:1)
- Performance by price range
- Performance by hold time
- Performance by float
- Performance by percentage gain
- Performance by relative volume
- Performance by share size
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt


class PerformanceTracker:
    def __init__(self, journal_file: str = "trade_journal.json"):
        """
        Initialize performance tracker

        Args:
            journal_file: Path to trade journal JSON file
        """
        self.journal_file = Path(journal_file)
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

        # Add calculated fields
        if not df.empty:
            # Parse times to calculate hold time
            if 'entry_time' in df.columns and 'exit_time' in df.columns:
                df['hold_minutes'] = df.apply(self._calculate_hold_time, axis=1)

            # Price ranges
            df['price_range'] = pd.cut(
                df['entry_price'],
                bins=[0, 2, 4, 10, 20, float('inf')],
                labels=['<$2', '$2-$4', '$4-$10', '$10-$20', '>$20']
            )

        return df

    def _calculate_hold_time(self, row) -> int:
        """Calculate hold time in minutes"""
        try:
            entry = datetime.strptime(row['entry_time'], "%H:%M")
            exit = datetime.strptime(row['exit_time'], "%H:%M")
            delta = exit - entry
            return int(delta.total_seconds() / 60)
        except:
            return 0

    def get_core_metrics(self) -> dict:
        """Get core performance metrics"""
        if self.trades_df.empty:
            return None

        df = self.trades_df

        wins = df[df['result'] == 'WIN']
        losses = df[df['result'] == 'LOSS']

        total_trades = len(df)
        total_wins = len(wins)
        total_losses = len(losses)

        accuracy = (total_wins / total_trades * 100) if total_trades > 0 else 0

        avg_winner = wins['gross_pnl'].mean() if not wins.empty else 0
        avg_loser = abs(losses['gross_pnl'].mean()) if not losses.empty else 0

        profit_loss_ratio = (avg_winner / avg_loser) if avg_loser > 0 else 0

        total_pnl = df['gross_pnl'].sum()

        return {
            'total_trades': total_trades,
            'wins': total_wins,
            'losses': total_losses,
            'accuracy': round(accuracy, 1),
            'accuracy_target': 75.0,
            'avg_winner': round(avg_winner, 2),
            'avg_loser': round(avg_loser, 2),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'ratio_target': 2.0,
            'total_pnl': round(total_pnl, 2)
        }

    def performance_by_price_range(self) -> pd.DataFrame:
        """Analyze performance by stock price range"""
        if self.trades_df.empty or 'price_range' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        grouped = df.groupby('price_range').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        grouped.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        grouped['Accuracy %'] = ((grouped['Wins'] / grouped['Trades']) * 100).round(1)

        return grouped.sort_values('Total P&L', ascending=False)

    def performance_by_hold_time(self) -> pd.DataFrame:
        """Analyze performance by hold time"""
        if self.trades_df.empty or 'hold_minutes' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df.copy()

        # Create hold time ranges
        df['hold_range'] = pd.cut(
            df['hold_minutes'],
            bins=[0, 5, 10, 30, 60, float('inf')],
            labels=['<5 min', '5-10 min', '10-30 min', '30-60 min', '>60 min']
        )

        grouped = df.groupby('hold_range').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        grouped.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        grouped['Accuracy %'] = ((grouped['Wins'] / grouped['Trades']) * 100).round(1)

        return grouped.sort_values('Total P&L', ascending=False)

    def performance_by_setup_quality(self) -> pd.DataFrame:
        """Analyze performance by setup quality rating"""
        if self.trades_df.empty or 'setup_quality' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        grouped = df.groupby('setup_quality').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        grouped.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        grouped['Accuracy %'] = ((grouped['Wins'] / grouped['Trades']) * 100).round(1)

        return grouped.sort_index(ascending=False)

    def performance_by_macd(self) -> pd.DataFrame:
        """Analyze performance when MACD was positive vs negative"""
        if self.trades_df.empty or 'macd_positive' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        grouped = df.groupby('macd_positive').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        grouped.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        grouped['Accuracy %'] = ((grouped['Wins'] / grouped['Trades']) * 100).round(1)
        grouped.index = ['MACD Negative', 'MACD Positive']

        return grouped.sort_values('Total P&L', ascending=False)

    def display_dashboard(self):
        """Display complete performance dashboard"""
        if self.trades_df.empty:
            print("\n❌ No trades data available. Start logging trades first!")
            return

        print(f"\n{'='*80}")
        print(f"CRITICAL METRICS DASHBOARD")
        print(f"Based on Ross Cameron's Performance Analysis")
        print(f"{'='*80}")

        # Core metrics
        core = self.get_core_metrics()

        print(f"\n📊 CORE METRICS:")
        print(f"   Total Trades: {core['total_trades']}")
        print(f"   Wins: {core['wins']} | Losses: {core['losses']}")

        # Accuracy with target comparison
        accuracy_status = "✅" if core['accuracy'] >= core['accuracy_target'] else "❌"
        print(f"   {accuracy_status} Accuracy: {core['accuracy']}% (Target: {core['accuracy_target']}%)")

        # Profit/Loss ratio with target comparison
        ratio_status = "✅" if core['profit_loss_ratio'] >= core['ratio_target'] else "❌"
        print(f"   {ratio_status} P/L Ratio: {core['profit_loss_ratio']}:1 (Target: {core['ratio_target']}:1)")

        print(f"\n💰 P&L SUMMARY:")
        print(f"   Total P&L: ${core['total_pnl']:,.2f}")
        print(f"   Avg Winner: ${core['avg_winner']:.2f}")
        print(f"   Avg Loser: ${core['avg_loser']:.2f}")

        # Performance by price range
        print(f"\n{'='*80}")
        print(f"📈 PERFORMANCE BY PRICE RANGE")
        print(f"{'='*80}")
        price_perf = self.performance_by_price_range()
        if not price_perf.empty:
            print(price_perf.to_string())
        else:
            print("   No data available")

        # Performance by hold time
        print(f"\n{'='*80}")
        print(f"⏱️  PERFORMANCE BY HOLD TIME")
        print(f"{'='*80}")
        hold_perf = self.performance_by_hold_time()
        if not hold_perf.empty:
            print(hold_perf.to_string())
        else:
            print("   No data available")

        # Performance by MACD
        print(f"\n{'='*80}")
        print(f"📉 PERFORMANCE BY MACD STATUS")
        print(f"{'='*80}")
        macd_perf = self.performance_by_macd()
        if not macd_perf.empty:
            print(macd_perf.to_string())
        else:
            print("   No data available")

        # Performance by setup quality
        print(f"\n{'='*80}")
        print(f"⭐ PERFORMANCE BY SETUP QUALITY (1-5)")
        print(f"{'='*80}")
        quality_perf = self.performance_by_setup_quality()
        if not quality_perf.empty:
            print(quality_perf.to_string())
        else:
            print("   No data available")

        # Actionable insights
        self.display_insights()

        print(f"\n{'='*80}\n")

    def display_insights(self):
        """Display actionable insights from the data"""
        if self.trades_df.empty:
            return

        print(f"\n{'='*80}")
        print(f"💡 ACTIONABLE INSIGHTS")
        print(f"{'='*80}")

        insights = []

        # Check accuracy
        core = self.get_core_metrics()
        if core['accuracy'] < 75:
            insights.append(f"⚠️  Accuracy is {core['accuracy']}%, below the 75% target. Focus on A+ setups only.")

        if core['profit_loss_ratio'] < 2.0:
            insights.append(f"⚠️  P/L ratio is {core['profit_loss_ratio']}:1, below 2:1 target. Let winners run more or cut losses faster.")

        # Check MACD performance
        macd_perf = self.performance_by_macd()
        if not macd_perf.empty:
            if 'MACD Negative' in macd_perf.index:
                neg_pnl = macd_perf.loc['MACD Negative', 'Total P&L']
                if neg_pnl < 0:
                    insights.append(f"⚠️  You lose money when MACD is negative. ONLY trade when MACD is positive!")

        # Check price range performance
        price_perf = self.performance_by_price_range()
        if not price_perf.empty:
            losing_ranges = price_perf[price_perf['Total P&L'] < 0]
            if not losing_ranges.empty:
                for range_name in losing_ranges.index:
                    insights.append(f"⚠️  You lose money in {range_name} range. Consider avoiding this price range.")

        # Check setup quality
        quality_perf = self.performance_by_setup_quality()
        if not quality_perf.empty:
            if 5 in quality_perf.index:
                best_pnl = quality_perf.loc[5, 'Total P&L']
                insights.append(f"✅ 5-star setups are performing well (${best_pnl:.2f}). Focus on quality over quantity!")

        if not insights:
            insights.append("✅ No major issues detected. Keep following your trading plan!")

        for insight in insights:
            print(f"   {insight}")


def main():
    """Example usage"""
    # Initialize tracker
    tracker = PerformanceTracker("my_trades.json")

    # Display dashboard
    tracker.display_dashboard()

    print("\n💡 TIP: Update this dashboard after each trade to track your progress!")
    print("Run this script regularly to identify areas for improvement.\n")


if __name__ == "__main__":
    main()
