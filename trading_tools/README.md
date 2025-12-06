# Trading Tools - Ross Cameron's Small Account Strategy

> **Based on Warrior Trading's 5-Pillar Stock Selection & Small Account Challenge**

A complete Python toolkit for day traders following Ross Cameron's momentum trading strategy. Perfect for small accounts ($2,000+) doing options scalping and 1-2 day trades.

---

## 🎯 Strategy Overview

### The 5 Pillars of Stock Selection

1. **Price Range**: $2-$20 (focus on $2-$4 for small accounts)
2. **Float**: Under 20M shares (preferably <5M in cold markets)
3. **Relative Volume**: 5x+ above average
4. **Percentage Gain**: Up at least 10%
5. **News Catalyst**: Breaking news (manual verification)

### The Bread and Butter Pullback Pattern

1. Stock surges up (hits scanner alert)
2. Pullback forms (time to do due diligence)
3. First candle makes new high (entry signal)
4. MACD must be POSITIVE
5. Volume profile must show strong buying

### Risk Management

- **Daily Target**: 10% account growth
- **Max Loss**: 10% per trade/day
- **Position Size**: 98% of buying power (Webull)
- **Trading Window**: 7 AM - 10 AM EST (most profitable)
- **One Trade Per Day**: Cash account limitation

---

## 📦 Tools Included

### 1. **Five Pillar Scanner** (`five_pillar_scanner.py`)
Scans stocks that meet all 5 criteria for momentum trading.

**Features:**
- Price range filtering
- Float analysis
- Relative volume calculation
- Percentage gain tracking
- News catalyst flagging

**Usage:**
```bash
python five_pillar_scanner.py
```

---

### 2. **Position Calculator** (`position_calculator.py`)
Calculates optimal position size based on account balance and risk tolerance.

**Features:**
- 98% buying power calculation (Webull)
- 10% max risk enforcement
- Profit target calculator (5%, 10%, 15%)
- Stop loss positioning

**Usage:**
```bash
python position_calculator.py
```

**Example:**
```python
from position_calculator import PositionCalculator

calc = PositionCalculator(account_balance=2800, max_risk_percent=10)
position = calc.calculate_position_size(entry_price=3.64, stop_loss=3.44)
```

---

### 3. **Trade Journal** (`trade_journal.py`)
Track your one-trade-per-day with detailed logging.

**Features:**
- Entry/exit tracking
- MACD status logging
- Volume profile notes
- Pattern recognition
- Setup quality rating (1-5 stars)

**Usage:**
```bash
python trade_journal.py
```

**Add a trade:**
```python
from trade_journal import TradeJournal

journal = TradeJournal("my_trades.json")
journal.add_trade(
    ticker="ATON",
    entry_price=3.64,
    exit_price=4.03,
    shares=769,
    macd_positive=True,
    volume_profile="Strong buying",
    pattern="Pullback",
    setup_quality=5
)
```

---

### 4. **Performance Tracker** (`performance_tracker.py`)
Analyze your performance metrics like Ross Cameron.

**Features:**
- Accuracy tracking (target: 75%)
- Profit/Loss ratio (target: 2:1)
- Performance by price range
- Performance by hold time
- Performance by MACD status
- Performance by setup quality
- Actionable insights

**Usage:**
```bash
python performance_tracker.py
```

---

### 5. **MACD & Volume Analyzer** (`macd_volume_analyzer.py`)
Real-time analysis of MACD and volume for entry signals.

**Features:**
- MACD calculation and status
- Volume profile analysis (buying vs selling)
- Topping tail detection
- Setup quality evaluation
- Entry recommendations

**Usage:**
```bash
python macd_volume_analyzer.py
```

**Quick check:**
```python
from macd_volume_analyzer import MACDVolumeAnalyzer

analyzer = MACDVolumeAnalyzer("ATON")
setup = analyzer.get_current_setup()
analyzer.display_analysis(setup)

# Boolean check
is_valid = analyzer.quick_check()  # Returns True/False
```

---

## 💎 OPTIONS TRADING TOOLKIT (NEW!) 🚀

### **Ross Cameron's 5-Pillar Strategy Optimized for Options**

**Perfect for small accounts ($2K-$10K) who want faster gains with defined risk**

Trade OPTIONS instead of shares for:
- ✅ **More Leverage:** Control 1000 shares with $500 vs $6,000
- ✅ **Bigger % Gains:** 50-200% per trade vs 5-10%
- ✅ **Defined Risk:** Max loss = premium paid
- ✅ **Small Capital:** Trade with $100-$500 per position

