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
import yfinance as yf

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


def fetch_live_market_data(ticker: str):
    """
    Fetch live market data for a ticker from yfinance

    Args:
        ticker: Stock symbol

    Returns:
        dict with stock price, best options strike, premium, etc.
    """
    try:
        stock = yf.Ticker(ticker)

        # Get current stock price
        try:
            info = stock.info
            stock_price = info.get('currentPrice') or info.get('regularMarketPrice')

            if not stock_price:
                # Try alternative method - get from history
                hist = stock.history(period="1d")
                if not hist.empty:
                    stock_price = float(hist['Close'].iloc[-1])
                else:
                    st.error(f"❌ Could not fetch current price for {ticker}")
                    return None
        except Exception as e:
            st.error(f"❌ Error fetching stock info: {str(e)}")
            return None

        # Get options chain
        try:
            expirations = stock.options

            if not expirations or len(expirations) == 0:
                st.error(f"❌ No options available for {ticker}")
                return None
        except Exception as e:
            st.error(f"❌ Error fetching options chain: {str(e)}")
            return None

        # Find nearest weekly expiration (within 7 days)
        today = datetime.now()
        weekly_exp = None

        try:
            for exp in expirations:
                exp_dt = datetime.strptime(exp, '%Y-%m-%d')
                days_away = (exp_dt - today).days

                if 0 <= days_away <= 7:
                    weekly_exp = exp
                    break

            if not weekly_exp:
                # Use first available if no weekly
                weekly_exp = expirations[0]
        except Exception as e:
            st.error(f"❌ Error parsing expiration dates: {str(e)}")
            return None

        # Get call options
        try:
            chain = stock.option_chain(weekly_exp)
            calls = chain.calls

            if calls.empty:
                st.error(f"❌ No call options found for {ticker}")
                return None
        except Exception as e:
            st.error(f"❌ Error fetching options data: {str(e)}")
            return None

        # Find ATM option (closest to stock price)
        try:
            atm_strike = calls.iloc[(calls['strike'] - stock_price).abs().argsort()[:1]]

            if atm_strike.empty:
                st.error(f"❌ Could not find suitable strike")
                return None

            atm = atm_strike.iloc[0]
        except Exception as e:
            st.error(f"❌ Error finding ATM strike: {str(e)}")
            return None

        # Find ITM option (3% in the money)
        try:
            target_itm_strike = stock_price * 0.97
            itm_candidates = calls[calls['strike'] < stock_price]

            if not itm_candidates.empty:
                itm_strike = itm_candidates.iloc[(itm_candidates['strike'] - target_itm_strike).abs().argsort()[:1]]
                itm = itm_strike.iloc[0]

                # Prefer ITM if it has good liquidity
                if itm['openInterest'] >= 100:
                    best = itm
                    option_type = 'ITM'
                else:
                    best = atm
                    option_type = 'ATM'
            else:
                best = atm
                option_type = 'ATM'
        except Exception as e:
            # Fallback to ATM if ITM search fails
            best = atm
            option_type = 'ATM'

        # Calculate spread
        try:
            spread = best['ask'] - best['bid']
            spread_pct = (spread / best['ask'] * 100) if best['ask'] > 0 else 100

            # Calculate days to expiration
            exp_dt = datetime.strptime(weekly_exp, '%Y-%m-%d')
            days_to_exp = (exp_dt - today).days

            # Ensure we have valid data
            if best['ask'] <= 0:
                st.error(f"❌ Invalid premium data (ask price is ${best['ask']:.2f})")
                return None

            return {
                'ticker': ticker,
                'stock_price': float(stock_price),
                'best_strike': float(best['strike']),
                'option_type': option_type,
                'premium': float(best['ask']),
                'bid': float(best['bid']),
                'ask': float(best['ask']),
                'spread_pct': float(spread_pct),
                'open_interest': int(best['openInterest']),
                'volume': int(best['volume']) if best['volume'] > 0 else 0,
                'expiration': weekly_exp,
                'days_to_exp': days_to_exp
            }

        except Exception as e:
            st.error(f"❌ Error calculating spread/premium: {str(e)}")
            return None

    except Exception as e:
        st.error(f"❌ Unexpected error fetching market data: {str(e)}")
        st.info("💡 Tip: Make sure the ticker symbol is valid and the market is open (or recently closed)")
        return None


