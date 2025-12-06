# Installation Notes

## ✅ Core Tools (No External Data Required)

The following tools work perfectly **without needing yfinance** or any market data API:

### 1. **Position Calculator** ✅
```bash
python position_calculator.py
```
- Calculates position sizes
- Profit targets
- Risk management
- Works 100% offline

### 2. **Trade Journal** ✅
```bash
python trade_journal.py
```
- Log all your trades
- Track performance
- Works 100% offline

### 3. **Performance Tracker** ✅
```bash
python performance_tracker.py
```
- Analyzes your journal data
- Shows accuracy, P/L ratio
- Performance insights
- Works 100% offline

---

## ⚠️ Optional Tools (Require yfinance)

These tools fetch live market data and require `yfinance`:

### 4. **Five Pillar Scanner** (Optional)
### 5. **MACD Volume Analyzer** (Optional)

---

## 🔧 Installation Options

### Option 1: Core Tools Only (Recommended to Start)

```bash
pip install pandas numpy matplotlib
```

This gives you:
- ✅ Position calculator
- ✅ Trade journal
- ✅ Performance tracker

You can manually enter stock data from Webull or other sources.

### Option 2: Full Installation (Advanced)

If you want the scanner and MACD analyzer, try:

```bash
# Try standard install
pip install yfinance

# If that fails, try without multitasking
pip install --no-deps yfinance
pip install pandas numpy requests beautifulsoup4 html5lib

# Or use alternative data source
# (You can modify the scanner to use Webull API or CSV imports)
```

---

## 💡 Recommended Workflow

### For Small Account Traders:

1. **Use Webull Screener** to find top gainers
   - No need for the Python scanner
   - Webull shows you the data you need

2. **Use Position Calculator** before each trade
   ```bash
   python position_calculator.py
   ```

3. **Log Trades in Journal** after each trade
   ```bash
   python trade_journal.py
   ```

4. **Review Performance** weekly
   ```bash
   python performance_tracker.py
   ```

This workflow works perfectly without yfinance!

---

## 🎯 Alternative: Manual Data Entry

You can use all tools with manual data from Webull:

### Scanner Alternative:
- Use Webull's built-in screener
- Filter by: Top Gainers > 10%, Price $2-$20
- Check float on finviz.com or Webull
- Manually verify the 5 pillars

### MACD Alternative:
- Use Webull's charting tools
- Add MACD indicator on chart
- Manually verify MACD is positive before entry

---

## 🐛 Known Issues

### Issue: yfinance installation fails

**Error:**
```
ERROR: Failed building wheel for multitasking
```

**Solution:**
This is a known Python 3.12 compatibility issue with the multitasking dependency.

**Workarounds:**
1. Use Python 3.10 or 3.11 instead
2. Skip yfinance and use manual data entry
3. Use Webull's built-in tools for scanning

---

## 📊 What You Can Do Without yfinance

### ✅ Full Functionality:
- Calculate position sizes for any price
- Log all trades with details
- Track performance metrics
- Get actionable insights
- Export to CSV

### ⚠️ Manual Input Required:
- Stock screening (use Webull instead)
- MACD analysis (use Webull charts instead)
- Real-time data (use Webull Level 2)

---

## 🚀 Quick Start (No yfinance)

```bash
# Install core dependencies
pip install pandas numpy matplotlib

# Test position calculator
python position_calculator.py

# Test trade journal
python trade_journal.py

# Test performance tracker
python performance_tracker.py
```

All three work perfectly!

---

## 💰 Trading Workflow (Manual Data)

### 1. Morning Scan (7:00 AM)
- Open Webull screener
- Sort by Top Gainers
- Filter: Price $2-$20, Volume 5x+
- Check news for catalysts

### 2. Position Sizing
```bash
python position_calculator.py
```
- Enter account balance
- Enter entry price from Webull
- Get calculated share size

### 3. Execute Trade
- Use Webull platform
- Check MACD on Webull chart
- Wait for pullback
- Enter trade

### 4. Log Trade
```bash
python trade_journal.py
```
- Record all details
- Note MACD status
- Rate setup quality

### 5. Weekly Review
```bash
python performance_tracker.py
```
- Review metrics
- Identify patterns
- Improve strategy

---

## ✅ Bottom Line

**You can use this toolkit successfully without yfinance!**

The core value is in:
- Position sizing discipline
- Trade journaling consistency
- Performance tracking insights

Use Webull for market data. Use Python for calculations and tracking.

---

## 🆘 Need Help?

- Check the main [README.md](README.md)
- Read the [QUICKSTART.md](QUICKSTART.md)
- Watch Ross Cameron's videos
- Use Webull's support resources