---

### 🔍 **Options Scanner** (`options_scanner.py`)
Find stocks with 5-pillar setups + liquid options to trade.

**Features:**
- Scans for Ross Cameron's 5 pillars
- Validates options liquidity (spread, open interest, volume)
- Identifies best strikes (ITM/ATM with high delta)
- Ranks setups by quality (1-5 stars)

**Usage:**
```bash
python options_scanner.py
```

---

### 💰 **Options Position Calculator** (`options_position_calculator.py`)
Calculate position size with Greeks analysis.

**Features:**
- Contract quantity based on 5% risk
- Greeks calculator (Delta, Theta, Gamma, Vega)
- Break-even price calculator
- Profit targets for different stock moves
- Multiple strike comparison

**Usage:**
```bash
python options_position_calculator.py
```

---

### 📒 **Options Trade Journal** (`options_trade_journal.py`)
Track options trades with complete details.

**Features:**
- Strike, expiration, premium tracking
- Greeks at entry/exit
- Theta decay impact analysis
- Performance by option type (ITM/ATM/OTM)

**Usage:**
```bash
python options_trade_journal.py
```

---

### 📖 Complete Options Guide

📘 **See [OPTIONS_GUIDE.md](OPTIONS_GUIDE.md)** for complete workflow, strategies, and examples!

---

## 🤖 Automation Tools

### Bridge Manual Trading → Algorithmic Bots

**Based on Moon Dev's RBI Framework (Research → Backtest → Implement)**

Once you've built consistency with manual trading (75%+ win rate over 20+ trades), these tools help you automate your strategy:

---

### 6. **Strategy Analyzer** (`strategy_analyzer.py`)
Export and analyze your manual trades for automation.

**Features:**
- Export to backtesting.py CSV format
- Extract winning rules from trade journal
- Generate strategy reports with code snippets
- Moon Dev nice_funks.py integration

**Usage:**
```bash
python strategy_analyzer.py
```

**Outputs:**
- `backtest_data.csv` - Ready for backtesting
- `strategy_report.txt` - Automatable rules
- `moon_dev_export.json` - Bot integration format

---

### 7. **Backtest Module** (`backtest_ross_strategy.py`)
Test Ross's 5-pillar strategy on historical data.

**Features:**
- Simulates trades on historical 5-min data
- Tests pullback pattern detection
- Calculates win rate, P/L ratio, Sharp ratio
- Validates MACD entry rule
- Identifies edge cases and failures

**Usage:**
```bash
python backtest_ross_strategy.py
```

**Targets:**
- Win Rate: 75%+
- P/L Ratio: 2:1+
- Sharp Ratio: 2.0+ (Moon Dev standard)
- Max Drawdown: <10%

---

### 8. **Strategy Bridge** (`strategy_bridge.py`)
Generate bot code from your winning patterns.

**Features:**
- Extracts patterns from winning trades
- Generates complete trading bot skeleton
- Creates Moon Dev nice_funks.py functions
- Paper trading ready code

**Usage:**
```bash
python strategy_bridge.py
```

**Outputs:**
- `ross_cameron_bot.py` - Full trading bot
- `ross_nice_funks.py` - Moon Dev integration

---

### Automation Workflow:

```
1. Manual Trading (20+ trades) → trade_journal.py
2. Find Pocket → pocket_finder.py
3. Export & Analyze → strategy_analyzer.py
4. Backtest Strategy → backtest_ross_strategy.py
5. Generate Bot → strategy_bridge.py
6. Paper Trade → ross_cameron_bot.py
7. Deploy Live → Moon Dev framework
```

📖 **See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md) for complete details**

---

## 🚀 Installation

### 1. Install Python Dependencies

```bash
cd trading_tools
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
python -c "import yfinance; import pandas; print('✅ All dependencies installed!')"
```

---

## 📖 Daily Trading Workflow

### Morning Routine (7:00 AM - 10:00 AM)

1. **Scan for Opportunities**
   ```bash
   python five_pillar_scanner.py
   ```
   - Review stocks that pass all 5 pillars
   - Verify news catalyst manually
   - Check Webull Level 2 data

2. **Calculate Position Size**
   ```bash
   python position_calculator.py
   ```
   - Enter your account balance
   - Enter planned entry price
   - Set your stop loss
   - Note the recommended shares

3. **Analyze Entry Setup**
   ```bash
   python macd_volume_analyzer.py
   ```
   - Enter the ticker
   - Confirm MACD is POSITIVE
   - Confirm volume profile is good
   - Watch for pullback