def scanner_page():
    """Options Scanner Page"""
    st.markdown("## 🔍 Options Scanner")
    st.markdown("*Find stocks with 5-pillar setups + liquid options*")

    # Check if technical analysis is available
    try:
        from options_scanner import TECHNICAL_ANALYSIS_AVAILABLE
        if TECHNICAL_ANALYSIS_AVAILABLE:
            st.success("✅ Technical Analysis & Patterns: ACTIVE")
        else:
            st.warning("⚠️ Technical Analysis: Unavailable (using basic scan only)")
    except:
        st.warning("⚠️ Technical Analysis: Unavailable (using basic scan only)")

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
        help="Comma-separated ticker symbols",
        key="scanner_ticker_input"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 SCAN NOW", type="primary", key="scan_manual"):
            if tickers_input:
                with st.spinner("🔍 Scanning for tradeable options..."):
                    scan_stocks(tickers_input)
            else:
                st.warning("⚠️ Please enter at least one ticker")

    with col2:
        if st.button("🤖 Auto-Scan Market", type="secondary", key="auto_scan_market"):
            with st.spinner("🤖 Fetching top gainers from market..."):
                auto_scan_market()

    with col3:
        if st.button("📋 Demo Scan", key="demo_scan"):
            with st.spinner("🔍 Running demo scan..."):
                scan_stocks("PTON, AMD, NVDA, TSLA")

    # Display results
    if st.session_state.scan_results is not None:
        display_scan_results()


def get_market_gainers():
    """
    Fetch top gainers from market automatically

    Returns:
        list of ticker symbols
    """
    import time

    try:
        # Small cap & penny stocks under $50 with liquid options
        # Perfect for Ross Cameron's 5-pillar strategy and small accounts
        candidate_pool = [
            # Under $10 - High volatility day trading favorites
            "SNDL", "NOK", "F", "SOFI", "NIO", "LCID", "CLOV", "WISH",
            "PLUG", "FCEL", "TELL", "SENS", "VXRT", "OCGN", "GRAB",

            # $10-$20 - Popular retail/meme stocks
            "AMC", "PTON", "RIVN", "HOOD", "SNAP", "LYFT", "BABA",

            # $20-$50 - Mid-range movers with good options
            "PLTR", "DKNG", "GME", "COIN", "SAVA", "CLF", "AA",

            # Biotech/Pharma under $30 (volatile)
            "BBBY", "APE", "BBIG", "MULN", "GNUS",

            # Energy/Materials under $25
            "ET", "MRO", "VALE", "FCX", "SWN",

            # Recent IPOs/SPACs under $20
            "OPEN", "GOEV", "FSR", "QS", "BLNK",

            # Small cap tech under $30
            "FUBO", "NKLA", "RIDE", "WKHS", "SKLZ"
        ]

        # Check each stock for today's performance
        gainers = []
        checked = 0
        in_range = 0
        errors = 0

        # Show progress
        progress_placeholder = st.empty()

        # Reduce to 15 stocks to avoid rate limiting
        for ticker in candidate_pool[:15]:
            try:
                checked += 1
                progress_placeholder.text(f"Checking {ticker}... ({checked}/15)")

                # Add delay to avoid rate limiting (important!)
                time.sleep(0.5)  # 500ms delay between requests

                stock = yf.Ticker(ticker)

                # Try to get current price - use history as fallback
                try:
                    # Use longer period for better data availability
                    hist = stock.history(period="1mo")

                    if len(hist) >= 2:
                        current_price = float(hist['Close'].iloc[-1])
                        prev_close = float(hist['Close'].iloc[-2])
                    else:
                        errors += 1
                        continue
                except Exception as e:
                    errors += 1
                    continue

                if not current_price or not prev_close or current_price <= 0:
                    continue

                # Calculate gain
                gain_pct = ((current_price - prev_close) / prev_close) * 100

                # Focus on $2-$20 sweet spot, but allow up to $50
                if 2.0 <= current_price <= 50.0:
                    in_range += 1

                    # Lower threshold to 2% to find more opportunities
                    if gain_pct >= 2.0:
                        gainers.append({
                            'ticker': ticker,
                            'price': current_price,
                            'gain_pct': gain_pct
                        })

            except Exception as e:
                errors += 1
                continue

        progress_placeholder.empty()

        # Show debug info
        if errors > 5:
            st.warning(f"⚠️ Yahoo Finance API issues ({errors} errors). Results may be limited.")

        st.info(f"📊 Checked {checked} stocks | {in_range} in $2-$50 range | {len(gainers)} gaining 2%+ | {errors} errors")

        # Sort by gain % descending
        gainers.sort(key=lambda x: x['gain_pct'], reverse=True)

        # Return top 8 tickers (reduced from 10)
        return [g['ticker'] for g in gainers[:8]]

    except Exception as e:
        st.error(f"Error fetching market gainers: {e}")
        return []


