import requests
from datetime import datetime, timedelta
import json
from collections import defaultdict

class MarketSentimentAnalyzer:
    def __init__(self, api_key):
        """
        Initialize the sentiment analyzer
        api_key: NewsAPI key (get free at https://newsapi.org/)
        """
        self.api_key = api_key
        self.news_api_url = "https://newsapi.org/v2/everything"
        
    def fetch_news(self, ticker, company_name, days_back=1):
        """Fetch news articles for a specific ticker"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Try searching with just the ticker first, then company name
        search_terms = [ticker, company_name]
        all_articles = []
        
        for term in search_terms:
            params = {
                'q': term,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': self.api_key,
                'pageSize': 10
            }
            
            try:
                response = requests.get(self.news_api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'ok':
                    articles = data.get('articles', [])
                    all_articles.extend(articles)
                else:
                    print(f"API response for {term}: {data.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Error fetching news for {term}: {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles[:20]  # Limit to 20 articles
    
    def simple_sentiment_score(self, text):
        """
        Simple rule-based sentiment scoring
        Returns: score between -1 (very negative) and +1 (very positive)
        """
        if not text:
            return 0
        
        text = text.lower()
        
        # Positive words common in financial news
        positive_words = [
            'surge', 'soar', 'gain', 'profit', 'growth', 'bullish', 'rally',
            'beat', 'exceed', 'strong', 'positive', 'upgrade', 'outperform',
            'record', 'high', 'breakthrough', 'innovation', 'success', 'rise',
            'jump', 'boost', 'momentum', 'optimistic', 'milestone', 'expansion'
        ]
        
        # Negative words common in financial news
        negative_words = [
            'plunge', 'fall', 'drop', 'loss', 'decline', 'bearish', 'crash',
            'miss', 'weak', 'negative', 'downgrade', 'underperform', 'concern',
            'low', 'risk', 'warning', 'struggle', 'disappointing', 'cut',
            'slump', 'trouble', 'pressure', 'pessimistic', 'setback', 'layoff'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        total = pos_count + neg_count
        if total == 0:
            return 0
        
        score = (pos_count - neg_count) / total
        return score
    
    def analyze_ticker(self, ticker, company_name):
        """Analyze sentiment for a single ticker"""
        articles = self.fetch_news(ticker, company_name)
        
        if not articles:
            return {
                'ticker': ticker,
                'company': company_name,
                'sentiment_score': 0,
                'article_count': 0,
                'articles': []
            }
        
        article_sentiments = []
        analyzed_articles = []
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            text = f"{title} {description}"
            
            score = self.simple_sentiment_score(text)
            article_sentiments.append(score)
            
            analyzed_articles.append({
                'title': title,
                'source': article.get('source', {}).get('name', 'Unknown'),
                'url': article.get('url', ''),
                'sentiment': score,
                'published_at': article.get('publishedAt', '')
            })
        
        # Calculate overall sentiment
        avg_sentiment = sum(article_sentiments) / len(article_sentiments) if article_sentiments else 0
        
        # Categorize articles
        positive = sum(1 for s in article_sentiments if s > 0.2)
        neutral = sum(1 for s in article_sentiments if -0.2 <= s <= 0.2)
        negative = sum(1 for s in article_sentiments if s < -0.2)
        
        return {
            'ticker': ticker,
            'company': company_name,
            'sentiment_score': round(avg_sentiment, 3),
            'article_count': len(articles),
            'positive_articles': positive,
            'neutral_articles': neutral,
            'negative_articles': negative,
            'articles': sorted(analyzed_articles, key=lambda x: abs(x['sentiment']), reverse=True)[:5]
        }
    
    def generate_report(self, tickers):
        """
        Generate sentiment report for multiple tickers
        tickers: dict of {ticker: company_name}
        """
        results = []
        
        print("🔍 Analyzing market sentiment...\n")
        
        for ticker, company_name in tickers.items():
            print(f"Fetching news for {ticker}...")
            result = self.analyze_ticker(ticker, company_name)
            results.append(result)
        
        # Sort by sentiment score
        results.sort(key=lambda x: x['sentiment_score'], reverse=True)
        
        # Generate report
        report = self._format_report(results)
        return report, results
    
    def _format_report(self, results):
        """Format the analysis into a readable report"""
        report = []
        report.append("=" * 60)
        report.append(f"📊 MARKET SENTIMENT BRIEF - {datetime.now().strftime('%B %d, %Y')}")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("📈 SENTIMENT OVERVIEW")
        report.append("-" * 60)
        for result in results:
            sentiment = result['sentiment_score']
            ticker = result['ticker']
            company = result['company']
            count = result['article_count']
            
            # Emoji based on sentiment
            if sentiment > 0.3:
                emoji = "🟢"
                label = "Bullish"
            elif sentiment > 0:
                emoji = "🔵"
                label = "Slightly Bullish"
            elif sentiment > -0.3:
                emoji = "🟡"
                label = "Neutral/Mixed"
            else:
                emoji = "🔴"
                label = "Bearish"
            
            report.append(f"{emoji} {ticker} ({company})")
            report.append(f"   Sentiment: {sentiment:+.3f} ({label})")
            report.append(f"   Articles: {count} ({result['positive_articles']}+ / {result['neutral_articles']}= / {result['negative_articles']}-)")
            report.append("")
        
        # Detailed insights
        report.append("")
        report.append("📰 TOP HEADLINES BY TICKER")
        report.append("=" * 60)
        
        for result in results:
            report.append(f"\n{result['ticker']} - {result['company']}")
            report.append("-" * 60)
            
            if result['articles']:
                for i, article in enumerate(result['articles'][:3], 1):
                    sentiment_icon = "📈" if article['sentiment'] > 0 else "📉" if article['sentiment'] < 0 else "➡️"
                    report.append(f"{i}. {sentiment_icon} {article['title']}")
                    report.append(f"   Source: {article['source']} | Sentiment: {article['sentiment']:+.3f}")
                    report.append(f"   {article['url'][:80]}...")
                    report.append("")
            else:
                report.append("   No recent news found")
                report.append("")
        
        return "\n".join(report)


# Example usage

if __name__ == "__main__":
    from config import NEWSAPI_KEY, TICKERS
    
    # Create analyzer
    analyzer = MarketSentimentAnalyzer(NEWSAPI_KEY)
    
    # Generate report
    print("Starting analysis...")
    report, data = analyzer.generate_report(TICKERS)
    
    # Print report
    print(report)
    
    # Optional: Save to file
    with open(f'sentiment_report_{datetime.now().strftime("%Y%m%d")}.txt', 'w') as f:
        f.write(report)
    
    # Optional: Save raw data as JSON
    with open(f'sentiment_data_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n✅ Report saved to file!")



