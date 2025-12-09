#!/usr/bin/env python3
"""
ROSS CAMERON OPTIONS TRADING APP
Mobile-Optimized Web Interface for iPhone

Access all your trading tools from your phone:
- Options Scanner
- Position Calculator
- Trade Journal
- Performance Dashboard

No terminal commands needed - just tap buttons! 📱
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import our trading tools
from options_scanner import OptionsScanner
from options_position_calculator import OptionsPositionCalculator
from options_trade_journal import OptionsTradeJournal

# Page config - optimized for mobile
st.set_page_config(
    page_title="Ross Cameron Options Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
<style>
    /* Mobile-friendly styling */
    .main {
        padding: 0rem 0.5rem;
    }

    .stButton>button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }

    .stNumberInput>div>div>input {
        font-size: 1.2rem;
        height: 3rem;
    }

    .stTextInput>div>div>input {
        font-size: 1.2rem;
        height: 3rem;
    }

    /* Card styling */
    .trade-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .success-card {
        background: #d4edda;
        border-left-color: #28a745;
    }

    .warning-card {
        background: #fff3cd;
        border-left-color: #ffc107;
    }

    .danger-card {
        background: #f8d7da;
        border-left-color: #dc3545;
    }

    h1 {
        font-size: 2rem !important;
        margin-bottom: 1rem !important;
    }

    h2 {
        font-size: 1.5rem !important;
        margin-top: 1rem !important;
    }

    h3 {
        font-size: 1.3rem !important;
    }

    /* Star ratings */
    .stars {
        font-size: 1.5rem;
        color: #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'account_balance' not in st.session_state:
    st.session_state.account_balance = 2800.0

if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = None

# Main navigation
def main():
    # App header
    st.markdown("# 📈 Ross Cameron Options Trader")
    st.markdown("*Trade smarter with the 5-Pillar Strategy*")

    # Account balance at top - editable
    st.markdown("### 💰 Account Balance")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_balance = st.number_input(
            "Current Balance ($)",
            min_value=100.0,
            max_value=1000000.0,
            value=st.session_state.account_balance,
            step=100.0,
            key="balance_input",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("💾 Save", key="save_balance"):
            st.session_state.account_balance = new_balance
            st.success("✅ Saved!")

    st.markdown("---")

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Scanner",
        "💰 Calculator",
        "📒 Journal",
        "📊 Dashboard"
    ])

    with tab1:
        scanner_page()

    with tab2:
        calculator_page()

    with tab3:
        journal_page()

    with tab4:
        dashboard_page()


def scanner_page():
    """Options Scanner Page"""
    st.markdown("## 🔍 Options Scanner")
    st.markdown("*Find stocks with 5-pillar setups + liquid options*")

    # Instructions
    with st.expander("📖 How to use"):
        st.markdown("""
        **Step 1:** Open Webull → Quotes → Gainers

        **Step 2:** Find stocks up 10%+ in $2-$20 range

        **Step 3:** Enter tickers below (comma-separated)

        **Step 4:** Tap "Scan" and wait for results!

        **Example:** PTON, SAVA, AMD, NVDA
        """)

    # Input area
    tickers_input = st.text_input(
        "Enter tickers to scan:",
        placeholder="PTON, SAVA, AMD",
        help="Comma-separated ticker symbols"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 SCAN NOW", type="primary"):
            if tickers_input:
                with st.spinner("🔍 Scanning for tradeable options..."):
                    scan_stocks(tickers_input)
            else:
                st.warning("⚠️ Please enter at least one ticker")

    with col2:
        if st.button("📋 Demo Scan"):
            with st.spinner("🔍 Running demo scan..."):
                scan_stocks("PTON, AMD, NVDA, TSLA")

    # Display results
    if st.session_state.scan_results is not None:
        display_scan_results()


def scan_stocks(tickers_input):
    """Run the options scanner"""
    try:
        # Parse tickers
        tickers = [t.strip().upper() for t in tickers_input.split(',')]

        # Initialize scanner
        scanner = OptionsScanner(
            min_price=2.0,
            max_price=20.0,
            max_float=20_000_000,
            min_rel_volume=5.0,
            min_gain_percent=10.0,
            min_open_interest=100,
            max_spread_percent=10.0,
            min_option_volume=50
        )

        # Scan each ticker
        results = []
        for ticker in tickers:
            result = scanner.scan_ticker(ticker)
            if result:
                results.append(result)

        st.session_state.scan_results = results

        if results:
            st.success(f"✅ Found {len(results)} tradeable setup(s)!")
        else:
            st.warning("❌ No stocks passed all criteria. Try different tickers!")

    except Exception as e:
        st.error(f"❌ Error scanning: {str(e)}")
        st.session_state.scan_results = []


def display_scan_results():
    """Display scan results as cards"""
    results = st.session_state.scan_results

    if not results:
        st.info("No results to display")
        return

    st.markdown("### 🎯 Tradeable Setups Found:")

    for result in results:
        ticker = result['ticker']
        price = result['price']
        gain_pct = result['gain_pct']
        quality = result['setup_quality']
        opts = result['options']

        # Create card
        st.markdown(f"""
        <div class="trade-card">
            <h2>{ticker} - {'⭐' * quality} ({quality}/5)</h2>
            <p style="font-size: 1.2rem;">
                <strong>Price:</strong> ${price:.2f} |
                <strong>Gain:</strong> +{gain_pct:.1f}%
            </p>
            <p style="font-size: 1.1rem;">
                <strong>📋 Best Option:</strong> ${opts['best_strike']} {opts['option_type']} exp {opts['expiration']}<br>
                <strong>💵 Premium:</strong> ${opts['ask']:.2f} |
                <strong>📊 Spread:</strong> {opts['spread_pct']:.1f}% |
                <strong>🔢 OI:</strong> {opts['open_interest']:,}
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📊 Details", key=f"details_{ticker}"):
                show_stock_details(result)
        with col2:
            if st.button(f"💰 Calculate", key=f"calc_{ticker}"):
                st.session_state.selected_ticker = result
                st.info(f"✅ {ticker} loaded! Go to Calculator tab →")


