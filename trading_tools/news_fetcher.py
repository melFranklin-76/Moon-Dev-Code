#!/usr/bin/env python3
"""
NEWS FETCHER MODULE
Fetch recent news for stocks to validate catalyst (Pillar 5)

Uses yfinance for free news data
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')


class NewsFetcher:
    """Fetch and analyze stock news"""

    def __init__(self, ticker: str):
        """
        Initialize news fetcher

        Args:
            ticker: Stock symbol
        """
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)

    def get_recent_news(self, max_items: int = 5) -> List[Dict]:
        """
        Get recent news headlines for the ticker

        Args:
            max_items: Maximum number of news items to return

        Returns:
            List of news items with title, publisher, link, published date
        """
        try:
            news = self.stock.news

            if not news:
                return []

            # Parse news items
            news_items = []
            for item in news[:max_items]:
                try:
                    # Extract data
                    title = item.get('title', 'No title')
                    publisher = item.get('publisher', 'Unknown')
                    link = item.get('link', '')

                    # Parse timestamp
                    timestamp = item.get('providerPublishTime')
                    if timestamp:
                        pub_date = datetime.fromtimestamp(timestamp)
                        time_ago = self._time_ago(pub_date)
                    else:
                        time_ago = 'Unknown'

                    news_items.append({
                        'title': title,
                        'publisher': publisher,
                        'link': link,
                        'time_ago': time_ago,
                        'timestamp': timestamp
                    })

                except Exception as e:
                    continue

            return news_items

        except Exception as e:
            print(f"Error fetching news for {self.ticker}: {e}")
            return []

    def has_recent_catalyst(self, hours: int = 24) -> Dict:
        """
        Check if there's been recent news (catalyst)

        Args:
            hours: Look for news within this many hours

        Returns:
            dict with catalyst status and details
        """
        try:
            news = self.get_recent_news(max_items=10)

            if not news:
                return {
                    'has_catalyst': False,
                    'catalyst_type': 'NONE',
                    'news_count': 0,
                    'latest_news': None
                }

            # Check for recent news (within specified hours)
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_news = []

            for item in news:
                if item['timestamp']:
                    news_time = datetime.fromtimestamp(item['timestamp'])
                    if news_time >= cutoff_time:
                        recent_news.append(item)

            # Analyze catalyst type from headlines
            catalyst_keywords = {
                'EARNINGS': ['earnings', 'eps', 'revenue', 'profit', 'loss', 'quarter', 'q1', 'q2', 'q3', 'q4'],
                'FDA': ['fda', 'approval', 'drug', 'clinical', 'trial', 'phase'],
                'UPGRADE': ['upgrade', 'raised', 'price target', 'bullish', 'buy rating'],
                'DOWNGRADE': ['downgrade', 'lowered', 'bearish', 'sell rating'],
                'MERGER': ['merger', 'acquisition', 'buyout', 'takeover'],
                'PARTNERSHIP': ['partnership', 'deal', 'agreement', 'contract'],
                'LAWSUIT': ['lawsuit', 'legal', 'court', 'sue'],
                'PRODUCT': ['launch', 'product', 'release', 'unveil'],
                'BANKRUPTCY': ['bankruptcy', 'chapter 11', 'liquidation']
            }

            detected_catalysts = []
            for item in recent_news[:3]:  # Check top 3 recent news
                title_lower = item['title'].lower()
                for catalyst_type, keywords in catalyst_keywords.items():
                    if any(keyword in title_lower for keyword in keywords):
                        detected_catalysts.append(catalyst_type)
                        break

            # Determine overall catalyst status
            if recent_news:
                has_catalyst = True
                if detected_catalysts:
                    catalyst_type = detected_catalysts[0]  # Use first detected
                else:
                    catalyst_type = 'NEWS'  # Generic news
            else:
                has_catalyst = False
                catalyst_type = 'NONE'

            return {
                'has_catalyst': has_catalyst,
                'catalyst_type': catalyst_type,
                'news_count': len(recent_news),
                'latest_news': recent_news[0] if recent_news else None,
                'all_recent_news': recent_news
            }

        except Exception as e:
            print(f"Error checking catalyst for {self.ticker}: {e}")
            return {
                'has_catalyst': False,
                'catalyst_type': 'ERROR',
                'news_count': 0,
                'latest_news': None
            }

    def _time_ago(self, pub_date: datetime) -> str:
        """Convert datetime to human-readable time ago"""
        now = datetime.now()
        diff = now - pub_date

        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            else:
                return f"{diff.days} days ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            if hours == 1:
                return "1 hour ago"
            else:
                return f"{hours} hours ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            if minutes == 1:
                return "1 minute ago"
            else:
                return f"{minutes} minutes ago"
        else:
            return "Just now"


def quick_news_check(ticker: str, hours: int = 24) -> Dict:
    """
    Quick function to check for recent news catalyst

    Args:
        ticker: Stock symbol
        hours: Look for news within this many hours

    Returns:
        dict with catalyst info
    """
    fetcher = NewsFetcher(ticker)
    return fetcher.has_recent_catalyst(hours=hours)


def get_ticker_news(ticker: str, max_items: int = 5) -> List[Dict]:
    """
    Quick function to get recent news

    Args:
        ticker: Stock symbol
        max_items: Maximum number of news items

    Returns:
        List of news items
    """
    fetcher = NewsFetcher(ticker)
    return fetcher.get_recent_news(max_items=max_items)


if __name__ == "__main__":
    # Test with example ticker
    print("Testing News Fetcher Module...")
    print("=" * 60)

    ticker = "PTON"
    print(f"\n📰 Fetching news for {ticker}...\n")

    fetcher = NewsFetcher(ticker)

    # Get recent news
    news = fetcher.get_recent_news(max_items=5)

    if news:
        print(f"Found {len(news)} recent news items:\n")
        for i, item in enumerate(news, 1):
            print(f"{i}. {item['title']}")
            print(f"   Publisher: {item['publisher']}")
            print(f"   Time: {item['time_ago']}\n")
    else:
        print("No news found")

    # Check for catalyst
    catalyst = fetcher.has_recent_catalyst(hours=24)

    print("\n📊 Catalyst Check (24 hours):")
    print(f"Has Catalyst: {catalyst['has_catalyst']}")
    print(f"Catalyst Type: {catalyst['catalyst_type']}")
    print(f"News Count: {catalyst['news_count']}")

    if catalyst['latest_news']:
        print(f"\nLatest: {catalyst['latest_news']['title']}")
        print(f"        ({catalyst['latest_news']['time_ago']})")

    print("\n" + "=" * 60)
    print("✅ News Fetcher Module Working!")
