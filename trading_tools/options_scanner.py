#!/usr/bin/env python3
"""
OPTIONS SCANNER - Professional Grade
Find stocks that pass Ross Cameron's 5 Pillars + have liquid options

Features:
- Scans stocks for Ross Cameron's 5-pillar criteria
- Validates options liquidity (volume, open interest, bid/ask spread)
- Identifies best strikes to trade (ITM/ATM with high delta)
- Checks weekly expiration availability
- Recommends contract sizing
- Ranks setups by quality
- Real-time or watchlist scanning

This scanner answers:
1. WHAT stocks to trade (5 pillars)
2. Which OPTIONS are liquid enough (spread, OI, volume)
3. Which STRIKES to buy (ITM/ATM recommendations)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Import technical analysis modules
try:
    from technical_indicators import TechnicalIndicators
    from candlestick_patterns import CandlestickPatternRecognizer
    TECHNICAL_ANALYSIS_AVAILABLE = True
except ImportError:
    TECHNICAL_ANALYSIS_AVAILABLE = False
    print("⚠️  Technical analysis modules not available")

# Import news fetcher
try:
    from news_fetcher import NewsFetcher
    NEWS_FETCHER_AVAILABLE = True
except ImportError:
    NEWS_FETCHER_AVAILABLE = False
    print("⚠️  News fetcher module not available")


class OptionsScanner:
    def __init__(self,
                 # 5-Pillar criteria
                 min_price: float = 2.0,
                 max_price: float = 20.0,
                 max_float: float = 20_000_000,
                 min_rel_volume: float = 5.0,
                 min_gain_percent: float = 10.0,

                 # Options liquidity criteria
                 min_open_interest: int = 100,
                 max_spread_percent: float = 10.0,
                 min_option_volume: int = 50):
        """
        Initialize Options Scanner

        Args:
            # Stock criteria (Ross Cameron's 5 Pillars)
            min_price: Minimum stock price
            max_price: Maximum stock price
            max_float: Maximum float (shares outstanding)
            min_rel_volume: Minimum relative volume
            min_gain_percent: Minimum % gain

            # Options liquidity criteria
            min_open_interest: Minimum open interest for liquid options
            max_spread_percent: Maximum bid/ask spread %
            min_option_volume: Minimum option volume
        """
        # Stock filters
        self.min_price = min_price
        self.max_price = max_price
        self.max_float = max_float
        self.min_rel_volume = min_rel_volume
        self.min_gain_percent = min_gain_percent

        # Options filters
        self.min_open_interest = min_open_interest
        self.max_spread_percent = max_spread_percent
        self.min_option_volume = min_option_volume

        print(f"\n{'='*80}")
        print(f"🔍 OPTIONS SCANNER - Ross Cameron 5-Pillar + Options Liquidity")
        print(f"{'='*80}")
        print(f"\n📊 STOCK FILTERS:")
        print(f"   Price Range: ${self.min_price} - ${self.max_price}")
        print(f"   Max Float: {self.max_float/1_000_000:.1f}M shares")
        print(f"   Min Rel Volume: {self.min_rel_volume}x")
        print(f"   Min Gain: {self.min_gain_percent}%")
        print(f"\n📋 OPTIONS FILTERS:")
        print(f"   Min Open Interest: {self.min_open_interest}")
        print(f"   Max Spread: {self.max_spread_percent}%")
        print(f"   Min Option Volume: {self.min_option_volume}")
        print(f"\n{'='*80}\n")

    def check_stock_criteria(self, ticker: str) -> Dict:
        """
        Check if stock passes 5-pillar criteria

        Args:
            ticker: Stock symbol

        Returns:
            Dictionary with results
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Get current price
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if not price:
                return {'passes': False, 'reason': 'No price data'}

            # Get float (shares outstanding)
            float_shares = info.get('floatShares') or info.get('sharesOutstanding')
            if not float_shares:
                float_shares = info.get('sharesOutstanding', 0)

            # Get volume data
            volume = info.get('volume') or info.get('regularMarketVolume', 0)
            avg_volume = info.get('averageVolume') or info.get('averageVolume10days', 1)

            # Calculate relative volume
            rel_volume = volume / avg_volume if avg_volume > 0 else 0

            # Get % change
            prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose', price)
            gain_pct = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0

            # Check each pillar
            results = {
                'ticker': ticker,
                'price': price,
                'float': float_shares,
                'volume': volume,
                'avg_volume': avg_volume,
                'rel_volume': rel_volume,
                'gain_pct': gain_pct,
            }

            # Pillar checks
            pillar_1 = self.min_price <= price <= self.max_price
            pillar_2 = float_shares <= self.max_float
            pillar_3 = rel_volume >= self.min_rel_volume
            pillar_4 = gain_pct >= self.min_gain_percent

            results['pillar_1_price'] = pillar_1
            results['pillar_2_float'] = pillar_2
            results['pillar_3_volume'] = pillar_3
            results['pillar_4_gain'] = pillar_4

            # All pillars must pass (except news - manual check)
            results['passes'] = pillar_1 and pillar_2 and pillar_3 and pillar_4

            if not results['passes']:
                failed = []
                if not pillar_1:
                    failed.append(f"Price ${price:.2f}")
                if not pillar_2:
                    failed.append(f"Float {float_shares/1_000_000:.1f}M")
                if not pillar_3:
                    failed.append(f"RelVol {rel_volume:.1f}x")
                if not pillar_4:
                    failed.append(f"Gain {gain_pct:.1f}%")
                results['reason'] = "Failed: " + ", ".join(failed)

            return results

        except Exception as e:
            return {'passes': False, 'reason': f'Error: {str(e)}'}

    def check_options_liquidity(self, ticker: str, stock_price: float) -> Optional[Dict]:
        """
        Check if stock has liquid options to trade

        Args:
            ticker: Stock symbol
            stock_price: Current stock price

        Returns:
            Dict with options analysis or None if no good options
        """
        try:
            stock = yf.Ticker(ticker)

            # Get available expirations
            expirations = stock.options

            if not expirations:
                return None

            # Find nearest weekly expiration (within 7 days)
            today = datetime.now()
            weekly_exp = None

            for exp in expirations:
                exp_dt = datetime.strptime(exp, '%Y-%m-%d')
                days_away = (exp_dt - today).days

                if 0 <= days_away <= 7:
                    weekly_exp = exp
                    break

            if not weekly_exp:
                # Use first available if no weekly
                weekly_exp = expirations[0]

            # Get option chain
            chain = stock.option_chain(weekly_exp)
            calls = chain.calls

            if calls.empty:
                return None

            # Find best strikes: ATM and slightly ITM
            # ATM = strike near stock price
            # ITM = strike below stock price

            # Find ATM option
            atm_strike = calls.iloc[(calls['strike'] - stock_price).abs().argsort()[:1]]

            if atm_strike.empty:
                return None

            atm = atm_strike.iloc[0]

            # Find ITM option (2-5% in the money)
            target_itm_strike = stock_price * 0.97  # 3% ITM
            itm_candidates = calls[calls['strike'] < stock_price]

            if not itm_candidates.empty:
                itm_strike = itm_candidates.iloc[(itm_candidates['strike'] - target_itm_strike).abs().argsort()[:1]]
                itm = itm_strike.iloc[0]
            else:
                itm = None

            # Analyze best option (prefer ITM if available and liquid)
            if itm is not None and itm['openInterest'] >= self.min_open_interest:
                best = itm
                option_type = 'ITM'
            else:
                best = atm
                option_type = 'ATM'

            # Calculate spread
            spread = best['ask'] - best['bid']
            spread_pct = (spread / best['ask'] * 100) if best['ask'] > 0 else 100

            # Check liquidity criteria
            liquid_oi = best['openInterest'] >= self.min_open_interest
            liquid_spread = spread_pct <= self.max_spread_percent
            liquid_volume = best['volume'] >= self.min_option_volume if best['volume'] > 0 else False

            # Calculate days to expiration
            exp_dt = datetime.strptime(weekly_exp, '%Y-%m-%d')
            days_to_exp = (exp_dt - today).days

            analysis = {
                'expiration': weekly_exp,
                'days_to_expiration': days_to_exp,
                'best_strike': best['strike'],
                'option_type': option_type,
                'bid': best['bid'],
                'ask': best['ask'],
                'last': best['lastPrice'],
                'spread': spread,
                'spread_pct': spread_pct,
                'volume': best['volume'],
                'open_interest': best['openInterest'],
                'implied_volatility': best['impliedVolatility'],

                # Liquidity checks
                'liquid_oi': liquid_oi,
                'liquid_spread': liquid_spread,
                'liquid_volume': liquid_volume,
                'is_liquid': liquid_oi and liquid_spread,

                # Delta approximation
                'delta': 0.7 if option_type == 'ITM' else 0.5
            }

            return analysis

        except Exception as e:
            print(f"   ⚠️  Options error for {ticker}: {str(e)}")
            return None

    def get_technical_analysis(self, ticker: str) -> Optional[Dict]:
        """
        Get technical indicators analysis

        Args:
            ticker: Stock symbol

        Returns:
            Dict with all technical indicators or None
        """
        if not TECHNICAL_ANALYSIS_AVAILABLE:
            return None

        try:
            analyzer = TechnicalIndicators(ticker, period="3mo", interval="1d")
            indicators = analyzer.get_all_indicators()

            if not indicators:
                return None

            trade_signal = analyzer.get_trade_signal()
            indicators['trade_signal'] = trade_signal

            return indicators

        except Exception as e:
            print(f"   ⚠️  Technical analysis error for {ticker}: {str(e)}")
            return None

    def get_candlestick_patterns(self, ticker: str) -> Optional[Dict]:
        """
        Get candlestick pattern analysis

        Args:
            ticker: Stock symbol

        Returns:
            Dict with identified patterns or None
        """
        if not TECHNICAL_ANALYSIS_AVAILABLE:
            return None

        try:
            recognizer = CandlestickPatternRecognizer(ticker, period="1mo", interval="1d")
            patterns = recognizer.scan_all_patterns()

            return patterns

        except Exception as e:
            print(f"   ⚠️  Pattern recognition error for {ticker}: {str(e)}")
            return None

    def get_news_catalyst(self, ticker: str) -> Optional[Dict]:
        """
        Check for recent news catalyst (Pillar 5)

        Args:
            ticker: Stock symbol

        Returns:
            Dict with news and catalyst info or None
        """
        if not NEWS_FETCHER_AVAILABLE:
            return None

        try:
            fetcher = NewsFetcher(ticker)

            # Get recent news (last 24 hours)
            catalyst = fetcher.has_recent_catalyst(hours=24)

            # Get top 3 news items regardless of timing
            recent_news = fetcher.get_recent_news(max_items=3)

            return {
                'has_catalyst': catalyst['has_catalyst'],
                'catalyst_type': catalyst['catalyst_type'],
                'news_count': catalyst['news_count'],
                'recent_headlines': recent_news
            }

        except Exception as e:
            print(f"   ⚠️  News fetch error for {ticker}: {str(e)}")
            return None

    def scan_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Complete scan of a single ticker

        Args:
            ticker: Stock symbol

        Returns:
            Complete analysis or None if doesn't pass
        """
        print(f"\n🔍 Scanning {ticker}...")

        # Check stock criteria (5 pillars)
        stock_check = self.check_stock_criteria(ticker)

        if not stock_check['passes']:
            print(f"   ❌ Failed stock criteria: {stock_check.get('reason', 'Unknown')}")
            return None

        print(f"   ✅ Passes 5 pillars!")
        print(f"      Price: ${stock_check['price']:.2f}")
        print(f"      Float: {stock_check['float']/1_000_000:.1f}M")
        print(f"      Rel Vol: {stock_check['rel_volume']:.1f}x")
        print(f"      Gain: {stock_check['gain_pct']:.1f}%")

        # Check options liquidity
        options_check = self.check_options_liquidity(ticker, stock_check['price'])

        if not options_check:
            print(f"   ❌ No liquid options available")
            return None

        if not options_check['is_liquid']:
            reasons = []
            if not options_check['liquid_oi']:
                reasons.append(f"Low OI ({options_check['open_interest']})")
            if not options_check['liquid_spread']:
                reasons.append(f"Wide spread ({options_check['spread_pct']:.1f}%)")

            print(f"   ❌ Options not liquid: {', '.join(reasons)}")
            return None

        print(f"   ✅ Liquid options available!")
        print(f"      Strike: ${options_check['best_strike']} ({options_check['option_type']})")
        print(f"      Premium: ${options_check['ask']:.2f}")
        print(f"      Spread: {options_check['spread_pct']:.1f}%")
        print(f"      OI: {options_check['open_interest']:,}")
        print(f"      Exp: {options_check['expiration']} ({options_check['days_to_expiration']} days)")

        # Get technical analysis
        print(f"\n   📊 Running technical analysis...")
        technical = self.get_technical_analysis(ticker)

        if technical and technical.get('trade_signal'):
            signal = technical['trade_signal']
            print(f"   {signal['emoji']} Trade Signal: {signal['signal']} (Score: {signal['score']})")

            # Show key indicators
            if technical.get('macd'):
                macd = technical['macd']
                print(f"      MACD: {'✅ Positive' if macd['is_positive'] else '❌ Negative'}")

            if technical.get('rsi'):
                rsi = technical['rsi']
                print(f"      RSI: {rsi['rsi']} {rsi['color']} ({rsi['signal']})")

            if technical.get('moving_averages'):
                mas = technical['moving_averages']
                print(f"      Trend: {mas['trend_emoji']} {mas['trend']}")

        # Get candlestick patterns
        print(f"\n   🕯️  Scanning candlestick patterns...")
        patterns = self.get_candlestick_patterns(ticker)

        if patterns and patterns.get('pattern_count', 0) > 0:
            print(f"   {patterns['signal_emoji']} Found {patterns['pattern_count']} pattern(s) - {patterns['overall_signal']}")
            for p in patterns['patterns_found'][:3]:  # Show top 3
                print(f"      {p['emoji']} {p['name']}: {p['description']}")
        else:
            print(f"   ➡️ No significant patterns")

        # Get news catalyst (Pillar 5)
        print(f"\n   📰 Checking for news catalyst...")
        news = self.get_news_catalyst(ticker)

        if news:
            if news['has_catalyst']:
                print(f"   ✅ CATALYST DETECTED: {news['catalyst_type']}")
                if news['recent_headlines']:
                    print(f"      Latest: {news['recent_headlines'][0]['title']}")
                    print(f"      ({news['recent_headlines'][0]['time_ago']})")
            else:
                print(f"   ℹ️  No recent catalyst (last 24h)")
                if news['recent_headlines']:
                    print(f"      Recent news: {news['recent_headlines'][0]['title']}")

        # Calculate setup quality (1-5 stars)
        quality_score = 0

        # Stock quality
        if stock_check['rel_volume'] >= 10:
            quality_score += 1
        if stock_check['float'] <= 10_000_000:  # Under 10M float
            quality_score += 1
        if stock_check['gain_pct'] >= 20:  # 20%+ gainer
            quality_score += 1

        # Options quality
        if options_check['spread_pct'] < 5:  # Tight spread
            quality_score += 1
        if options_check['open_interest'] > 500:  # High liquidity
            quality_score += 1

        # Technical analysis bonus points
        if technical and technical.get('trade_signal'):
            signal = technical['trade_signal']
            if signal['signal'] in ['BUY', 'STRONG_BUY']:
                quality_score += 2  # Bonus for bullish signals
            if technical.get('macd', {}).get('is_positive'):
                quality_score += 1  # Bonus for MACD positive

        # Candlestick pattern bonus
        if patterns and patterns.get('overall_signal') == 'BULLISH':
            quality_score += 1

        # News catalyst bonus (Pillar 5 validation)
        if news and news['has_catalyst']:
            quality_score += 1

        setup_quality = min(5, max(1, quality_score))

        # Combine results
        result = {
            **stock_check,
            'options': options_check,
            'technical_analysis': technical,
            'candlestick_patterns': patterns,
            'news_catalyst': news,
            'setup_quality': setup_quality
        }

        print(f"\n   ⭐ Overall Setup Quality: {setup_quality}/5 stars")

        return result

    def scan_watchlist(self, tickers: List[str]) -> pd.DataFrame:
        """
        Scan multiple tickers

        Args:
            tickers: List of stock symbols

        Returns:
            DataFrame of qualifying stocks
        """
        print(f"\n{'='*80}")
        print(f"🚀 SCANNING {len(tickers)} TICKERS FOR OPTIONS TRADING")
        print(f"{'='*80}")

        results = []

        for ticker in tickers:
            result = self.scan_ticker(ticker)

            if result:
                results.append({
                    'Ticker': ticker,
                    'Price': f"${result['price']:.2f}",
                    'Gain': f"{result['gain_pct']:.1f}%",
                    'Float': f"{result['float']/1_000_000:.1f}M",
                    'RelVol': f"{result['rel_volume']:.1f}x",
                    'Strike': f"${result['options']['best_strike']}",
                    'Type': result['options']['option_type'],
                    'Premium': f"${result['options']['ask']:.2f}",
                    'Spread': f"{result['options']['spread_pct']:.1f}%",
                    'OI': f"{result['options']['open_interest']:,}",
                    'Exp': result['options']['expiration'],
                    'Quality': f"{'⭐' * result['setup_quality']} ({result['setup_quality']}/5)"
                })

        if not results:
            print(f"\n❌ No stocks found matching all criteria")
            print(f"\n💡 TIP: Try scanning top gainers from Webull or Finviz")
            return pd.DataFrame()

        df = pd.DataFrame(results)

        print(f"\n{'='*80}")
        print(f"✅ FOUND {len(df)} TRADEABLE SETUPS!")
        print(f"{'='*80}\n")

        print(df.to_string(index=False))

        print(f"\n{'='*80}")
        print(f"💡 NEXT STEPS:")
        print(f"{'='*80}")
        print(f"1. Check news catalyst for each stock (Pillar 5)")
        print(f"2. Wait for pullback pattern on 5-min chart")
        print(f"3. Verify MACD positive")
        print(f"4. Use options_position_calculator.py to size position")
        print(f"5. Execute trade on Webull")
        print(f"\n{'='*80}\n")

        return df


def main():
    """Example usage"""
    print("\n🚀 ROSS CAMERON OPTIONS SCANNER")
    print("Find stocks with 5-pillar setups + liquid options\n")

    # Initialize scanner
    scanner = OptionsScanner(
        # Stock criteria
        min_price=2.0,
        max_price=20.0,
        max_float=20_000_000,
        min_rel_volume=5.0,
        min_gain_percent=10.0,

        # Options criteria
        min_open_interest=100,
        max_spread_percent=10.0,
        min_option_volume=50
    )

    # Example watchlist
    # In real use, get this from Webull Gainers list
    print("📋 Enter tickers to scan (comma-separated)")
    print("   Or press Enter for demo with: PTON, AMD, NVDA, SAVA")

    user_input = input("\nTickers: ").strip()

    if user_input:
        watchlist = [t.strip().upper() for t in user_input.split(',')]
    else:
        watchlist = ['PTON', 'AMD', 'NVDA', 'SAVA', 'TSLA']
        print(f"\n📊 Demo Mode: Scanning {', '.join(watchlist)}")

    # Scan watchlist
    results = scanner.scan_watchlist(watchlist)


if __name__ == "__main__":
    main()