def show_stock_details(result):
    """Show detailed stock information"""
    st.markdown("### 📊 Stock Details")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Price", f"${result['price']:.2f}")
        st.metric("Gain", f"+{result['gain_pct']:.1f}%")
        st.metric("Float", f"{result['float']/1_000_000:.1f}M")

    with col2:
        st.metric("Rel Volume", f"{result['rel_volume']:.1f}x")
        st.metric("Volume", f"{result['volume']:,}")
        st.metric("Quality", f"{'⭐' * result['setup_quality']}")

    st.markdown("### 📋 Options Details")
    opts = result['options']

    st.markdown(f"""
    - **Strike:** ${opts['best_strike']} ({opts['option_type']})
    - **Expiration:** {opts['expiration']} ({opts['days_to_expiration']} days)
    - **Premium:** ${opts['ask']:.2f}
    - **Bid/Ask:** ${opts['bid']:.2f} / ${opts['ask']:.2f}
    - **Spread:** {opts['spread_pct']:.1f}%
    - **Open Interest:** {opts['open_interest']:,}
    - **Volume:** {opts['volume']:,}
    - **Delta:** ~{opts['delta']:.2f}
    """)

    # Technical Indicators
    if result.get('technical_analysis'):
        st.markdown("### 📈 Technical Indicators")

        technical = result['technical_analysis']

        # Trade Signal
        if technical.get('trade_signal'):
            signal = technical['trade_signal']
            st.markdown(f"""
            <div class="stat-card {'success-card' if 'BUY' in signal['signal'] else 'warning-card'}">
                <h3>{signal['emoji']} {signal['signal']} (Score: {signal['score']})</h3>
                <p><strong>Bullish Signals:</strong> {signal['bullish_count']} | <strong>Bearish Signals:</strong> {signal['bearish_count']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Show signals
            if signal.get('bullish_signals'):
                st.markdown("**✅ Bullish Signals:**")
                for s in signal['bullish_signals']:
                    st.markdown(f"- {s}")

            if signal.get('bearish_signals'):
                st.markdown("**❌ Bearish Signals:**")
                for s in signal['bearish_signals']:
                    st.markdown(f"- {s}")

        # Key Indicators
        col1, col2, col3 = st.columns(3)

        with col1:
            if technical.get('macd'):
                macd = technical['macd']
                st.metric("MACD",
                         "✅ Positive" if macd['is_positive'] else "❌ Negative",
                         f"Hist: {macd['histogram']:.3f}")

        with col2:
            if technical.get('rsi'):
                rsi = technical['rsi']
                st.metric("RSI",
                         f"{rsi['rsi']:.1f}",
                         rsi['signal'])

        with col3:
            if technical.get('moving_averages'):
                mas = technical['moving_averages']
                st.metric("Trend",
                         mas['trend'],
                         mas['trend_emoji'])

        # More details in expander
        with st.expander("📊 View All Indicators"):
            if technical.get('moving_averages'):
                mas = technical['moving_averages']
                st.markdown("**Moving Averages:**")
                col1, col2 = st.columns(2)
                with col1:
                    if mas.get('ema_9'):
                        st.markdown(f"- 9 EMA: ${mas['ema_9']:.2f} {'✅' if mas['above_ema_9'] else '❌'}")
                    if mas.get('ema_20'):
                        st.markdown(f"- 20 EMA: ${mas['ema_20']:.2f} {'✅' if mas['above_ema_20'] else '❌'}")
                with col2:
                    if mas.get('ema_50'):
                        st.markdown(f"- 50 EMA: ${mas['ema_50']:.2f} {'✅' if mas['above_ema_50'] else '❌'}")
                    if mas.get('ema_200'):
                        st.markdown(f"- 200 EMA: ${mas['ema_200']:.2f} {'✅' if mas['above_ema_200'] else '❌'}")

            if technical.get('atr'):
                atr = technical['atr']
                st.markdown("**Volatility (ATR):**")
                st.markdown(f"- ATR: ${atr['atr']:.2f} ({atr['atr_percent']:.1f}% of price)")
                st.markdown(f"- Volatility: {atr['volatility_level']}")
                st.markdown(f"- Suggested stop loss: ${atr['stop_loss_1_5x_atr']:.2f} (1.5x ATR)")

            if technical.get('bollinger_bands'):
                bb = technical['bollinger_bands']
                st.markdown("**Bollinger Bands:**")
                st.markdown(f"- Upper: ${bb['upper_band']:.2f}")
                st.markdown(f"- Middle: ${bb['middle_band']:.2f}")
                st.markdown(f"- Lower: ${bb['lower_band']:.2f}")
                st.markdown(f"- Position: {bb['emoji']} {bb['signal']}")

    # Candlestick Patterns
    if result.get('candlestick_patterns'):
        patterns = result['candlestick_patterns']

        if patterns.get('pattern_count', 0) > 0:
            st.markdown("### 🕯️ Candlestick Patterns")

            st.markdown(f"""
            <div class="stat-card {'success-card' if patterns['overall_signal'] == 'BULLISH' else 'danger-card' if patterns['overall_signal'] == 'BEARISH' else ''}">
                <h3>{patterns['signal_emoji']} {patterns['overall_signal']}</h3>
                <p>Found {patterns['pattern_count']} pattern(s) | Bullish: {patterns['bullish_patterns']} | Bearish: {patterns['bearish_patterns']}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Detected Patterns:**")
            for p in patterns['patterns_found']:
                pattern_color = "success-card" if p['type'] == 'BULLISH' else "danger-card" if p['type'] == 'BEARISH' else ""
                st.markdown(f"""
                <div class="stat-card {pattern_color}">
                    <h4>{p['emoji']} {p['name']}</h4>
                    <p>{p['description']}<br>
                    <strong>Type:</strong> {p['type']} | <strong>Strength:</strong> {p['strength']}</p>
                </div>
                """, unsafe_allow_html=True)


def calculator_page():
    """Position Calculator Page"""
    st.markdown("## 💰 Position Calculator")
    st.markdown("*Calculate contract quantity with Greeks analysis*")

    # Check if ticker selected from scanner
    if st.session_state.selected_ticker:
        result = st.session_state.selected_ticker
        st.success(f"✅ Analyzing: {result['ticker']}")

        # Auto-fill from scan results
        ticker = result['ticker']
        stock_price = result['price']
        strike = result['options']['best_strike']
        expiration = result['options']['expiration']
        premium = result['options']['ask']

        # Display auto-filled values
        st.markdown(f"""
        **Auto-filled from scanner:**
        - Ticker: {ticker}
        - Stock Price: ${stock_price:.2f}
        - Strike: ${strike}
        - Premium: ${premium:.2f}
        - Expiration: {expiration}
        """)

        if st.button("🔄 Clear Selection"):
            st.session_state.selected_ticker = None
            st.rerun()
    else:
        # Manual entry
        st.info("💡 Tip: Scan stocks first, then tap 'Calculate' for auto-fill!")

        ticker = st.text_input("Ticker:", placeholder="PTON", key="calc_ticker").upper()

        col1, col2 = st.columns(2)
        with col1:
            stock_price = st.number_input("Stock Price ($):", min_value=0.01, value=6.00, step=0.01, key="calc_stock_price")
            premium = st.number_input("Option Premium ($):", min_value=0.01, value=0.65, step=0.01, key="calc_premium")
        with col2:
            strike = st.number_input("Strike Price ($):", min_value=0.01, value=5.00, step=0.50, key="calc_strike")
            days_to_exp = st.number_input("Days to Expiration:", min_value=1, max_value=365, value=7, key="calc_days_to_exp")

        expiration = (datetime.now() + timedelta(days=days_to_exp)).strftime('%Y-%m-%d')

    # Calculate button
    if st.button("📊 CALCULATE POSITION", type="primary"):
        if ticker:
            with st.spinner("Calculating..."):
                calculate_position(ticker, stock_price, strike, premium, expiration, days_to_exp if 'days_to_exp' in locals() else 7)
        else:
            st.warning("⚠️ Please enter a ticker symbol")


def calculate_position(ticker, stock_price, strike, premium, expiration, days_to_exp):
    """Calculate and display position details"""
    try:
        # Initialize calculator
        calc = OptionsPositionCalculator(
            account_balance=st.session_state.account_balance,
            max_risk_percent=5.0
        )

        # Simple position sizing
        max_risk = st.session_state.account_balance * 0.05
        cost_per_contract = premium * 100
        contracts = int(max_risk / cost_per_contract)
        contracts = max(1, contracts)

        total_cost = premium * contracts * 100

        # Calculate Greeks (simplified)
        intrinsic = max(0, stock_price - strike)
        extrinsic = premium - intrinsic

        moneyness = stock_price / strike
        if moneyness >= 1.05:
            delta = min(0.95, 0.70 + (moneyness - 1.05) * 2)
        elif moneyness >= 0.95:
            delta = 0.50
        else:
            delta = 0.30 * moneyness

        theta = -extrinsic / days_to_exp if days_to_exp > 0 else -premium

        # Break-even
        break_even = strike + premium
        break_even_move = ((break_even / stock_price) - 1) * 100

        # Profit targets
        targets = []
        for move_pct in [10, 20, 30]:
            target_stock = stock_price * (1 + move_pct/100)
            target_intrinsic = max(0, target_stock - strike)
            days_passed = min(3, days_to_exp // 2)
            remaining_extrinsic = max(0, extrinsic - (abs(theta) * days_passed))
            target_premium = target_intrinsic + remaining_extrinsic

            profit = (target_premium - premium) * contracts * 100
            profit_pct = (target_premium / premium - 1) * 100
            account_growth = (profit / st.session_state.account_balance) * 100

            targets.append({
                'move': move_pct,
                'stock_price': target_stock,
                'premium': target_premium,
                'profit': profit,
                'profit_pct': profit_pct,
                'account_growth': account_growth
            })

        # Display results
        st.markdown("### ✅ RECOMMENDED POSITION")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Contracts", f"{contracts}")
        with col2:
            st.metric("Total Cost", f"${total_cost:.0f}")
        with col3:
            st.metric("% of Account", f"{(total_cost/st.session_state.account_balance*100):.1f}%")

        st.markdown("### 🔢 THE GREEKS")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Delta", f"{delta:.3f}", help="Option moves ${delta:.2f} per $1 stock move")
            st.metric("Intrinsic Value", f"${intrinsic:.2f}")
        with col2:
            st.metric("Theta", f"${theta:.2f}/day", help="You lose ${abs(theta):.2f} every day")
            st.metric("Extrinsic Value", f"${extrinsic:.2f}")

        st.markdown("### ⚖️ BREAK-EVEN")
        st.markdown(f"""
        <div class="stat-card warning-card">
            <h3>Stock must reach: ${break_even:.2f}</h3>
            <p>Stock must move: <strong>+{break_even_move:.1f}%</strong></p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 💵 PROFIT TARGETS")

        for target in targets:
            if target['account_growth'] >= 10:
                card_class = "success-card"
                emoji = "✅"
            elif target['account_growth'] >= 5:
                card_class = "stat-card"
                emoji = "📊"
            else:
                card_class = "warning-card"
                emoji = "⚠️"

            st.markdown(f"""
            <div class="stat-card {card_class}">
                <h4>{emoji} Stock +{target['move']}% → ${target['stock_price']:.2f}</h4>
                <p>
                    Option Premium: <strong>${target['premium']:.2f}</strong><br>
                    Profit: <strong>${target['profit']:.0f}</strong> (+{target['profit_pct']:.0f}% on options)<br>
                    Account Growth: <strong>+{target['account_growth']:.1f}%</strong>
                </p>
                {' <p style="color: #28a745; font-weight: bold;">🎯 HITS 10% ACCOUNT GOAL!</p>' if target['account_growth'] >= 10 else ''}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### ⚠️ MAX RISK")
        st.markdown(f"""
        <div class="stat-card danger-card">
            <h3>Maximum Loss: ${total_cost:.0f}</h3>
            <p>If option expires worthless (100% loss of premium)</p>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Calculation error: {str(e)}")


def journal_page():
    """Trade Journal Page"""
    st.markdown("## 📒 Trade Journal")
    st.markdown("*Log and track your options trades*")

    # Initialize journal
    journal = OptionsTradeJournal("streamlit_trades.json")

    # Tabs for Add vs View
    tab1, tab2 = st.tabs(["➕ Add Trade", "📊 View Trades"])

    with tab1:
        add_trade_form(journal)

    with tab2:
        view_trades(journal)


def add_trade_form(journal):
    """Form to add a new trade"""
    st.markdown("### ➕ Log New Trade")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input("Ticker:", placeholder="PTON", key="journal_ticker").upper()
        strike = st.number_input("Strike Price ($):", min_value=0.01, value=5.00, step=0.50, key="journal_strike")
        contracts = st.number_input("Contracts:", min_value=1, max_value=100, value=4, key="journal_contracts")

    with col2:
        expiration = st.date_input("Expiration:", value=datetime.now() + timedelta(days=7), key="journal_expiration")
        contract_type = st.selectbox("Type:", ["CALL", "PUT"], key="journal_contract_type")

    st.markdown("### 📊 Entry Details")
    col1, col2, col3 = st.columns(3)

    with col1:
        entry_premium = st.number_input("Entry Premium ($):", min_value=0.01, value=0.65, step=0.01, key="journal_entry_premium")
    with col2:
        entry_stock_price = st.number_input("Stock Price at Entry ($):", min_value=0.01, value=6.00, step=0.01, key="journal_entry_stock_price")
    with col3:
        entry_time = st.time_input("Entry Time:", value=datetime.now().time(), key="journal_entry_time")

    st.markdown("### 📊 Exit Details")
    col1, col2, col3 = st.columns(3)

    with col1:
        exit_premium = st.number_input("Exit Premium ($):", min_value=0.01, value=1.45, step=0.01, key="journal_exit_premium")
    with col2:
        exit_stock_price = st.number_input("Stock Price at Exit ($):", min_value=0.01, value=6.35, step=0.01, key="journal_exit_stock_price")
    with col3:
        exit_time = st.time_input("Exit Time:", value=datetime.now().time(), key="journal_exit_time")

    exit_reason = st.selectbox("Exit Reason:", [
        "TARGET_HIT",
        "STOP_LOSS",
        "TIME_LIMIT",
        "MACD_NEGATIVE"
    ], key="journal_exit_reason")

    st.markdown("### 📈 Strategy")
    col1, col2, col3 = st.columns(3)

    with col1:
        pattern = st.selectbox("Pattern:", ["Pullback", "Breakout", "Reversal", "Other"], key="journal_pattern")
    with col2:
        macd_positive = st.checkbox("MACD Positive?", value=True, key="journal_macd_positive")
    with col3:
        setup_quality = st.slider("Setup Quality:", 1, 5, 5, key="journal_setup_quality")

    notes = st.text_area("Notes (optional):", placeholder="What went well? What could improve?", key="journal_notes")

    if st.button("💾 SAVE TRADE", type="primary"):
        try:
            # Calculate days to expiration
            days_to_exp = (expiration - datetime.now().date()).days

            # Add trade
            journal.add_trade(
                ticker=ticker,
                strike=strike,
                expiration=str(expiration),
                contract_type=contract_type,
                entry_premium=entry_premium,
                entry_time=entry_time.strftime("%H:%M"),
                contracts=contracts,
                entry_stock_price=entry_stock_price,
                exit_premium=exit_premium,
                exit_time=exit_time.strftime("%H:%M"),
                exit_stock_price=exit_stock_price,
                exit_reason=exit_reason,
                pattern=pattern,
                macd_positive=macd_positive,
                setup_quality=setup_quality,
                days_to_expiration=days_to_exp,
                notes=notes
            )

            st.success("✅ Trade logged successfully!")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Error saving trade: {str(e)}")


def view_trades(journal):
    """View trade history and stats"""
    if not journal.trades:
        st.info("📭 No trades logged yet. Add your first trade above!")
        return

    # Summary stats
    stats = journal.get_summary_stats()

    st.markdown("### 📊 Performance Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Trades", stats['total_trades'])
    with col2:
        st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
    with col3:
        st.metric("Total P&L", f"${stats['total_pnl']:+,.0f}")
    with col4:
        st.metric("Avg P&L", f"${stats['avg_pnl']:+,.0f}")

    # Win rate gauge
    if stats['win_rate'] >= 75:
        st.success(f"✅ EXCELLENT! Win rate at {stats['win_rate']:.1f}% (Target: 75%)")
    elif stats['win_rate'] >= 60:
        st.warning(f"⚠️ GOOD! Win rate at {stats['win_rate']:.1f}% (Getting closer to 75%)")
    else:
        st.error(f"❌ NEEDS WORK! Win rate at {stats['win_rate']:.1f}% (Target: 75%)")

    # Recent trades
    st.markdown("### 📜 Recent Trades")

    df = journal.view_trades(limit=10)

    # Display as cards
    for _, trade in df.iterrows():
        result_emoji = "✅" if trade['result'] == 'WIN' else "❌"
        card_class = "success-card" if trade['result'] == 'WIN' else "danger-card"

        st.markdown(f"""
        <div class="stat-card {card_class}">
            <h4>{result_emoji} {trade['ticker']} ${trade['strike']} {trade['contract_type']}</h4>
            <p>
                {trade['contracts']} contracts @ ${trade['entry_premium']:.2f} → ${trade['exit_premium']:.2f}<br>
                P&L: <strong>${trade['net_pnl']:+,.0f}</strong> ({trade['return_pct']:+.1f}%)<br>
                Pattern: {trade['pattern']} | Quality: {'⭐' * trade['setup_quality']}<br>
                Date: {trade['date']}
            </p>
        </div>
        """, unsafe_allow_html=True)


def dashboard_page():
    """Performance Dashboard"""
    st.markdown("## 📊 Performance Dashboard")
    st.markdown("*Your trading metrics at a glance*")

    journal = OptionsTradeJournal("streamlit_trades.json")

    if not journal.trades:
        st.info("📭 No trading data yet. Start logging trades!")
        st.markdown("""
        ### 🚀 Quick Start:
        1. Go to **Scanner** tab → Find tradeable stocks
        2. Go to **Calculator** tab → Size your position
        3. Execute trade on Webull
        4. Go to **Journal** tab → Log the trade
        5. Come back here to see your stats!
        """)
        return

    stats = journal.get_summary_stats()

    # Key metrics
    st.markdown("### 🎯 Key Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Win Rate",
            f"{stats['win_rate']:.1f}%",
            delta=f"{stats['win_rate'] - 75:.1f}% vs target",
            delta_color="normal"
        )

    with col2:
        st.metric(
            "P/L Ratio",
            f"{stats['pl_ratio']:.2f}:1",
            delta=f"{stats['pl_ratio'] - 2:.2f} vs target",
            delta_color="normal"
        )

    with col3:
        st.metric(
            "Total P&L",
            f"${stats['total_pnl']:+,.0f}",
            delta=f"${stats['avg_pnl']:+,.0f} avg"
        )

    # Progress bars
    st.markdown("### 📈 Progress to Targets")

    # Win rate progress
    win_rate_progress = min(100, (stats['win_rate'] / 75) * 100)
    st.markdown(f"**Win Rate Progress:** {stats['win_rate']:.1f}% / 75% target")
    st.progress(win_rate_progress / 100)

    # P/L ratio progress
    pl_progress = min(100, (stats['pl_ratio'] / 2.0) * 100)
    st.markdown(f"**P/L Ratio Progress:** {stats['pl_ratio']:.2f}:1 / 2:1 target")
    st.progress(pl_progress / 100)

    # Trade analysis
    st.markdown("### 📊 Trade Analysis")

    # By option type
    type_analysis = journal.analyze_by_option_type()
    if not type_analysis.empty:
        st.markdown("**Performance by Option Type:**")
        st.dataframe(type_analysis, use_container_width=True)

    # By expiration
    exp_analysis = journal.analyze_by_days_to_expiration()
    if not exp_analysis.empty:
        st.markdown("**Performance by Days to Expiration:**")
        st.dataframe(exp_analysis, use_container_width=True)

    # Recommendations
    st.markdown("### 💡 Recommendations")

    if stats['win_rate'] >= 75:
        st.success("✅ **Win rate target achieved!** You're ready for automation!")
    else:
        st.warning(f"⚠️ **Focus on quality:** Trade only 5-star setups to boost win rate")

    if stats['pl_ratio'] >= 2.0:
        st.success("✅ **P/L ratio target achieved!** Your winners are 2x your losers!")
    else:
        st.info("💡 **Take profits faster:** Exit when profit target hits")

    if stats.get('avg_hold_time'):
        if stats['avg_hold_time'] <= 30:
            st.success(f"✅ **Good hold time:** {stats['avg_hold_time']:.1f} min average")
        else:
            st.warning(f"⚠️ **Hold time too long:** {stats['avg_hold_time']:.1f} min (target <30 min)")


# Run the app
if __name__ == "__main__":
    main()
