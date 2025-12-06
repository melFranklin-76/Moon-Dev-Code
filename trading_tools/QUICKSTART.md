# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd trading_tools
pip install -r requirements.txt
```

### Step 2: Launch the Dashboard

```bash
python trading_dashboard.py
```

That's it! You now have access to all tools in one place.

---

## 📖 First Time Using the Tools?

### Morning Trading Routine

#### 1. **Pre-Market (6:30 AM - 7:00 AM)**
   - Review Webull screener for top gainers
   - Note stocks up 10%+ with news
   - Run the 5-Pillar Scanner (Option 1)

#### 2. **Market Open (7:00 AM - 10:00 AM)**
   - Calculate position size (Option 2)
   - Analyze MACD/Volume (Option 3)
   - Wait for pullback setup
   - Execute trade on Webull

#### 3. **Post-Trade (After Exit)**
   - Log the trade (Option 4)
   - Review performance (Option 6)
   - Study what worked/didn't work

---

## 🎯 Quick Examples

### Example 1: Run Scanner
```bash
python five_pillar_scanner.py
```
Enter tickers or use demo mode.

### Example 2: Calculate Position
```bash
python position_calculator.py
```
Enter your account balance and entry price.

### Example 3: Log a Trade
```bash
python trade_journal.py
```
Records your trade with all details.

### Example 4: View Performance
```bash
python performance_tracker.py
```
See your accuracy, P/L ratio, and insights.

---

## 💡 Tips for Success

1. **Start in Simulator**: Practice 10 trades before using real money
2. **Focus on Quality**: Only take 4-5 star setups
3. **One Trade Per Day**: Don't force trades
4. **Track Everything**: Log every trade in the journal
5. **Review Weekly**: Check performance tracker every Friday

---

## ⚠️ Common Mistakes to Avoid

❌ Trading without MACD confirmation
❌ Chasing stocks after the move
❌ Ignoring the volume profile
❌ Trading outside 7-10 AM window
❌ Not logging trades

✅ Wait for pullback
✅ Confirm MACD is positive
✅ Check volume profile
✅ Trade during hot hours
✅ Log everything

---

## 🆘 Troubleshooting

### "No module named 'yfinance'"
```bash
pip install yfinance pandas numpy matplotlib
```

### "No data available"
- Check your internet connection
- Verify ticker symbol is correct
- Try during market hours (7 AM - 4 PM EST)

### "Permission denied"
```bash
chmod +x *.py
```

---

## 📚 Learn More

- Read the full [README.md](README.md)
- Watch Ross Cameron's videos
- Join Warrior Trading community
- Practice in simulator

---

**Remember: $200 a day keeps the 9-5 away!** 💰
