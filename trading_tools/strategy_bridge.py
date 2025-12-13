#!/usr/bin/env python3
"""
Strategy Bridge - Convert Manual Trading to Algorithmic Bots
Bridges Ross Cameron manual approach with Moon Dev automation

Generates:
1. Bot skeleton code from winning patterns
2. Entry/exit rule functions
3. Risk management integration
4. Backtesting-ready code

Based on:
- Ross Cameron's discretionary rules
- Moon Dev's RBI framework (Research → Backtest → Implement)
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class StrategyBridge:
    def __init__(self, journal_file: str = "trade_journal.json"):
        """
        Initialize strategy bridge

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

        return pd.DataFrame(trades)

    def extract_winning_patterns(self) -> Dict:
        """
        Extract winning patterns from trade journal

        Returns:
            Dictionary of pattern rules
        """
        if self.trades_df.empty:
            return {}

        winners = self.trades_df[self.trades_df['result'] == 'WIN']

        if winners.empty:
            return {}

        # Extract rules from winners
        patterns = {
            'entry_rules': {
                'price_min': float(winners['entry_price'].min()),
                'price_max': float(winners['entry_price'].max()),
                'price_avg': float(winners['entry_price'].mean()),
                'macd_positive_required': (winners['macd_positive'] == True).sum() / len(winners) >= 0.8,
                'best_pattern': winners.groupby('pattern')['gross_pnl'].sum().idxmax(),
                'min_setup_quality': int(winners['setup_quality'].mode()[0]) if not winners['setup_quality'].mode().empty else 5
            },
            'exit_rules': {
                'avg_profit_pct': float(((winners['exit_price'] - winners['entry_price']) / winners['entry_price'] * 100).mean()),
                'max_profit_pct': float(((winners['exit_price'] - winners['entry_price']) / winners['entry_price'] * 100).max()),
                'min_profit_pct': float(((winners['exit_price'] - winners['entry_price']) / winners['entry_price'] * 100).min())
            },
            'risk_management': {
                'stop_loss_pct': 0.02,  # Ross's 2% stop
                'position_size_pct': 0.10  # 10% risk per trade
            }
        }

        return patterns

    def generate_bot_skeleton(self, output_file: str = "ross_cameron_bot.py") -> str:
        """
        Generate bot skeleton code from winning patterns

        Args:
            output_file: Output Python filename

        Returns:
            Path to generated bot file
        """
        patterns = self.extract_winning_patterns()

        if not patterns:
            print("\n❌ No winning patterns to generate bot from")
            print("💡 Log more winning trades first")
            return None

        # Generate bot code
        bot_code = self._generate_bot_code(patterns)

        # Write to file
        with open(output_file, 'w') as f:
            f.write(bot_code)

        print(f"\n✅ Generated bot skeleton: {output_file}")
        print(f"💡 Next steps:")
        print(f"   1. Review and customize the generated code")
        print(f"   2. Test with paper trading")
        print(f"   3. Backtest with backtest_ross_strategy.py")
        print(f"   4. Deploy with Moon Dev's framework")

        return output_file

    def _generate_bot_code(self, patterns: Dict) -> str:
        """Generate the actual bot code"""
        entry = patterns['entry_rules']
        exit_rules = patterns['exit_rules']
        risk = patterns['risk_management']

        code = f'''#!/usr/bin/env python3
"""
Ross Cameron 5-Pillar Momentum Bot
Auto-generated from manual trading patterns

Strategy Rules (extracted from winning trades):
- Price Range: ${entry['price_min']:.2f} - ${entry['price_max']:.2f}
- MACD Positive: {entry['macd_positive_required']}
- Best Pattern: {entry['best_pattern']}
- Min Setup Quality: {entry['min_setup_quality']}/5 stars
- Avg Profit Target: {exit_rules['avg_profit_pct']:.2f}%
- Stop Loss: {risk['stop_loss_pct'] * 100}%

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional


class RossCameronBot:
    def __init__(self, account_balance: float = 2000):
        """
        Initialize Ross Cameron momentum trading bot

        Args:
            account_balance: Starting account balance
        """
        self.account_balance = account_balance
        self.position = None

        # Strategy parameters (from winning trades)
        self.min_price = {entry['price_min']:.2f}
        self.max_price = {entry['price_max']:.2f}
        self.macd_required = {entry['macd_positive_required']}
        self.min_setup_quality = {entry['min_setup_quality']}

        # Exit parameters
        self.profit_target_pct = {exit_rules['avg_profit_pct'] / 100:.4f}  # {exit_rules['avg_profit_pct']:.2f}%
        self.stop_loss_pct = {risk['stop_loss_pct']:.4f}  # {risk['stop_loss_pct'] * 100}%

        # Risk management
        self.risk_per_trade = {risk['position_size_pct']:.2f}  # 10% risk
        self.max_buying_power = 0.98  # Webull 98% limit

        print(f"🤖 Ross Cameron Bot Initialized")
        print(f"   Account Balance: ${self.account_balance:,.2f}")
        print(f"   Price Range: ${self.min_price:.2f} - ${self.max_price:.2f}")
        print(f"   Profit Target: {self.profit_target_pct * 100:.2f}%")

    def get_stock_data(self, ticker: str, period: str = "1d", interval: str = "5m") -> pd.DataFrame:
        """
        Fetch real-time stock data

        Args:
            ticker: Stock symbol
            period: Time period (1d, 5d, 1mo)
            interval: Data interval (1m, 5m, 15m)

        Returns:
            DataFrame with OHLCV data and indicators
        """
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                return None

            # Calculate MACD
            df = self._calculate_macd(df)

            # Calculate relative volume
            df['Rel_Volume'] = df['Volume'] / df['Volume'].rolling(window=20).mean()

            return df

        except Exception as e:
            print(f"Error fetching {{ticker}}: {{e}}")
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

    def check_entry_signal(self, ticker: str, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Check if stock meets entry criteria (Ross Cameron 5-Pillar)

        Args:
            ticker: Stock symbol
            df: OHLCV DataFrame with indicators

        Returns:
            Tuple of (signal, details)
        """
        if df is None or df.empty:
            return False, {{'reason': 'No data'}}

        current = df.iloc[-1]

        # Pillar 1: Price Range (${entry['price_min']:.2f} - ${entry['price_max']:.2f})
        if not (self.min_price <= current['Close'] <= self.max_price):
            return False, {{'reason': f'Price ${{current["Close"]:.2f}} out of range'}}

        # Pillar 2: MACD Positive (from winning trades: {entry['macd_positive_required']})
        if self.macd_required and not current['MACD_Positive']:
            return False, {{'reason': 'MACD not positive'}}

        # Pillar 3: Relative Volume (5x+)
        if pd.isna(current['Rel_Volume']) or current['Rel_Volume'] < 5.0:
            return False, {{'reason': f'Rel volume {{current["Rel_Volume"]:.1f}}x below 5x'}}

        # Pillar 4: Pullback Pattern Detection
        if not self._detect_pullback_pattern(df):
            return False, {{'reason': 'No pullback pattern'}}

        # All criteria met!
        details = {{
            'ticker': ticker,
            'price': current['Close'],
            'macd_positive': current['MACD_Positive'],
            'rel_volume': current['Rel_Volume'],
            'pattern': '{entry['best_pattern']}',  # Your best pattern
            'timestamp': df.index[-1]
        }}

        return True, details

    def _detect_pullback_pattern(self, df: pd.DataFrame) -> bool:
        """
        Detect Ross Cameron's pullback pattern
        Surge → Pullback → New High

        Args:
            df: OHLCV DataFrame

        Returns:
            True if pullback pattern detected
        """
        if len(df) < 10:
            return False

        # Look back 10 bars
        lookback = df.iloc[-10:]

        # Check for surge (big green candle)
        surge_bars = lookback[lookback['Close'] > lookback['Open'] * 1.02]
        if surge_bars.empty:
            return False

        # Check for pullback after surge
        last_surge_idx = surge_bars.index[-1]
        after_surge = df.loc[last_surge_idx:]

        if len(after_surge) < 3:
            return False

        # At least one red candle (pullback)
        pullback_bars = after_surge[after_surge['Close'] < after_surge['Open']]
        if pullback_bars.empty:
            return False

        # Current bar near recent high
        current_high = df.iloc[-1]['High']
        recent_high = lookback['High'].max()

        return current_high >= recent_high * 0.98

    def calculate_position_size(self, entry_price: float) -> int:
        """
        Calculate position size with Ross Cameron risk management

        Args:
            entry_price: Planned entry price

        Returns:
            Number of shares to trade
        """
        # 10% risk, 2% stop loss
        risk_dollars = self.account_balance * self.risk_per_trade
        stop_loss_distance = entry_price * self.stop_loss_pct
        shares = int(risk_dollars / stop_loss_distance)

        # Webull 98% buying power constraint
        max_shares = int((self.account_balance * self.max_buying_power) / entry_price)
        shares = min(shares, max_shares)

        return max(shares, 0)

    def execute_entry(self, ticker: str, entry_price: float, shares: int) -> Dict:
        """
        Execute entry (paper trading simulation)

        Args:
            ticker: Stock symbol
            entry_price: Entry price
            shares: Number of shares

        Returns:
            Position details
        """
        stop_loss = entry_price * (1 - self.stop_loss_pct)
        take_profit = entry_price * (1 + self.profit_target_pct)

        self.position = {{
            'ticker': ticker,
            'entry_price': entry_price,
            'shares': shares,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': datetime.now()
        }}

        print(f"\\n✅ ENTRY: {{ticker}}")
        print(f"   Price: ${{entry_price:.2f}}")
        print(f"   Shares: {{shares:,}}")
        print(f"   Stop Loss: ${{stop_loss:.2f}} ({self.stop_loss_pct * 100:.0f}%)")
        print(f"   Take Profit: ${{take_profit:.2f}} ({self.profit_target_pct * 100:.0f}%)")

        return self.position

    def check_exit_signal(self, current_price: float, macd_positive: bool) -> Tuple[bool, str]:
        """
        Check if should exit position

        Args:
            current_price: Current stock price
            macd_positive: Current MACD status

        Returns:
            Tuple of (should_exit, reason)
        """
        if not self.position:
            return False, "No position"

        # Stop loss hit
        if current_price <= self.position['stop_loss']:
            return True, "STOP_LOSS"

        # Take profit hit
        if current_price >= self.position['take_profit']:
            return True, "TAKE_PROFIT"

        # MACD turned negative (Ross's exit signal)
        if not macd_positive:
            return True, "MACD_NEGATIVE"

        # Time-based exit (30 min max hold from Ross's approach)
        hold_time = (datetime.now() - self.position['entry_time']).total_seconds() / 60
        if hold_time >= 30:
            return True, "TIME_LIMIT"

        return False, "HOLD"

    def execute_exit(self, exit_price: float, exit_reason: str) -> Dict:
        """
        Execute exit

        Args:
            exit_price: Exit price
            exit_reason: Reason for exit

        Returns:
            Trade result
        """
        if not self.position:
            print("❌ No position to exit")
            return None

        # Calculate P&L
        shares = self.position['shares']
        entry_price = self.position['entry_price']
        gross_pnl = (exit_price - entry_price) * shares

        # Update balance
        self.account_balance += gross_pnl

        result = {{
            'ticker': self.position['ticker'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'shares': shares,
            'gross_pnl': gross_pnl,
            'exit_reason': exit_reason,
            'result': 'WIN' if gross_pnl > 0 else 'LOSS'
        }}

        print(f"\\n{'✅' if gross_pnl > 0 else '❌'}} EXIT: {{self.position['ticker']}}")
        print(f"   Entry: ${{entry_price:.2f}} → Exit: ${{exit_price:.2f}}")
        print(f"   P&L: ${{gross_pnl:+,.2f}}")
        print(f"   Reason: {{exit_reason}}")
        print(f"   New Balance: ${{self.account_balance:,.2f}}")

        self.position = None
        return result

    def scan_for_entry(self, tickers: List[str]) -> Optional[Dict]:
        """
        Scan watchlist for entry signals

        Args:
            tickers: List of stock symbols to scan

        Returns:
            Entry signal details if found, None otherwise
        """
        print(f"\\n🔍 Scanning {{len(tickers)}} tickers...")

        for ticker in tickers:
            df = self.get_stock_data(ticker)

            if df is None:
                continue

            signal, details = self.check_entry_signal(ticker, df)

            if signal:
                print(f"\\n🎯 ENTRY SIGNAL FOUND: {{ticker}}")
                print(f"   Price: ${{details['price']:.2f}}")
                print(f"   MACD: {{'Positive' if details['macd_positive'] else 'Negative'}}")
                print(f"   Rel Volume: {{details['rel_volume']:.1f}}x")
                print(f"   Pattern: {{details['pattern']}}")

                return details

        print("   No entry signals found")
        return None


def main():
    """
    Example bot usage (paper trading)
    """
    # Initialize bot
    bot = RossCameronBot(account_balance=2000)

    # Watchlist (top gainers from Webull screener)
    watchlist = ['PTON', 'AMD', 'NVDA', 'TSLA']

    print("\\n🤖 Starting Ross Cameron Bot (Paper Trading)")
    print("="*80)

    # Scan for entry
    signal = bot.scan_for_entry(watchlist)

    if signal:
        # Calculate position size
        shares = bot.calculate_position_size(signal['price'])

        if shares > 0:
            # Execute entry
            bot.execute_entry(signal['ticker'], signal['price'], shares)

            # Monitor position (in real bot, this would be a loop)
            print("\\n💡 Position opened. Monitor for exit signals...")
            print("   Implement monitoring loop in production version")
    else:
        print("\\n⏳ No entry signals. Wait for next scan cycle...")


if __name__ == "__main__":
    main()
'''

        return code

    def generate_nice_funks_integration(self, output_file: str = "ross_nice_funks.py") -> str:
        """
        Generate Moon Dev nice_funks.py compatible functions

        Args:
            output_file: Output Python filename

        Returns:
            Path to generated file
        """
        patterns = self.extract_winning_patterns()

        if not patterns:
            print("\n❌ No patterns to generate")
            return None

        code = f'''#!/usr/bin/env python3
"""
Ross Cameron Strategy - Moon Dev nice_funks.py Integration
Functions for Moon Dev's bot framework

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


# ==================== STRATEGY RULES (from manual trades) ====================
PRICE_MIN = {patterns['entry_rules']['price_min']:.2f}
PRICE_MAX = {patterns['entry_rules']['price_max']:.2f}
MACD_REQUIRED = {patterns['entry_rules']['macd_positive_required']}
PROFIT_TARGET_PCT = {patterns['exit_rules']['avg_profit_pct'] / 100:.4f}
STOP_LOSS_PCT = {patterns['risk_management']['stop_loss_pct']:.4f}
POSITION_SIZE_PCT = {patterns['risk_management']['position_size_pct']:.2f}


# ==================== NICE FUNKS ====================

def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate MACD indicator (Moon Dev style)

    Args:
        df: OHLCV DataFrame

    Returns:
        DataFrame with MACD columns
    """
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_histogram'] = histogram
    df['macd_positive'] = df['macd_histogram'] > 0

    return df


def calculate_relative_volume(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calculate relative volume

    Args:
        df: OHLCV DataFrame
        window: Rolling window for average

    Returns:
        DataFrame with rel_volume column
    """
    df['rel_volume'] = df['volume'] / df['volume'].rolling(window=window).mean()
    return df


def check_price_filter(price: float) -> bool:
    """
    Ross Cameron price range filter

    Args:
        price: Current stock price

    Returns:
        True if price in valid range
    """
    return PRICE_MIN <= price <= PRICE_MAX


def check_macd_filter(macd_positive: bool) -> bool:
    """
    MACD filter (from winning trades)

    Args:
        macd_positive: Is MACD histogram positive

    Returns:
        True if MACD meets criteria
    """
    if MACD_REQUIRED:
        return macd_positive
    return True  # MACD not required if win rate without it is high


def detect_pullback_pattern(df: pd.DataFrame, lookback: int = 10) -> bool:
    """
    Ross Cameron pullback pattern detection
    Surge → Pullback → New High

    Args:
        df: OHLCV DataFrame
        lookback: Bars to look back

    Returns:
        True if pullback pattern detected
    """
    if len(df) < lookback:
        return False

    recent = df.iloc[-lookback:]

    # Surge detection (2%+ green candle)
    surge_bars = recent[recent['close'] > recent['open'] * 1.02]
    if surge_bars.empty:
        return False

    # Pullback detection (red candle after surge)
    last_surge_idx = surge_bars.index[-1]
    after_surge = df.loc[last_surge_idx:]

    if len(after_surge) < 3:
        return False

    pullback_bars = after_surge[after_surge['close'] < after_surge['open']]
    if pullback_bars.empty:
        return False

    # New high attempt
    current_high = df.iloc[-1]['high']
    recent_high = recent['high'].max()

    return current_high >= recent_high * 0.98


def calculate_position_size(account_balance: float, entry_price: float,
                           stop_loss_pct: float = STOP_LOSS_PCT,
                           risk_pct: float = POSITION_SIZE_PCT) -> int:
    """
    Ross Cameron position sizing with risk management

    Args:
        account_balance: Current account balance
        entry_price: Planned entry price
        stop_loss_pct: Stop loss percentage
        risk_pct: Risk percentage of account

    Returns:
        Number of shares to trade
    """
    risk_dollars = account_balance * risk_pct
    stop_loss_distance = entry_price * stop_loss_pct
    shares = int(risk_dollars / stop_loss_distance)

    # Webull 98% buying power
    max_shares = int((account_balance * 0.98) / entry_price)
    shares = min(shares, max_shares)

    return max(shares, 0)


def calculate_profit_targets(entry_price: float) -> Dict[str, float]:
    """
    Calculate profit targets (from winning trades average)

    Args:
        entry_price: Entry price

    Returns:
        Dictionary of price targets
    """
    return {{
        'stop_loss': entry_price * (1 - STOP_LOSS_PCT),
        'target_1': entry_price * (1 + PROFIT_TARGET_PCT / 2),  # 50% of target
        'target_2': entry_price * (1 + PROFIT_TARGET_PCT),      # Full target
        'trailing_stop': entry_price * 0.98  # 2% trailing
    }}


def check_entry_signal(df: pd.DataFrame, ticker: str) -> Tuple[bool, Dict]:
    """
    Main entry signal checker (Ross Cameron 5-Pillar)

    Args:
        df: OHLCV DataFrame with indicators
        ticker: Stock symbol

    Returns:
        Tuple of (signal, details)
    """
    if df.empty:
        return False, {{'reason': 'No data'}}

    current = df.iloc[-1]

    # Pillar 1: Price Range
    if not check_price_filter(current['close']):
        return False, {{'reason': f'Price out of range'}}

    # Pillar 2: MACD
    if not check_macd_filter(current.get('macd_positive', False)):
        return False, {{'reason': 'MACD not positive'}}

    # Pillar 3: Relative Volume
    if pd.isna(current.get('rel_volume', 0)) or current.get('rel_volume', 0) < 5.0:
        return False, {{'reason': 'Low relative volume'}}

    # Pillar 4: Pullback Pattern
    if not detect_pullback_pattern(df):
        return False, {{'reason': 'No pullback pattern'}}

    # All criteria met
    return True, {{
        'ticker': ticker,
        'price': current['close'],
        'macd_positive': current.get('macd_positive', False),
        'rel_volume': current.get('rel_volume', 0)
    }}


def check_exit_signal(entry_price: float, current_price: float,
                      macd_positive: bool, hold_minutes: float) -> Tuple[bool, str]:
    """
    Check exit signals

    Args:
        entry_price: Entry price
        current_price: Current price
        macd_positive: Current MACD status
        hold_minutes: Minutes held

    Returns:
        Tuple of (should_exit, reason)
    """
    targets = calculate_profit_targets(entry_price)

    # Stop loss
    if current_price <= targets['stop_loss']:
        return True, 'STOP_LOSS'

    # Take profit
    if current_price >= targets['target_2']:
        return True, 'TARGET_HIT'

    # MACD turned negative
    if not macd_positive:
        return True, 'MACD_NEGATIVE'

    # Time limit (30 min max)
    if hold_minutes >= 30:
        return True, 'TIME_LIMIT'

    return False, 'HOLD'


# ==================== BACKTESTING FUNCTIONS ====================

def calculate_sharp_ratio(returns: pd.Series) -> float:
    """
    Calculate Sharp Ratio (Moon Dev target: 2.0+)

    Args:
        returns: Series of trade returns

    Returns:
        Sharp ratio
    """
    if returns.std() == 0:
        return 0
    return (returns.mean() / returns.std()) * np.sqrt(252)


def calculate_max_drawdown(balances: pd.Series) -> float:
    """
    Calculate maximum drawdown percentage

    Args:
        balances: Series of account balances

    Returns:
        Max drawdown as percentage
    """
    peak = balances.expanding().max()
    drawdown = (balances - peak) / peak * 100
    return abs(drawdown.min())


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    print("Ross Cameron Nice Funks Integration")
    print("="*80)
    print(f"Price Range: ${{PRICE_MIN:.2f}} - ${{PRICE_MAX:.2f}}")
    print(f"MACD Required: {{MACD_REQUIRED}}")
    print(f"Profit Target: {{PROFIT_TARGET_PCT * 100:.2f}}%")
    print(f"Stop Loss: {{STOP_LOSS_PCT * 100:.2f}}%")
    print("="*80)
'''

        with open(output_file, 'w') as f:
            f.write(code)

        print(f"\n✅ Generated nice_funks integration: {output_file}")
        return output_file

    def display_bridge_summary(self):
        """Display summary of bridge capabilities"""
        print(f"\n{'='*80}")
        print(f"🌉 STRATEGY BRIDGE - MANUAL TO ALGO")
        print(f"{'='*80}")
        print(f"\n📊 AVAILABLE CONVERSIONS:")
        print(f"{'='*80}")
        print(f"")
        print(f"1. FULL BOT SKELETON (ross_cameron_bot.py)")
        print(f"   - Complete trading bot with Ross's rules")
        print(f"   - Entry/exit logic from winning trades")
        print(f"   - Risk management integration")
        print(f"   - Paper trading ready")
        print(f"")
        print(f"2. MOON DEV INTEGRATION (ross_nice_funks.py)")
        print(f"   - Compatible with Moon Dev framework")
        print(f"   - Modular function library")
        print(f"   - Drop-in replacement for nice_funks.py")
        print(f"   - Backtesting ready")
        print(f"")
        print(f"💡 WORKFLOW:")
        print(f"   1. Log winning trades manually (trade_journal.py)")
        print(f"   2. Generate bot code (strategy_bridge.py)")
        print(f"   3. Backtest bot (backtest_ross_strategy.py)")
        print(f"   4. Paper trade to validate")
        print(f"   5. Deploy to live (Moon Dev framework)")
        print(f"\n{'='*80}\n")


def main():
    """Example usage"""
    # Initialize bridge
    bridge = StrategyBridge("my_trades.json")

    # Display capabilities
    bridge.display_bridge_summary()

    # Generate bot skeleton
    bridge.generate_bot_skeleton("ross_cameron_bot.py")

    # Generate Moon Dev integration
    bridge.generate_nice_funks_integration("ross_nice_funks.py")


if __name__ == "__main__":
    main()
