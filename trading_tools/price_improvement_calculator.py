#!/usr/bin/env python3
"""
Price Improvement Calculator
Based on Ross Cameron's Day 4 Analysis

Shows the advantage of commission-free brokers vs. direct access brokers:
- Price improvement (~1 cent/share on Webull)
- Zero commissions
- Break-even trades can be winners
- Slippage comparison
"""

from datetime import datetime


class PriceImprovementCalculator:
    def __init__(self):
        """Initialize calculator with broker fee structures"""
        # Commission-free broker (Webull)
        self.webull_price_improvement = 0.01  # ~1 cent per share (highest in industry)
        self.webull_commission = 0.0

        # Direct access broker (typical)
        self.direct_commission_per_share = 0.005  # $0.005/share
        self.direct_ecn_fee = 0.003  # $0.003/share ECN fee
        self.direct_platform_fee = 100.0  # $100/month platform fee
        self.direct_slippage = 0.02  # ~2 cents slippage per trade

    def calculate_webull_trade(self, shares: int, entry_price: float, exit_price: float) -> dict:
        """
        Calculate P&L on Webull with price improvement

        Args:
            shares: Number of shares traded
            entry_price: Entry price per share
            exit_price: Exit price per share

        Returns:
            dict with trade details
        """
        # Price improvement on entry and exit
        entry_improvement = shares * self.webull_price_improvement
        exit_improvement = shares * self.webull_price_improvement

        # Gross P&L
        gross_pnl = (exit_price - entry_price) * shares

        # Add price improvement
        net_pnl = gross_pnl + entry_improvement + exit_improvement

        return {
            'broker': 'Webull (Commission-Free)',
            'shares': shares,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'gross_pnl': gross_pnl,
            'price_improvement': entry_improvement + exit_improvement,
            'commissions': 0.0,
            'fees': 0.0,
            'slippage': 0.0,
            'net_pnl': net_pnl
        }

    def calculate_direct_access_trade(self, shares: int, entry_price: float, exit_price: float) -> dict:
        """
        Calculate P&L on direct access broker with commissions/slippage

        Args:
            shares: Number of shares traded
            entry_price: Entry price per share
            exit_price: Exit price per share

        Returns:
            dict with trade details
        """
        # Slippage on entry and exit
        entry_slippage = shares * self.direct_slippage
        exit_slippage = shares * self.direct_slippage
        total_slippage = entry_slippage + exit_slippage

        # Commissions
        commissions = shares * self.direct_commission_per_share * 2  # Entry + Exit

        # ECN fees
        ecn_fees = shares * self.direct_ecn_fee * 2  # Entry + Exit

        # Gross P&L
        gross_pnl = (exit_price - entry_price) * shares

        # Net P&L
        net_pnl = gross_pnl - total_slippage - commissions - ecn_fees

        return {
            'broker': 'Direct Access (Commission)',
            'shares': shares,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'gross_pnl': gross_pnl,
            'price_improvement': 0.0,
            'commissions': commissions,
            'fees': ecn_fees,
            'slippage': total_slippage,
            'net_pnl': net_pnl
        }

    def compare_brokers(self, shares: int, entry_price: float, exit_price: float):
        """
        Compare the same trade on both broker types

        Args:
            shares: Number of shares traded
            entry_price: Entry price per share
            exit_price: Exit price per share
        """
        webull = self.calculate_webull_trade(shares, entry_price, exit_price)
        direct = self.calculate_direct_access_trade(shares, entry_price, exit_price)

        difference = webull['net_pnl'] - direct['net_pnl']

        print(f"\n{'='*80}")
        print(f"PRICE IMPROVEMENT CALCULATOR - BROKER COMPARISON")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")

        print(f"\n📊 TRADE DETAILS:")
        print(f"   Shares: {shares:,}")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Exit: ${exit_price:.2f}")
        print(f"   Price Move: ${exit_price - entry_price:.2f} ({((exit_price - entry_price) / entry_price * 100):+.2f}%)")

        print(f"\n{'='*80}")
        print(f"💚 WEBULL (COMMISSION-FREE)")
        print(f"{'='*80}")
        print(f"   Gross P&L: ${webull['gross_pnl']:+.2f}")
        print(f"   Price Improvement: +${webull['price_improvement']:.2f}")
        print(f"   Commissions: $0.00")
        print(f"   Fees: $0.00")
        print(f"   Slippage: $0.00")
        print(f"   ─────────────────────")
        print(f"   NET P&L: ${webull['net_pnl']:+.2f}")

        print(f"\n{'='*80}")
        print(f"📉 DIRECT ACCESS BROKER")
        print(f"{'='*80}")
        print(f"   Gross P&L: ${direct['gross_pnl']:+.2f}")
        print(f"   Price Improvement: $0.00")
        print(f"   Commissions: -${direct['commissions']:.2f}")
        print(f"   ECN Fees: -${direct['fees']:.2f}")
        print(f"   Slippage: -${direct['slippage']:.2f}")
        print(f"   ─────────────────────")
        print(f"   NET P&L: ${direct['net_pnl']:+.2f}")

        print(f"\n{'='*80}")
        print(f"💰 COMPARISON")
        print(f"{'='*80}")

        if difference > 0:
            print(f"   ✅ WEBULL ADVANTAGE: +${difference:.2f}")
            print(f"   You saved ${difference:.2f} by using commission-free routing!")
        elif difference < 0:
            print(f"   ⚠️  DIRECT ACCESS ADVANTAGE: +${abs(difference):.2f}")
            print(f"   Direct access was better by ${abs(difference):.2f}")
        else:
            print(f"   ➖ EQUAL: Both brokers resulted in same P&L")

        # Break-even analysis
        if abs(webull['gross_pnl']) < 10:  # Near break-even
            print(f"\n   💡 BREAK-EVEN TRADE INSIGHT:")
            if webull['net_pnl'] > 0 and direct['net_pnl'] < 0:
                print(f"   This break-even trade was a WINNER on Webull (+${webull['net_pnl']:.2f})")
                print(f"   but a LOSER on direct access (-${abs(direct['net_pnl']):.2f})!")
                print(f"   Price improvement made the difference!")

        print(f"\n{'='*80}\n")

        return webull, direct, difference

    def monthly_savings(self, avg_trades_per_day: int, avg_shares: int, avg_improvement: float = 0.01):
        """
        Calculate monthly savings using commission-free broker

        Args:
            avg_trades_per_day: Average number of trades per day
            avg_shares: Average shares per trade
            avg_improvement: Average savings per share (default $0.01)

        Returns:
            Monthly savings amount
        """
        # Trading days per month (approx 21)
        trading_days = 21

        # Total trades per month
        monthly_trades = avg_trades_per_day * trading_days

        # Price improvement savings
        price_improvement_savings = monthly_trades * avg_shares * avg_improvement * 2  # Entry + Exit

        # Commission savings (vs direct access)
        commission_savings = monthly_trades * avg_shares * self.direct_commission_per_share * 2

        # ECN fee savings
        ecn_savings = monthly_trades * avg_shares * self.direct_ecn_fee * 2

        # Platform fee savings
        platform_savings = self.direct_platform_fee

        total_savings = price_improvement_savings + commission_savings + ecn_savings + platform_savings

        print(f"\n{'='*80}")
        print(f"📅 MONTHLY SAVINGS CALCULATOR")
        print(f"{'='*80}")
        print(f"\n📊 YOUR TRADING PROFILE:")
        print(f"   Trades per day: {avg_trades_per_day}")
        print(f"   Shares per trade: {avg_shares:,}")
        print(f"   Trading days per month: {trading_days}")
        print(f"   Total monthly trades: {monthly_trades}")

        print(f"\n💰 MONTHLY SAVINGS BREAKDOWN:")
        print(f"   Price Improvement: +${price_improvement_savings:.2f}")
        print(f"   Commission Savings: +${commission_savings:.2f}")
        print(f"   ECN Fee Savings: +${ecn_savings:.2f}")
        print(f"   Platform Fee Savings: +${platform_savings:.2f}")
        print(f"   ─────────────────────")
        print(f"   TOTAL MONTHLY SAVINGS: ${total_savings:.2f}")

        print(f"\n📈 ANNUAL IMPACT:")
        print(f"   Yearly Savings: ${total_savings * 12:,.2f}")
        print(f"\n{'='*80}\n")

        return total_savings


def main():
    """Example usage - Ross's Day 4 trade"""
    calc = PriceImprovementCalculator()

    print("\n🎯 EXAMPLE: ROSS'S DAY 4 TRADE (SPRC)")
    print("="*80)

    # Ross's actual trade from Day 4
    shares = 932
    entry = 3.30  # Approximate
    exit = 3.31   # Near break-even

    # Compare brokers
    webull, direct, diff = calc.compare_brokers(shares, entry, exit)

    print("\n📝 ROSS'S ACTUAL RESULTS:")
    print(f"   Webull: +$11.70 (small winner)")
    print(f"   Direct Access (Lightseed): -$2,600 (loser)")
    print(f"   Difference: This demonstrates the power of price improvement!")

    # Monthly savings for small account trader
    print("\n" + "="*80)
    print("📊 SMALL ACCOUNT TRADER SCENARIO")
    print("="*80)
    print("1 trade per day (cash account)")
    print("~1,000 shares per trade")

    calc.monthly_savings(
        avg_trades_per_day=1,
        avg_shares=1000,
        avg_improvement=0.01
    )


if __name__ == "__main__":
    main()
