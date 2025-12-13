#!/usr/bin/env python3
"""
Position Size Calculator
Based on Ross Cameron's 10% Risk Management Rule

For small cash accounts on Webull:
- Use 98% of buying power
- Calculate max shares based on risk tolerance
- Track daily profit targets (10% growth goal)
"""

import math
from datetime import datetime


class PositionCalculator:
    def __init__(self, account_balance: float, max_risk_percent: float = 10.0):
        """
        Initialize position calculator

        Args:
            account_balance: Current account balance
            max_risk_percent: Maximum risk per trade as percentage (default 10%)
        """
        self.account_balance = account_balance
        self.max_risk_percent = max_risk_percent
        self.webull_buying_power_pct = 0.98  # Webull uses 98% of buying power

    def calculate_position_size(self,
                                entry_price: float,
                                stop_loss: float = None,
                                risk_per_share: float = None) -> dict:
        """
        Calculate position size based on account balance and risk

        Args:
            entry_price: Planned entry price
            stop_loss: Stop loss price (optional)
            risk_per_share: Risk per share in dollars (optional, alternative to stop_loss)

        Returns:
            dict with position sizing details
        """
        # Calculate usable buying power (98% for Webull)
        buying_power = self.account_balance * self.webull_buying_power_pct

        # Calculate max risk in dollars
        max_risk_dollars = self.account_balance * (self.max_risk_percent / 100)

        # If stop loss is provided, calculate risk per share
        if stop_loss:
            risk_per_share = abs(entry_price - stop_loss)
        elif risk_per_share is None:
            # Default: assume 10% stop loss if none provided
            risk_per_share = entry_price * 0.10

        # Calculate max shares based on risk
        max_shares_by_risk = math.floor(max_risk_dollars / risk_per_share)

        # Calculate max shares based on buying power
        max_shares_by_capital = math.floor(buying_power / entry_price)

        # Use the smaller of the two
        position_size = min(max_shares_by_risk, max_shares_by_capital)

        # Calculate actual dollar amounts
        position_value = position_size * entry_price
        total_risk = position_size * risk_per_share
        risk_percent = (total_risk / self.account_balance) * 100

        return {
            'position_size': position_size,
            'entry_price': entry_price,
            'position_value': position_value,
            'buying_power': buying_power,
            'buying_power_used_pct': (position_value / buying_power) * 100,
            'stop_loss': stop_loss if stop_loss else entry_price - risk_per_share,
            'risk_per_share': risk_per_share,
            'total_risk': total_risk,
            'risk_percent': risk_percent,
            'account_balance': self.account_balance
        }

    def calculate_profit_targets(self, entry_price: float, position_size: int) -> dict:
        """
        Calculate profit targets based on Ross's 10% daily goal

        Args:
            entry_price: Entry price per share
            position_size: Number of shares

        Returns:
            dict with profit target prices and amounts
        """
        # 10% account growth target
        target_profit_dollars = self.account_balance * 0.10

        # Calculate price per share needed for 10% account growth
        price_move_needed = target_profit_dollars / position_size

        # Profit targets
        target_price_10pct = entry_price + price_move_needed

        # Additional targets (conservative and aggressive)
        target_price_5pct = entry_price + (price_move_needed / 2)
        target_price_15pct = entry_price + (price_move_needed * 1.5)

        return {
            'entry_price': entry_price,
            'position_size': position_size,
            'target_10pct_account_growth': {
                'price': target_price_10pct,
                'profit': target_profit_dollars,
                'percent_move': ((target_price_10pct - entry_price) / entry_price) * 100
            },
            'conservative_5pct': {
                'price': target_price_5pct,
                'profit': target_profit_dollars / 2,
                'percent_move': ((target_price_5pct - entry_price) / entry_price) * 100
            },
            'aggressive_15pct': {
                'price': target_price_15pct,
                'profit': target_profit_dollars * 1.5,
                'percent_move': ((target_price_15pct - entry_price) / entry_price) * 100
            }
        }

    def display_position_sizing(self, calc: dict):
        """Display position sizing in formatted output"""
        print(f"\n{'='*60}")
        print(f"POSITION SIZE CALCULATOR - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        print(f"\n📊 ACCOUNT INFO:")
        print(f"   Balance: ${calc['account_balance']:,.2f}")
        print(f"   Buying Power (98%): ${calc['buying_power']:,.2f}")
        print(f"   Max Risk ({self.max_risk_percent}%): ${calc['total_risk']:,.2f}")

        print(f"\n🎯 POSITION DETAILS:")
        print(f"   Entry Price: ${calc['entry_price']:.2f}")
        print(f"   Position Size: {calc['position_size']:,} shares")
        print(f"   Position Value: ${calc['position_value']:,.2f}")
        print(f"   Buying Power Used: {calc['buying_power_used_pct']:.1f}%")

        print(f"\n🛡️  RISK MANAGEMENT:")
        print(f"   Stop Loss: ${calc['stop_loss']:.2f}")
        print(f"   Risk Per Share: ${calc['risk_per_share']:.2f}")
        print(f"   Total Risk: ${calc['total_risk']:,.2f} ({calc['risk_percent']:.1f}%)")

        print(f"\n{'='*60}\n")

    def display_profit_targets(self, targets: dict):
        """Display profit targets in formatted output"""
        print(f"\n{'='*60}")
        print(f"PROFIT TARGETS - 10% DAILY GROWTH GOAL")
        print(f"{'='*60}")
        print(f"\n📈 ENTRY:")
        print(f"   Price: ${targets['entry_price']:.2f}")
        print(f"   Shares: {targets['position_size']:,}")

        print(f"\n🎯 TARGETS:")

        print(f"\n   💰 CONSERVATIVE (5% Account Growth):")
        t = targets['conservative_5pct']
        print(f"      Exit Price: ${t['price']:.2f}")
        print(f"      Profit: ${t['profit']:.2f}")
        print(f"      Stock Move: +{t['percent_move']:.1f}%")

        print(f"\n   🎯 PRIMARY TARGET (10% Account Growth):")
        t = targets['target_10pct_account_growth']
        print(f"      Exit Price: ${t['price']:.2f}")
        print(f"      Profit: ${t['profit']:.2f}")
        print(f"      Stock Move: +{t['percent_move']:.1f}%")

        print(f"\n   🚀 AGGRESSIVE (15% Account Growth):")
        t = targets['aggressive_15pct']
        print(f"      Exit Price: ${t['price']:.2f}")
        print(f"      Profit: ${t['profit']:.2f}")
        print(f"      Stock Move: +{t['percent_move']:.1f}%")

        print(f"\n{'='*60}\n")


def main():
    """Example usage"""
    # Example: $2,800 account (like Ross on Day 3)
    account_balance = 2800.00

    calc = PositionCalculator(
        account_balance=account_balance,
        max_risk_percent=10.0
    )

    # Example: Planning to buy a $3.64 stock (like ATON from the video)
    entry_price = 3.64
    stop_loss = 3.44  # 20 cent stop loss (about 5.5%)

    # Calculate position size
    position = calc.calculate_position_size(
        entry_price=entry_price,
        stop_loss=stop_loss
    )

    # Display position sizing
    calc.display_position_sizing(position)

    # Calculate profit targets
    targets = calc.calculate_profit_targets(
        entry_price=entry_price,
        position_size=position['position_size']
    )

    # Display profit targets
    calc.display_profit_targets(targets)

    # Ross's actual trade example from the video
    print(f"\n{'='*60}")
    print(f"📺 ROSS'S ACTUAL TRADE (ATON - Day 3)")
    print(f"{'='*60}")
    print(f"Entry: $3.64")
    print(f"Exit: $4.03")
    print(f"Shares: ~769 shares (based on $2,800 buying power)")
    print(f"Profit: $291.56")
    print(f"Account Growth: ~10.4%")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
