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
        
        # Get sentiment from news
        sentiment_data = self.analyze_ticker(ticker, company_name)
        
        # Get financial metrics with alphavantage_key
        metrics_analyzer = FinancialMetricsAnalyzer(self.alphavantage_key)
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
                    valuation,
                    metrics.get('price_change_pct', 0)
                )
            }
            
            return combined_analysis
        
        return sentiment_data
    
    def _generate_combined_signal(self, sentiment_score, valuation, price_change_pct=0):
        """
        Generate investment signal combining sentiment, valuation, and price momentum
        
        IMPROVED LOGIC:
        - Lower sentiment thresholds for more responsive signals
        - Include price momentum in the decision
        - More nuanced signal generation
        """
        
        signals = []
        
        # === 1. SENTIMENT INTERPRETATION ===
        # Lowered thresholds from ±0.3 to ±0.15 for better responsiveness
        if sentiment_score > 0.15:
            sentiment_label = "Bullish"
        elif sentiment_score < -0.15:
            sentiment_label = "Bearish"
        else:
            sentiment_label = "Neutral"
        
        # === 2. PRICE MOMENTUM INTERPRETATION ===
        # Consider recent price action as a strong signal
        if price_change_pct is not None:
            if price_change_pct > 2.0:
                momentum_label = "Strong Upward"
            elif price_change_pct > 0.5:
                momentum_label = "Upward"
            elif price_change_pct < -2.0:
                momentum_label = "Strong Downward"
            elif price_change_pct < -0.5:
                momentum_label = "Downward"
            else:
                momentum_label = "Flat"
        else:
            momentum_label = "Unknown"
        
        # === 3. VALUATION INTERPRETATION ===
        valuation_label = valuation['overall']
        
        # === 4. COMBINED SIGNAL GENERATION ===
        # Calculate a composite score
        score = 0
        
        # Sentiment contribution (weight: 30%)
        if sentiment_label == "Bullish":
            score += 30
        elif sentiment_label == "Bearish":
            score -= 30
        
        # Momentum contribution (weight: 40%) - Price action is important!
        if momentum_label == "Strong Upward":
            score += 40
        elif momentum_label == "Upward":
            score += 20
        elif momentum_label == "Strong Downward":
            score -= 40
        elif momentum_label == "Downward":
            score -= 20
        
        # Valuation contribution (weight: 30%)
        if valuation_label == "Attractive":
            score += 30
        elif valuation_label == "Concerns":
            score -= 30
        
        # Generate signal based on composite score
        if score >= 60:
            signal = "🟢 STRONG BUY"
            signals.append(f"High conviction: {sentiment_label} sentiment + {momentum_label} momentum + {valuation_label} valuation")
        elif score >= 30:
            signal = "🟢 BUY"
            signals.append(f"Positive signals: {sentiment_label} sentiment, {momentum_label} momentum, {valuation_label} valuation")
        elif score >= 10:
            signal = "🟡 WEAK BUY"
            signals.append(f"Modestly positive: Check {valuation_label} valuation and {momentum_label} momentum")
        elif score <= -60:
            signal = "🔴 STRONG SELL"
            signals.append(f"High risk: {sentiment_label} sentiment + {momentum_label} momentum + {valuation_label} valuation")
        elif score <= -30:
            signal = "🔴 SELL"
            signals.append(f"Negative signals: {sentiment_label} sentiment, {momentum_label} momentum, {valuation_label} valuation")
        elif score <= -10:
            signal = "🟡 WEAK SELL"
            signals.append(f"Modestly negative: Monitor {valuation_label} valuation and {momentum_label} momentum")
        else:
            signal = "⚪ NEUTRAL"
            signals.append(f"Mixed signals: {sentiment_label} sentiment, {momentum_label} momentum, {valuation_label} valuation")
        
        # Add specific reasoning based on combinations
        if sentiment_label == "Bullish" and momentum_label in ["Strong Upward", "Upward"] and valuation_label == "Attractive":
            signals.append("⭐ All indicators aligned - Strong opportunity")
        elif sentiment_label == "Bearish" and momentum_label in ["Strong Downward", "Downward"] and valuation_label == "Concerns":
            signals.append("⚠️ All indicators negative - High risk")
        elif sentiment_label == "Bullish" and valuation_label == "Concerns":
            signals.append("⚠️ Positive sentiment but overvalued - Exercise caution")
        elif sentiment_label == "Bearish" and valuation_label == "Attractive":
            signals.append("💎 Potential value opportunity despite negative sentiment")
        elif momentum_label in ["Strong Upward", "Upward"] and sentiment_label == "Neutral":
            signals.append("📈 Strong price momentum - Watch for sentiment shift")
        
        return {
            'signal': signal,
            'sentiment': sentiment_label,
            'momentum': momentum_label,
            'momentum_pct': round(price_change_pct, 2) if price_change_pct else None,
            'valuation': valuation_label,
            'composite_score': score,
            'reasoning': signals
        }
    
    def generate_report(self, tickers):
        """Generate enhanced report with fundamentals"""
        results = []
    
        print("🔍 Analyzing market sentiment and fundamentals...\n")
    
        for ticker, company_name in tickers.items():
            print(f"Fetching data for {ticker}...")
            # Use the enhanced method
            result = self.analyze_ticker_with_fundamentals(ticker, company_name)
            results.append(result)
    
        return "", results  # Return empty string for report, just results
