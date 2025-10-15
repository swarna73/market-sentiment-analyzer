import requests
from financial_metrics import FinancialMetricsAnalyzer
from datetime import datetime, timedelta
import json
from collections import defaultdict

class MarketSentimentAnalyzer:
    def __init__(self, api_key, alphavantage_key=None):
        """
        Initialize the sentiment analyzer
        api_key: NewsAPI key (get free at https://newsapi.org/)
        alphavantage_key: Alpha Vantage API key for financial metrics
        """
        self.api_key = api_key
        self.alphavantage_key = alphavantage_key
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
    def analyze_ticker_with_fundamentals(self, ticker, company_name):
        """Enhanced analysis including both sentiment and fundamentals"""
        from financial_metrics import FinancialMetricsAnalyzer
        
        # Get sentiment from news
        sentiment_data = self.analyze_ticker(ticker, company_name)
        
        # Get financial metrics
        metrics_analyzer = FinancialMetricsAnalyzer(api_key=self.alphavantage_key)
        fundamentals = metrics_analyzer.get_stock_fundamentals(ticker)
        
        if fundamentals['success']:
            metrics = fundamentals['metrics']
            valuation = metrics_analyzer.analyze_valuation(metrics)
            
            # Combine both analyses
            combined_analysis = {
                **sentiment_data,
                'financial_metrics': {
                    'current_price': metrics.get('current_price'),
                    'price_change_pct': metrics.get('price_change_pct'),
                    'market_cap': metrics_analyzer.format_number(metrics.get('market_cap')),
                    'pe_ratio': metrics_analyzer.format_ratio(metrics.get('pe_ratio')),
                    'forward_pe': metrics_analyzer.format_ratio(metrics.get('forward_pe')),
                    'eps': metrics_analyzer.format_ratio(metrics.get('eps')),
                    'dividend_yield': metrics_analyzer.format_percentage(metrics.get('dividend_yield')),
                    'debt_to_equity': metrics_analyzer.format_ratio(metrics.get('debt_to_equity')),
                    'profit_margin': metrics_analyzer.format_percentage(metrics.get('profit_margin')),
                    'revenue_growth': metrics_analyzer.format_percentage(metrics.get('quarterly_revenue_growth')),
                    'beta': metrics_analyzer.format_ratio(metrics.get('beta')),
                },
                'valuation_analysis': valuation,
                'combined_signal': self._generate_combined_signal(
                    sentiment_data['sentiment_score'], 
                    valuation
                )
            }
            
            return combined_analysis
        
        return sentiment_data
    
    def _generate_combined_signal(self, sentiment_score, valuation):
        """Generate investment signal combining sentiment and valuation"""
        
        signals = []
        
        # Sentiment interpretation
        if sentiment_score > 0.3:
            sentiment_label = "Bullish"
        elif sentiment_score < -0.3:
            sentiment_label = "Bearish"
        else:
            sentiment_label = "Neutral"
        
        # Valuation interpretation
        valuation_label = valuation['overall']
        
        # Combined signal
        if sentiment_label == "Bullish" and valuation_label == "Attractive":
            signal = "🟢 STRONG BUY SIGNAL"
            signals.append("Positive sentiment + Attractive valuation")
        elif sentiment_label == "Bullish" and valuation_label == "Concerns":
            signal = "🟡 CAUTION"
            signals.append("Positive sentiment but valuation concerns")
        elif sentiment_label == "Bearish" and valuation_label == "Attractive":
            signal = "🟡 CONTRARIAN OPPORTUNITY"
            signals.append("Negative sentiment but attractive valuation - possible value play")
        elif sentiment_label == "Bearish" and valuation_label == "Concerns":
            signal = "🔴 AVOID"
            signals.append("Negative sentiment + Valuation concerns")
        else:
            signal = "⚪ NEUTRAL"
            signals.append("Mixed signals - further research needed")
        
        return {
            'signal': signal,
            'sentiment': sentiment_label,
            'valuation': valuation_label,
            'reasoning': signals
        }
    def _format_enhanced_report(self, results):
        """Format report with financial metrics included"""
        report = []
        report.append("=" * 80)
        report.append(f"📊 ENHANCED MARKET ANALYSIS - {datetime.now().strftime('%B %d, %Y')}")
        report.append("=" * 80)
        report.append("")
        
        # Sort by combined signal strength
        results.sort(key=lambda x: x.get('sentiment_score', 0), reverse=True)
        
        for result in results:
            report.append("")
            report.append("=" * 80)
            report.append(f"{result['ticker']} - {result['company']}")
            report.append("=" * 80)
            
            # Combined Signal
            combined = result.get('combined_signal', {})
            report.append(f"\n{combined.get('signal', 'N/A')}")
            report.append(f"Sentiment: {combined.get('sentiment', 'N/A')} | Valuation: {combined.get('valuation', 'N/A')}")
            
            # News Sentiment
            report.append(f"\n📰 NEWS SENTIMENT")
            report.append(f"Score: {result['sentiment_score']:+.3f}")
            report.append(f"Articles: {result['article_count']} ({result['positive_articles']}+ / {result['neutral_articles']}= / {result['negative_articles']}-)")
            
            # Financial Metrics
            metrics = result.get('financial_metrics', {})
            if metrics:
                report.append(f"\n💰 FINANCIAL METRICS")
                
                price = metrics.get('current_price')
                price_change = metrics.get('price_change_pct')
                if price and price_change:
                    arrow = "📈" if price_change > 0 else "📉"
                    report.append(f"Price: ${price:.2f} {arrow} {price_change:+.2f}%")
                
                report.append(f"Market Cap: {metrics.get('market_cap', 'N/A')}")
                report.append(f"P/E Ratio: {metrics.get('pe_ratio', 'N/A')} | Forward P/E: {metrics.get('forward_pe', 'N/A')}")
                report.append(f"EPS: {metrics.get('eps', 'N/A')} | Dividend Yield: {metrics.get('dividend_yield', 'N/A')}")
                report.append(f"Profit Margin: {metrics.get('profit_margin', 'N/A')} | Revenue Growth: {metrics.get('revenue_growth', 'N/A')}")
                report.append(f"Debt/Equity: {metrics.get('debt_to_equity', 'N/A')} | Beta: {metrics.get('beta', 'N/A')}")
            
            # Valuation Analysis
            valuation = result.get('valuation_analysis', {})
            if valuation:
                report.append(f"\n📊 VALUATION ANALYSIS")
                
                if valuation.get('strengths'):
                    report.append("Strengths:")
                    for strength in valuation['strengths']:
                        report.append(f"  ✓ {strength}")
                
                if valuation.get('concerns'):
                    report.append("Concerns:")
                    for concern in valuation['concerns']:
                        report.append(f"  ⚠ {concern}")
            
            # Top Headlines
            if result.get('articles'):
                report.append(f"\n📰 TOP HEADLINES")
                for i, article in enumerate(result['articles'][:3], 1):
                    sentiment_icon = "📈" if article['sentiment'] > 0 else "📉" if article['sentiment'] < 0 else "➡️"
                    report.append(f"{i}. {sentiment_icon} {article['title']}")
                    report.append(f"   {article['source']} | Sentiment: {article['sentiment']:+.3f}")
        
        report.append("")
        report.append("=" * 80)
        report.append("💡 DISCLAIMER: This is automated analysis for informational purposes only.")
        report.append("   Not financial advice. Always do your own research before investing.")
        report.append("=" * 80)
        
        return "\n".join(report)

    def generate_report(self, tickers):
        """Generate enhanced report with fundamentals"""
        results = []
    
        print("🔍 Analyzing market sentiment and fundamentals...\n")
    
        for ticker, company_name in tickers.items():
            print(f"Fetching data for {ticker}...")
            # Use the enhanced method instead
            result = self.analyze_ticker_with_fundamentals(ticker, company_name)
            results.append(result)
    
        # Use enhanced report formatting
        report = self._format_enhanced_report(results)
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
    from config import NEWSAPI_KEY, TICKERS, ALPHAVANTAGE_KEY
    
    # Create analyzer
    analyzer = MarketSentimentAnalyzer(NEWSAPI_KEY, ALPHAVANTAGE_KEY)
    
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



