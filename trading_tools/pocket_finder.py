#!/usr/bin/env python3
"""
Pocket Finder - Find Your Profitable Trading Niche
Based on Ross Cameron's "Find Your Pocket" Strategy

Analyzes your trades to identify:
- Most profitable price ranges (e.g., $5-$10 stocks)
- Best performing float ranges
- Optimal hold times
- Best patterns and setups

"Even just this little pocket... that's something you want to pay
attention to because we can build that into something bigger."
- Ross Cameron
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt


class PocketFinder:
    def __init__(self, journal_file: str = "trade_journal.json"):
        """
        Initialize pocket finder

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
            # Price ranges
            df['price_range'] = pd.cut(
                df['entry_price'],
                bins=[0, 2, 4, 5, 10, 20, float('inf')],
                labels=['<$2', '$2-$4', '$4-$5', '$5-$10', '$10-$20', '>$20']
            )

            # Hold time in minutes
            if 'entry_time' in df.columns and 'exit_time' in df.columns:
                df['hold_minutes'] = df.apply(self._calculate_hold_time, axis=1)
                df['hold_range'] = pd.cut(
                    df['hold_minutes'],
                    bins=[0, 3, 5, 10, 30, float('inf')],
                    labels=['<3 min', '3-5 min', '5-10 min', '10-30 min', '>30 min']
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

    def find_price_pocket(self) -> pd.DataFrame:
        """Find your most profitable price ranges"""
        if self.trades_df.empty or 'price_range' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        # Group by price range
        pocket = df.groupby('price_range').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        pocket.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        pocket['Win Rate %'] = ((pocket['Wins'] / pocket['Trades']) * 100).round(1)
        pocket['Consistency Score'] = (pocket['Win Rate %'] * pocket['Total P&L'] / 100).round(2)

        # Sort by consistency score (best pocket = high win rate + good P&L)
        pocket = pocket.sort_values('Consistency Score', ascending=False)

        return pocket

    def find_hold_time_pocket(self) -> pd.DataFrame:
        """Find your most profitable hold times"""
        if self.trades_df.empty or 'hold_range' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        pocket = df.groupby('hold_range').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        pocket.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        pocket['Win Rate %'] = ((pocket['Wins'] / pocket['Trades']) * 100).round(1)
        pocket['Consistency Score'] = (pocket['Win Rate %'] * pocket['Total P&L'] / 100).round(2)

        pocket = pocket.sort_values('Consistency Score', ascending=False)

        return pocket

    def find_pattern_pocket(self) -> pd.DataFrame:
        """Find your most profitable patterns"""
        if self.trades_df.empty or 'pattern' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        pocket = df.groupby('pattern').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        pocket.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        pocket['Win Rate %'] = ((pocket['Wins'] / pocket['Trades']) * 100).round(1)
        pocket['Consistency Score'] = (pocket['Win Rate %'] * pocket['Total P&L'] / 100).round(2)

        pocket = pocket.sort_values('Consistency Score', ascending=False)

        return pocket

    def find_setup_quality_pocket(self) -> pd.DataFrame:
        """Find correlation between setup quality and performance"""
        if self.trades_df.empty or 'setup_quality' not in self.trades_df.columns:
            return pd.DataFrame()

        df = self.trades_df

        pocket = df.groupby('setup_quality').agg({
            'gross_pnl': ['sum', 'mean', 'count'],
            'result': lambda x: (x == 'WIN').sum()
        }).round(2)

        pocket.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
        pocket['Win Rate %'] = ((pocket['Wins'] / pocket['Trades']) * 100).round(1)

        pocket = pocket.sort_index(ascending=False)

        return pocket

    def display_all_pockets(self):
        """Display all profitable pockets"""
        if self.trades_df.empty:
            print("\n❌ No trading data available. Start logging trades!")
            return

        print(f"\n{'='*80}")
        print(f"🎯 POCKET FINDER - FIND YOUR PROFITABLE NICHE")
        print(f"{'='*80}")
        print(f'"Even just this little pocket... that\'s something you want to pay')
        print(f'attention to because we can build that into something bigger."')
        print(f"- Ross Cameron")
        print(f"{'='*80}\n")

        # Price Pocket
        print(f"💰 PRICE RANGE POCKET")
        print(f"{'='*80}")
        price_pocket = self.find_price_pocket()
        if not price_pocket.empty:
            print(price_pocket.to_string())
            best_price = price_pocket.index[0]
            print(f"\n🎯 YOUR BEST POCKET: {best_price}")
            print(f"   Win Rate: {price_pocket.loc[best_price, 'Win Rate %']:.1f}%")
            print(f"   Total P&L: ${price_pocket.loc[best_price, 'Total P&L']:.2f}")
            print(f"   💡 FOCUS HERE! This is where you're making money.")
        else:
            print("   No data available")

        # Hold Time Pocket
        print(f"\n⏱️  HOLD TIME POCKET")
        print(f"{'='*80}")
        hold_pocket = self.find_hold_time_pocket()
        if not hold_pocket.empty:
            print(hold_pocket.to_string())
            best_hold = hold_pocket.index[0]
            print(f"\n🎯 YOUR BEST POCKET: {best_hold}")
            print(f"   Win Rate: {hold_pocket.loc[best_hold, 'Win Rate %']:.1f}%")
            print(f"   Total P&L: ${hold_pocket.loc[best_hold, 'Total P&L']:.2f}")
        else:
            print("   No data available")

        # Pattern Pocket
        print(f"\n📈 PATTERN POCKET")
        print(f"{'='*80}")
        pattern_pocket = self.find_pattern_pocket()
        if not pattern_pocket.empty:
            print(pattern_pocket.to_string())
            best_pattern = pattern_pocket.index[0]
            print(f"\n🎯 YOUR BEST POCKET: {best_pattern}")
            print(f"   Win Rate: {pattern_pocket.loc[best_pattern, 'Win Rate %']:.1f}%")
            print(f"   Total P&L: ${pattern_pocket.loc[best_pattern, 'Total P&L']:.2f}")
        else:
            print("   No data available")

        # Setup Quality Pocket
        print(f"\n⭐ SETUP QUALITY ANALYSIS")
        print(f"{'='*80}")
        quality_pocket = self.find_setup_quality_pocket()
        if not quality_pocket.empty:
            print(quality_pocket.to_string())
            print(f"\n💡 INSIGHT: Higher quality setups should have better results.")
            print(f"   If not, you may need to re-evaluate your setup criteria.")
        else:
            print("   No data available")

        # Actionable recommendations
        self._display_recommendations(price_pocket, hold_pocket, pattern_pocket, quality_pocket)

        print(f"\n{'='*80}\n")

    def _display_recommendations(self, price_pocket, hold_pocket, pattern_pocket, quality_pocket):
        """Display actionable recommendations based on pockets"""
        print(f"\n{'='*80}")
        print(f"💡 ACTIONABLE RECOMMENDATIONS")
        print(f"{'='*80}")

        recommendations = []

        # Price recommendations
        if not price_pocket.empty:
            best_price = price_pocket.index[0]
            losing_prices = price_pocket[price_pocket['Total P&L'] < 0]

            recommendations.append(
                f"✅ LEAN INTO {best_price} stocks - this is your profitable pocket!"
            )

            if not losing_prices.empty:
                for price_range in losing_prices.index:
                    recommendations.append(
                        f"❌ AVOID {price_range} stocks - you're losing money here"
                    )

        # Hold time recommendations
        if not hold_pocket.empty:
            best_hold = hold_pocket.index[0]
            recommendations.append(
                f"⏱️  OPTIMAL HOLD TIME: {best_hold} - stick to this window"
            )

        # Pattern recommendations
        if not pattern_pocket.empty:
            best_pattern = pattern_pocket.index[0]
            worst_pattern = pattern_pocket.iloc[-1]

            recommendations.append(
                f"📈 FOCUS ON: {best_pattern} pattern - your most consistent"
            )

        # Setup quality recommendations
        if not quality_pocket.empty:
            if 5 in quality_pocket.index and 3 in quality_pocket.index:
                five_star_pnl = quality_pocket.loc[5, 'Total P&L']
                three_star_pnl = quality_pocket.loc[3, 'Total P&L']

                if five_star_pnl > three_star_pnl:
                    recommendations.append(
                        "⭐ QUALITY MATTERS: 5-star setups outperform - be more selective!"
                    )

        # Display recommendations
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   📊 Log more trades to get personalized recommendations")

        print(f"\n💪 STRATEGY: Focus on your pockets, avoid your weaknesses.")
        print(f"   'Survive till you thrive' - lean into what works!")

    def plot_pockets(self, save_path: str = "pockets_analysis.png"):
        """Create visual analysis of pockets"""
        if self.trades_df.empty:
            print("\n❌ No data to plot")
            return

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

        # Price pocket
        price_pocket = self.find_price_pocket()
        if not price_pocket.empty:
            colors = ['green' if x > 0 else 'red' for x in price_pocket['Total P&L']]
            ax1.bar(price_pocket.index.astype(str), price_pocket['Total P&L'], color=colors, alpha=0.7)
            ax1.set_title('Price Range Performance', fontweight='bold')
            ax1.set_xlabel('Price Range')
            ax1.set_ylabel('Total P&L ($)')
            ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax1.grid(True, alpha=0.3)

        # Hold time pocket
        hold_pocket = self.find_hold_time_pocket()
        if not hold_pocket.empty:
            colors = ['green' if x > 0 else 'red' for x in hold_pocket['Total P&L']]
            ax2.bar(hold_pocket.index.astype(str), hold_pocket['Total P&L'], color=colors, alpha=0.7)
            ax2.set_title('Hold Time Performance', fontweight='bold')
            ax2.set_xlabel('Hold Time')
            ax2.set_ylabel('Total P&L ($)')
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax2.grid(True, alpha=0.3)

        # Win rate by price
        if not price_pocket.empty:
            ax3.bar(price_pocket.index.astype(str), price_pocket['Win Rate %'], color='blue', alpha=0.7)
            ax3.axhline(y=75, color='red', linestyle='--', label='75% Target')
            ax3.set_title('Win Rate by Price Range', fontweight='bold')
            ax3.set_xlabel('Price Range')
            ax3.set_ylabel('Win Rate %')
            ax3.legend()
            ax3.grid(True, alpha=0.3)

        # Setup quality
        quality_pocket = self.find_setup_quality_pocket()
        if not quality_pocket.empty:
            ax4.plot(quality_pocket.index, quality_pocket['Win Rate %'], marker='o', linewidth=2, markersize=8)
            ax4.set_title('Win Rate by Setup Quality', fontweight='bold')
            ax4.set_xlabel('Setup Quality (Stars)')
            ax4.set_ylabel('Win Rate %')
            ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 Pockets analysis chart saved to {save_path}")
        plt.close()


def main():
    """Example usage"""
    # Initialize pocket finder
    finder = PocketFinder("my_trades.json")

    # Display all pockets
    finder.display_all_pockets()

    # Create visual analysis
    # finder.plot_pockets()


if __name__ == "__main__":
    main()