def auto_scan_market():
    """Auto-scan market for top gainers"""
    try:
        st.info("🤖 Searching for today's top small cap gainers ($2-$50 range)...")

        # Get top gainers
        gainers = get_market_gainers()

        if not gainers:
            st.warning("⚠️ No strong gainers found in the small cap range today. Try manual entry or demo scan.")
            return

        st.success(f"✅ Found {len(gainers)} gainers! Scanning: {', '.join(gainers)}")

        # Scan them
        tickers_string = ', '.join(gainers)
        scan_stocks(tickers_string)

    except Exception as e:
        st.error(f"❌ Error in auto-scan: {str(e)}")


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
        progress_text = st.empty()

        for i, ticker in enumerate(tickers):
            progress_text.text(f"Scanning {ticker}... ({i+1}/{len(tickers)})")
            result = scanner.scan_ticker(ticker)
            if result:
                results.append(result)

        progress_text.empty()
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

        col1, col2 = st.columns([3, 1])
        with col1:
            ticker = st.text_input("Ticker:", placeholder="PTON", key="calc_ticker").upper()
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            fetch_data = st.button("📡 Fetch Market Data", type="secondary", key="fetch_market_data")

        # Initialize session state for fetched data
        if 'fetched_data' not in st.session_state:
            st.session_state.fetched_data = None

        # Fetch live market data
        if fetch_data and ticker:
            with st.spinner(f"📡 Fetching live data for {ticker}..."):
                market_data = fetch_live_market_data(ticker)
                if market_data:
                    st.session_state.fetched_data = market_data
                    st.success(f"✅ Live data loaded for {ticker}!")
                else:
                    st.error(f"❌ Could not fetch data for {ticker}")
                    st.session_state.fetched_data = None

        # Use fetched data if available, otherwise defaults
        if st.session_state.fetched_data:
            data = st.session_state.fetched_data
            default_price = data['stock_price']
            default_strike = data['best_strike']
            default_premium = data['premium']
            default_days = data['days_to_exp']

            # Show fetched data summary
            st.markdown(f"""
            <div class="stat-card success-card">
                <h4>📊 Live Market Data</h4>
                <p>
                    <strong>Stock:</strong> ${data['stock_price']:.2f} |
                    <strong>Best Strike:</strong> ${data['best_strike']} ({data['option_type']}) |
                    <strong>Premium:</strong> ${data['premium']:.2f}<br>
                    <strong>Spread:</strong> {data['spread_pct']:.1f}% |
                    <strong>OI:</strong> {data['open_interest']:,} |
                    <strong>Exp:</strong> {data['expiration']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            default_price = 6.00
            default_strike = 5.00
            default_premium = 0.65
            default_days = 7

        col1, col2 = st.columns(2)
        with col1:
            stock_price = st.number_input("Stock Price ($):", min_value=0.01, value=default_price, step=0.01, key="calc_stock_price")
            premium = st.number_input("Option Premium ($):", min_value=0.01, value=default_premium, step=0.01, key="calc_premium")
        with col2:
            strike = st.number_input("Strike Price ($):", min_value=0.01, value=default_strike, step=0.50, key="calc_strike")
            days_to_exp = st.number_input("Days to Expiration:", min_value=1, max_value=365, value=default_days, key="calc_days_to_exp")

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
