#!/usr/bin/env python3
"""
Trading Dashboard - All-in-One Interface
Ross Cameron's Small Account Strategy Tools

Combines all tools into one interactive dashboard
"""

import os
from datetime import datetime


class TradingDashboard:
    def __init__(self):
        self.journal_file = "my_trades.json"

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name != 'nt' else 'cls')

    def display_header(self):
        """Display dashboard header"""
        self.clear_screen()
        print(f"\n{'='*80}")
        print(f"🎯 ROSS CAMERON'S SMALL ACCOUNT TRADING DASHBOARD")
        print(f"{'='*80}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Strategy: 5-Pillar Stock Selection + Pullback Pattern")
        print(f"{'='*80}\n")

    def display_menu(self):
        """Display main menu"""
        print(f"\n{'='*80}")
        print(f"MAIN MENU")
        print(f"{'='*80}")
        print(f"\n📊 PRE-MARKET TOOLS:")
        print(f"   1. 🔍 Run 5-Pillar Stock Scanner")
        print(f"   2. 💰 Calculate Position Size")
        print(f"   3. 📈 Analyze MACD & Volume")

        print(f"\n📝 TRADE MANAGEMENT:")
        print(f"   4. ✍️  Log a Trade")
        print(f"   5. 📖 View Recent Trades")

        print(f"\n📊 PERFORMANCE ANALYSIS:")
        print(f"   6. 📈 View Performance Dashboard")
        print(f"   7. 💾 Export Trades to CSV")

        print(f"\n🎓 LEARNING:")
        print(f"   8. 📚 View Strategy Guide")
        print(f"   9. ℹ️  About This Dashboard")

        print(f"\n   0. 🚪 Exit")

        print(f"\n{'='*80}")

    def run_scanner(self):
        """Run the 5-pillar scanner"""
        print(f"\n{'='*80}")
        print(f"5-PILLAR STOCK SCANNER")
        print(f"{'='*80}\n")

        print("Enter tickers to scan (comma-separated) or press Enter for demo:")
        user_input = input("Tickers: ").strip()

        if user_input:
            tickers = [t.strip().upper() for t in user_input.split(',')]
        else:
            print("\nUsing demo tickers: PTON, AMC, SNDL")
            tickers = ['PTON', 'AMC', 'SNDL']

        print(f"\nScanning {len(tickers)} stocks...")
        print(f"⚠️  For live trading, get top gainers from Webull screener\n")

        from five_pillar_scanner import FivePillarScanner

        scanner = FivePillarScanner(
            min_price=float(input("Min price (default $2): ") or "2"),
            max_price=float(input("Max price (default $20): ") or "20"),
            max_float=float(input("Max float in millions (default 20M): ") or "20") * 1_000_000,
            min_rel_volume=float(input("Min relative volume (default 5x): ") or "5"),
            min_gain_percent=float(input("Min gain % (default 10%): ") or "10")
        )

        results = scanner.scan_watchlist(tickers)
        scanner.display_results(results)

        input("\nPress Enter to continue...")

    def calculate_position(self):
        """Calculate position size"""
        print(f"\n{'='*80}")
        print(f"POSITION SIZE CALCULATOR")
        print(f"{'='*80}\n")

        from position_calculator import PositionCalculator

        account_balance = float(input("Account balance: $"))
        entry_price = float(input("Entry price: $"))

        use_stop = input("Set stop loss? (y/n): ").lower() == 'y'

        if use_stop:
            stop_loss = float(input("Stop loss price: $"))
            calc = PositionCalculator(account_balance=account_balance)
            position = calc.calculate_position_size(entry_price=entry_price, stop_loss=stop_loss)
        else:
            risk_pct = float(input("Risk per share as % (default 10%): ") or "10")
            calc = PositionCalculator(account_balance=account_balance)
            position = calc.calculate_position_size(
                entry_price=entry_price,
                risk_per_share=entry_price * (risk_pct / 100)
            )

        calc.display_position_sizing(position)

        # Calculate profit targets
        targets = calc.calculate_profit_targets(entry_price, position['position_size'])
        calc.display_profit_targets(targets)

        input("\nPress Enter to continue...")

    def analyze_macd_volume(self):
        """Analyze MACD and volume"""
        print(f"\n{'='*80}")
        print(f"MACD & VOLUME ANALYZER")
        print(f"{'='*80}\n")

        from macd_volume_analyzer import MACDVolumeAnalyzer

        ticker = input("Enter ticker to analyze: ").strip().upper()

        if not ticker:
            print("❌ Ticker required")
            input("\nPress Enter to continue...")
            return

        analyzer = MACDVolumeAnalyzer(ticker)
        setup = analyzer.get_current_setup()
        analyzer.display_analysis(setup)

        is_valid = analyzer.quick_check()
        print(f"\n🎯 FINAL VERDICT:")
        if is_valid:
            print(f"   ✅ {ticker} meets Ross Cameron's entry criteria")
        else:
            print(f"   ❌ {ticker} does NOT meet criteria - wait for better setup")

        input("\nPress Enter to continue...")

    def log_trade(self):
        """Log a trade"""
        print(f"\n{'='*80}")
        print(f"LOG A TRADE")
        print(f"{'='*80}\n")

        from trade_journal import TradeJournal

        journal = TradeJournal(self.journal_file)

        ticker = input("Ticker: ").strip().upper()
        entry_price = float(input("Entry price: $"))
        exit_price = float(input("Exit price: $"))
        shares = int(input("Shares: "))

        entry_time = input("Entry time (HH:MM, or Enter for now): ").strip()
        exit_time = input("Exit time (HH:MM, or Enter for now): ").strip()

        macd_positive = input("MACD positive at entry? (y/n): ").lower() == 'y'
        volume_profile = input("Volume profile (e.g., 'Strong buying'): ").strip()
        pattern = input("Pattern (e.g., 'Pullback'): ").strip() or "Pullback"
        setup_quality = int(input("Setup quality (1-5 stars): ") or "3")
        notes = input("Notes: ").strip()

        journal.add_trade(
            ticker=ticker,
            entry_price=entry_price,
            exit_price=exit_price,
            shares=shares,
            entry_time=entry_time if entry_time else None,
            exit_time=exit_time if exit_time else None,
            macd_positive=macd_positive,
            volume_profile=volume_profile,
            pattern=pattern,
            setup_quality=setup_quality,
            notes=notes
        )

        input("\nPress Enter to continue...")

    def view_recent_trades(self):
        """View recent trades"""
        print(f"\n{'='*80}")
        print(f"RECENT TRADES")
        print(f"{'='*80}\n")

        from trade_journal import TradeJournal

        journal = TradeJournal(self.journal_file)
        n = int(input("How many trades to show? (default 10): ") or "10")
        journal.display_recent_trades(n)
        journal.display_stats()

        input("\nPress Enter to continue...")

    def view_performance(self):
        """View performance dashboard"""
        print(f"\n{'='*80}")
        print(f"LOADING PERFORMANCE DASHBOARD...")
        print(f"{'='*80}\n")

        from performance_tracker import PerformanceTracker

        tracker = PerformanceTracker(self.journal_file)
        tracker.display_dashboard()

        input("\nPress Enter to continue...")

    def export_trades(self):
        """Export trades to CSV"""
        print(f"\n{'='*80}")
        print(f"EXPORT TRADES")
        print(f"{'='*80}\n")

        from trade_journal import TradeJournal

        journal = TradeJournal(self.journal_file)

        filename = input("Filename (or Enter for auto): ").strip()
        if filename:
            journal.export_to_csv(filename)
        else:
            journal.export_to_csv()

        input("\nPress Enter to continue...")

    def show_strategy_guide(self):
        """Show strategy guide"""
        self.clear_screen()
        print(f"\n{'='*80}")
        print(f"ROSS CAMERON'S 5-PILLAR STRATEGY GUIDE")
        print(f"{'='*80}\n")

        print("🎯 THE 5 PILLARS OF STOCK SELECTION:")
        print("   1. Price Range: $2-$20 (focus $2-$4 for small accounts)")
        print("   2. Float: Under 20M shares (prefer <5M in cold markets)")
        print("   3. Relative Volume: 5x+ above average")
        print("   4. Percentage Gain: Up at least 10%")
        print("   5. News Catalyst: Breaking news (verify manually)")

        print("\n📈 THE BREAD AND BUTTER PULLBACK PATTERN:")
        print("   1. Stock surges up → hits scanner alert")
        print("   2. Pullback forms → do your due diligence")
        print("   3. First candle makes new high → ENTRY SIGNAL")
        print("   4. MACD MUST be POSITIVE ✓")
        print("   5. Volume profile shows strong buying")

        print("\n🛡️  RISK MANAGEMENT:")
        print("   • Daily Target: 10% account growth")
        print("   • Max Loss: 10% per trade")
        print("   • Position Size: 98% of buying power")
        print("   • Trading Window: 7 AM - 10 AM EST")
        print("   • One Trade Per Day: Cash account")

        print("\n📊 TARGET METRICS:")
        print("   • Accuracy: 75%+")
        print("   • P/L Ratio: 2:1 (avg winner 2x avg loser)")
        print("   • Setup Quality: Focus on 4-5 star setups only")

        print("\n💡 ROSS'S MANTRAS:")
        print("   • 'Get in, get green, get out'")
        print("   • '$200 a day keeps the 9-5 away'")
        print("   • 'Survive till you thrive'")
        print("   • 'Base hit trader - not home runs'")

        print(f"\n{'='*80}")

        input("\nPress Enter to continue...")

    def show_about(self):
        """Show about information"""
        self.clear_screen()
        print(f"\n{'='*80}")
        print(f"ABOUT THIS DASHBOARD")
        print(f"{'='*80}\n")

        print("This trading dashboard is based on Ross Cameron's publicly")
        print("shared momentum day trading strategy from Warrior Trading.")

        print("\n📺 LEARN MORE:")
        print("   • YouTube: @DaytradeWarrior")
        print("   • Website: algotradecamp.com")
        print("   • Small Account Challenge Series")

        print("\n⚠️  DISCLAIMER:")
        print("   • This is for educational purposes only")
        print("   • Not financial advice")
        print("   • Trading involves substantial risk")
        print("   • Practice in simulator first")
        print("   • Past performance ≠ future results")

        print("\n🛠️  TOOLS INCLUDED:")
        print("   • 5-Pillar Stock Scanner")
        print("   • Position Size Calculator")
        print("   • MACD & Volume Analyzer")
        print("   • Trade Journal")
        print("   • Performance Tracker")

        print("\n📁 FILES:")
        print(f"   • Journal: {self.journal_file}")
        print(f"   • Location: {os.getcwd()}")

        print(f"\n{'='*80}")

        input("\nPress Enter to continue...")

    def run(self):
        """Main dashboard loop"""
        while True:
            self.display_header()
            self.display_menu()

            choice = input("\nSelect option (0-9): ").strip()

            if choice == '0':
                print("\n👋 Happy trading! Remember: Get in, get green, get out!\n")
                break
            elif choice == '1':
                self.run_scanner()
            elif choice == '2':
                self.calculate_position()
            elif choice == '3':
                self.analyze_macd_volume()
            elif choice == '4':
                self.log_trade()
            elif choice == '5':
                self.view_recent_trades()
            elif choice == '6':
                self.view_performance()
            elif choice == '7':
                self.export_trades()
            elif choice == '8':
                self.show_strategy_guide()
            elif choice == '9':
                self.show_about()
            else:
                print("\n❌ Invalid option. Please try again.")
                input("\nPress Enter to continue...")


def main():
    """Launch the dashboard"""
    dashboard = TradingDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
