#!/usr/bin/env python3
"""
Strategy Analyzer - Bridge Manual Trading to Algorithmic Backtesting
Exports trade journal data to formats compatible with backtesting libraries

Based on:
- Ross Cameron's manual trading approach
- Moon Dev's backtesting and automation framework

Exports:
1. CSV format for backtesting.py library
2. Strategy rules extracted from winning trades
3. Pattern frequency analysis
4. Setup quality correlation
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple


class StrategyAnalyzer:
    def __init__(self, journal_file: str = "trade_journal.json"):
        """
        Initialize strategy analyzer

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
        df['date'] = pd.to_datetime(df['date'])

        return df

    def export_for_backtesting(self, output_file: str = "backtest_data.csv") -> str:
        """
        Export trades in format compatible with backtesting.py library

        Format required:
        - Date, Open, High, Low, Close, Volume
        - Entry/Exit signals as boolean columns

        Args:
            output_file: Output CSV filename

        Returns:
            Path to exported file
        """
        if self.trades_df.empty:
            print("\n❌ No trades to export")
            return None

        # Prepare backtesting format
        backtest_df = self.trades_df.copy()

        # Rename columns to match backtesting.py expectations
        backtest_df['Date'] = backtest_df['date']
        backtest_df['Ticker'] = backtest_df['ticker']
        backtest_df['Entry_Price'] = backtest_df['entry_price']
        backtest_df['Exit_Price'] = backtest_df['exit_price']
        backtest_df['Shares'] = backtest_df['shares']
        backtest_df['P&L'] = backtest_df['gross_pnl']
        backtest_df['Win'] = backtest_df['result'] == 'WIN'
        backtest_df['MACD_Positive'] = backtest_df['macd_positive']
        backtest_df['Pattern'] = backtest_df['pattern']
        backtest_df['Setup_Quality'] = backtest_df['setup_quality']

        # Select relevant columns
        export_cols = [
            'Date', 'Ticker', 'Entry_Price', 'Exit_Price', 'Shares',
            'P&L', 'Win', 'MACD_Positive', 'Pattern', 'Setup_Quality',
            'entry_time', 'exit_time', 'notes'
        ]

        export_df = backtest_df[export_cols]

        # Save to CSV
        output_path = Path(output_file)
        export_df.to_csv(output_path, index=False)

        print(f"\n✅ Exported {len(export_df)} trades to {output_path}")
        return str(output_path)

    def extract_winning_rules(self) -> Dict[str, any]:
        """
        Extract rules from winning trades to automate

        Returns:
            Dictionary of winning strategy rules
        """
        if self.trades_df.empty:
            return {}

        winners = self.trades_df[self.trades_df['result'] == 'WIN']
        losers = self.trades_df[self.trades_df['result'] == 'LOSS']

        if winners.empty:
            print("\n❌ No winning trades to analyze")
            return {}

        rules = {
            'total_trades': len(self.trades_df),
            'winning_trades': len(winners),
            'losing_trades': len(losers),
            'win_rate': (len(winners) / len(self.trades_df)) * 100,

            # Price range analysis
            'winning_price_range': {
                'min': float(winners['entry_price'].min()),
                'max': float(winners['entry_price'].max()),
                'avg': float(winners['entry_price'].mean()),
                'median': float(winners['entry_price'].median())
            },

            # MACD correlation
            'macd_positive_correlation': {
                'wins_with_macd': int((winners['macd_positive'] == True).sum()),
                'wins_total': len(winners),
                'win_rate_with_macd': float((winners[winners['macd_positive'] == True].shape[0] / winners.shape[0] * 100) if not winners.empty else 0)
            },

            # Pattern analysis
            'best_patterns': winners.groupby('pattern').agg({
                'gross_pnl': ['sum', 'mean', 'count']
            }).round(2).to_dict(),

            # Setup quality correlation
            'setup_quality_stats': winners.groupby('setup_quality').agg({
                'gross_pnl': ['mean', 'count']
            }).round(2).to_dict(),

            # Hold time analysis
            'avg_hold_time': self._calculate_avg_hold_time(winners),

            # Profit targets hit
            'avg_profit_pct': float(((winners['exit_price'] - winners['entry_price']) / winners['entry_price'] * 100).mean())
        }

        return rules

    def _calculate_avg_hold_time(self, df: pd.DataFrame) -> str:
        """Calculate average hold time in minutes"""
        if df.empty or 'entry_time' not in df.columns:
            return "N/A"

        try:
            hold_times = []
            for _, row in df.iterrows():
                entry = datetime.strptime(row['entry_time'], "%H:%M")
                exit = datetime.strptime(row['exit_time'], "%H:%M")
                delta = (exit - entry).total_seconds() / 60
                hold_times.append(delta)

            avg_minutes = np.mean(hold_times)
            return f"{avg_minutes:.1f} minutes"
        except:
            return "N/A"

    def generate_strategy_report(self, output_file: str = "strategy_report.txt"):
        """
        Generate comprehensive strategy report for automation

        Args:
            output_file: Output text filename
        """
        rules = self.extract_winning_rules()

        if not rules:
            print("\n❌ No data to generate report")
            return

        report = []
        report.append("="*80)
        report.append("STRATEGY ANALYSIS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)
        report.append("")

        # Overall Stats
        report.append("📊 OVERALL PERFORMANCE")
        report.append("="*80)
        report.append(f"Total Trades: {rules['total_trades']}")
        report.append(f"Winning Trades: {rules['winning_trades']}")
        report.append(f"Losing Trades: {rules['losing_trades']}")
        report.append(f"Win Rate: {rules['win_rate']:.1f}%")
        report.append(f"Target Win Rate: 75% (Ross Cameron standard)")
        report.append("")

        # Automatable Rules
        report.append("🤖 AUTOMATABLE STRATEGY RULES")
        report.append("="*80)
        report.append("")

        report.append("1. PRICE RANGE FILTER:")
        pr = rules['winning_price_range']
        report.append(f"   - Minimum: ${pr['min']:.2f}")
        report.append(f"   - Maximum: ${pr['max']:.2f}")
        report.append(f"   - Average: ${pr['avg']:.2f}")
        report.append(f"   - Median: ${pr['median']:.2f}")
        report.append(f"   ✅ CODE: entry_price >= {pr['min']:.2f} and entry_price <= {pr['max']:.2f}")
        report.append("")

        report.append("2. MACD VALIDATION:")
        macd = rules['macd_positive_correlation']
        report.append(f"   - Wins with MACD Positive: {macd['wins_with_macd']}/{macd['wins_total']}")
        report.append(f"   - Win Rate with MACD: {macd['win_rate_with_macd']:.1f}%")
        if macd['win_rate_with_macd'] >= 80:
            report.append(f"   ✅ CODE: macd_positive == True  # STRONG CORRELATION")
        else:
            report.append(f"   ⚠️  CODE: macd_positive == True  # MODERATE CORRELATION")
        report.append("")

        report.append("3. PROFIT TARGET:")
        report.append(f"   - Average Profit %: {rules['avg_profit_pct']:.2f}%")
        report.append(f"   ✅ CODE: take_profit = entry_price * (1 + {rules['avg_profit_pct']/100:.4f})")
        report.append("")

        report.append("4. HOLD TIME:")
        report.append(f"   - Average: {rules['avg_hold_time']}")
        report.append(f"   ✅ CODE: max_hold_time = {rules['avg_hold_time']}")
        report.append("")

        # Pattern Analysis
        report.append("📈 PATTERN PERFORMANCE")
        report.append("="*80)
        if self.trades_df.empty:
            report.append("No pattern data available")
        else:
            pattern_stats = self.trades_df.groupby('pattern').agg({
                'gross_pnl': ['sum', 'mean', 'count'],
                'result': lambda x: (x == 'WIN').sum()
            }).round(2)
            pattern_stats.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Wins']
            pattern_stats['Win Rate %'] = (pattern_stats['Wins'] / pattern_stats['Trades'] * 100).round(1)

            for pattern, row in pattern_stats.iterrows():
                report.append(f"\n{pattern}:")
                report.append(f"   Total P&L: ${row['Total P&L']:,.2f}")
                report.append(f"   Win Rate: {row['Win Rate %']:.1f}%")
                report.append(f"   Trades: {int(row['Trades'])}")
                if row['Win Rate %'] >= 75:
                    report.append(f"   ✅ AUTOMATE: High win rate - good candidate")
                else:
                    report.append(f"   ⚠️  CAUTION: Win rate below 75% target")

        report.append("")

        # Recommendations
        report.append("💡 AUTOMATION RECOMMENDATIONS")
        report.append("="*80)
        report.append("")

        if rules['win_rate'] >= 75:
            report.append("✅ READY FOR AUTOMATION:")
            report.append("   Your win rate meets Ross Cameron's 75% target.")
            report.append("   Strategy rules are consistent and can be coded.")
            report.append("")
            report.append("   Next Steps:")
            report.append("   1. Use backtest_ross_strategy.py to validate on historical data")
            report.append("   2. Use strategy_bridge.py to generate bot skeleton code")
            report.append("   3. Test with Moon Dev's paper trading setup")
        else:
            report.append("⚠️  MORE DATA NEEDED:")
            report.append(f"   Current win rate: {rules['win_rate']:.1f}% (Target: 75%)")
            report.append("   Continue manual trading to build confidence in strategy.")
            report.append("")
            report.append("   Focus on:")
            report.append("   - Only trade 5-star setups")
            report.append("   - Verify MACD positive before entry")
            report.append("   - Wait for clear pullback patterns")

        report.append("")
        report.append("="*80)

        # Write to file
        report_text = "\n".join(report)
        with open(output_file, 'w') as f:
            f.write(report_text)

        print(report_text)
        print(f"\n💾 Report saved to {output_file}")

    def export_for_moon_dev(self, output_file: str = "moon_dev_export.json"):
        """
        Export in Moon Dev's nice_funks.py format

        Args:
            output_file: Output JSON filename
        """
        if self.trades_df.empty:
            print("\n❌ No trades to export")
            return

        # Convert to Moon Dev format
        moon_dev_data = {
            'strategy_name': 'Ross_Cameron_5_Pillar',
            'description': 'Momentum day trading with pullback entries',
            'trades': [],
            'summary': {
                'total_trades': len(self.trades_df),
                'win_rate': float((self.trades_df['result'] == 'WIN').sum() / len(self.trades_df) * 100),
                'total_pnl': float(self.trades_df['gross_pnl'].sum()),
                'avg_pnl': float(self.trades_df['gross_pnl'].mean()),
                'sharp_ratio': None  # Calculate after backtesting
            }
        }

        # Add each trade
        for _, trade in self.trades_df.iterrows():
            moon_dev_data['trades'].append({
                'date': trade['date'].strftime('%Y-%m-%d'),
                'ticker': trade['ticker'],
                'entry': {
                    'price': float(trade['entry_price']),
                    'time': trade['entry_time'],
                    'macd_positive': bool(trade['macd_positive']),
                    'setup_quality': int(trade['setup_quality'])
                },
                'exit': {
                    'price': float(trade['exit_price']),
                    'time': trade['exit_time']
                },
                'position': {
                    'shares': int(trade['shares']),
                    'pnl': float(trade['gross_pnl'])
                },
                'pattern': trade['pattern'],
                'notes': trade.get('notes', '')
            })

        # Save to JSON
        with open(output_file, 'w') as f:
            json.dump(moon_dev_data, f, indent=2)

        print(f"\n✅ Exported {len(moon_dev_data['trades'])} trades in Moon Dev format")
        print(f"💾 Saved to {output_file}")

        return output_file

    def display_export_summary(self):
        """Display summary of available exports"""
        if self.trades_df.empty:
            print("\n❌ No trading data available")
            print("💡 Start logging trades with trade_journal.py")
            return

        print(f"\n{'='*80}")
        print(f"📊 STRATEGY ANALYZER - EXPORT CENTER")
        print(f"{'='*80}")
        print(f"\nTrades Available: {len(self.trades_df)}")
        print(f"Date Range: {self.trades_df['date'].min().strftime('%Y-%m-%d')} to {self.trades_df['date'].max().strftime('%Y-%m-%d')}")
        print(f"Win Rate: {(self.trades_df['result'] == 'WIN').sum() / len(self.trades_df) * 100:.1f}%")
        print(f"Total P&L: ${self.trades_df['gross_pnl'].sum():,.2f}")

        print(f"\n📁 AVAILABLE EXPORTS:")
        print(f"{'='*80}")
        print(f"1. Backtesting CSV (backtest_data.csv)")
        print(f"   - Compatible with backtesting.py library")
        print(f"   - Use with backtest_ross_strategy.py")
        print(f"")
        print(f"2. Strategy Report (strategy_report.txt)")
        print(f"   - Winning rules extraction")
        print(f"   - Automatable code snippets")
        print(f"   - Performance analysis")
        print(f"")
        print(f"3. Moon Dev Format (moon_dev_export.json)")
        print(f"   - Compatible with nice_funks.py")
        print(f"   - Ready for bot integration")
        print(f"   - Sharp ratio calculation ready")
        print(f"\n{'='*80}\n")


def main():
    """Example usage"""
    # Initialize analyzer
    analyzer = StrategyAnalyzer("my_trades.json")

    # Display export options
    analyzer.display_export_summary()

    # Export for backtesting
    analyzer.export_for_backtesting("backtest_data.csv")

    # Generate strategy report
    analyzer.generate_strategy_report("strategy_report.txt")

    # Export for Moon Dev
    analyzer.export_for_moon_dev("moon_dev_export.json")


if __name__ == "__main__":
    main()