4. **Execute Trade**
   - Wait for the pullback
   - Enter on first candle making new high
   - Use Webull hotkeys (Shift+1 to buy)
   - Set profit target (10% account growth)

5. **Log the Trade**
   ```bash
   python trade_journal.py
   ```
   - Record entry/exit
   - Note MACD status
   - Rate setup quality

6. **Review Performance**
   ```bash
   python performance_tracker.py
   ```
   - Check daily/weekly stats
   - Review actionable insights
   - Adjust strategy if needed

---

## 📊 Understanding the Metrics

### Critical Metrics (Ross Cameron's Dashboard)

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Accuracy** | 75% | Win rate consistency |
| **P/L Ratio** | 2:1 | Average winner 2x average loser |
| **Price Range** | $2-$4 | Best for small accounts |
| **Hold Time** | <10 min | Scalping strategy |
| **MACD** | Positive | Only trade with momentum |
| **Setup Quality** | 4-5 stars | Focus on A+ setups |

---

## 🎓 Learning Resources

### Ross Cameron's Videos
- **Small Account Challenge**: [Watch on YouTube](https://youtu.be/-6gIqlVhxeI)
- **Warrior Trading**: [algotradecamp.com](https://algotradecamp.com/?utm_source=github)

### Key Concepts
- **Base Hit Trading**: Take profits quickly, don't hold and hope
- **Get In, Get Green, Get Out**: Ross's mantra
- **200 a Day Keeps the 9-5 Away**: Consistent small profits
- **Survive Till You Thrive**: Risk management first

---

## ⚠️ Important Notes

### Cash Account Limitations
- **One Trade Per Day**: Funds settle overnight
- **T+1 Settlement**: Can't reuse funds until next day
- **98% Buying Power**: Webull limitation

### Pattern Day Trader Rule Update
- **Old Rule**: $25,000 minimum for day trading
- **New Rule**: $2,000 minimum (FINRA approved 2024)
- **Coming Soon**: Will allow faster trading on small accounts

### Risk Warnings
- **Trading is risky**
- **Past performance ≠ future results**
- **Never risk more than 10% per trade**
- **Practice in simulator first**
- **Only trade with money you can afford to lose**

---

## 🛠️ Customization

### Adjust Scanner Settings

Edit `five_pillar_scanner.py`:
```python
scanner = FivePillarScanner(
    min_price=2.0,      # Adjust for your account size
    max_price=4.0,      # Lower for very small accounts
    max_float=5_000_000,  # Tighter in cold markets
    min_rel_volume=5.0,
    min_gain_percent=10.0
)
```

### Adjust Risk Settings

Edit `position_calculator.py`:
```python
calc = PositionCalculator(
    account_balance=2000,
    max_risk_percent=10.0  # Lower to 5% for conservative
)
```

---

## 📁 File Structure

```
trading_tools/
├── five_pillar_scanner.py      # Stock scanner
├── position_calculator.py       # Position sizing
├── trade_journal.py             # Trade logging
├── performance_tracker.py       # Metrics analysis
├── macd_volume_analyzer.py      # Entry analysis
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── my_trades.json              # Your trade journal (auto-created)
```

---

## 🤝 Contributing

This toolkit is based on Ross Cameron's publicly shared strategy. Feel free to:
- Add new features
- Improve existing tools
- Share your performance data
- Report bugs or issues

---

## 📜 Disclaimer

**This toolkit is for educational purposes only.**

- Not financial advice
- Trading involves substantial risk
- Practice in simulator first
- Consult with a licensed financial advisor
- The creator is not responsible for trading losses

---

## 🎯 Success Checklist

- [ ] Install all dependencies
- [ ] Practice in simulator
- [ ] Log 10 simulated trades
- [ ] Achieve 75%+ accuracy in sim
- [ ] Achieve 2:1 P/L ratio in sim
- [ ] Fund Webull account ($2,000+)
- [ ] Start with small positions
- [ ] Focus on A+ setups only
- [ ] Track performance daily
- [ ] Review weekly metrics

---

## 📞 Support

- **Ross Cameron's Channel**: [YouTube](https://www.youtube.com/@DaytradeWarrior)
- **Warrior Trading**: [warriortrading.com](https://warriortrading.com)
- **Webull**: Free commission trading platform

---

**Remember: Get in, get green, get out. Trade small, trade smart, trade Ross's way.** ✅

**$200 a day keeps the 9-5 away!** 💰
