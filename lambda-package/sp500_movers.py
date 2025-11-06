"""
S&P 500 Top Gainers and Losers Module
Fetches real-time data and generates signals based on daily performance
"""
import requests
from datetime import datetime
import json

class SP500MoversAnalyzer:
    def __init__(self, alphavantage_key):
        """
        Initialize with Alpha Vantage API key
        """
        self.api_key = alphavantage_key
        self.base_url = "https://www.alphavantage.co/query"
        
        # S&P 500 tickers (top 100 most liquid for faster processing)
        # You can expand this list or use a full S&P 500 list
        self.sp500_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'LLY', 'AVGO',
            'JPM', 'V', 'UNH', 'XOM', 'WMT', 'MA', 'PG', 'JNJ', 'HD', 'COST',
            'ABBV', 'MRK', 'CVX', 'ORCL', 'KO', 'NFLX', 'PEP', 'BAC', 'AMD', 'CRM',
            'ADBE', 'TMO', 'MCD', 'CSCO', 'ACN', 'LIN', 'ABT', 'WFC', 'DHR', 'INTC',
            'VZ', 'DIS', 'PM', 'TXN', 'CMCSA', 'NEE', 'INTU', 'NKE', 'COP', 'IBM',
            'QCOM', 'RTX', 'UNP', 'AMGN', 'HON', 'UPS', 'LOW', 'SPGI', 'CAT', 'BA',
            'GE', 'AMAT', 'ELV', 'DE', 'T', 'BLK', 'AXP', 'SBUX', 'PLD', 'GILD',
            'MS', 'ADI', 'BKNG', 'ISRG', 'MDT', 'VRTX', 'C', 'GS', 'MMC', 'TJX',
            'ADP', 'CVS', 'SYK', 'LRCX', 'REGN', 'NOW', 'ZTS', 'SCHW', 'AMT', 'PGR',
            'MO', 'ETN', 'BX', 'BMY', 'CI', 'SO', 'TMUS', 'CB', 'BSX', 'DUK'
        ]
    
    def get_batch_quotes(self, tickers_batch):
        """
        Fetch quotes for a batch of tickers
        Note: Alpha Vantage free tier has rate limits (5 calls/min, 500 calls/day)
        """
        quotes = []
        
        for ticker in tickers_batch:
            try:
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': ticker,
                    'apikey': self.api_key
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    
                    price = self._safe_float(quote.get('05. price'))
                    change_pct = self._safe_float(quote.get('10. change percent', '').replace('%', ''))
                    volume = self._safe_float(quote.get('06. volume'))
                    
                    if price and change_pct is not None:
                        quotes.append({
                            'ticker': ticker,
                            'price': price,
                            'change_pct': change_pct,
                            'volume': volume,
                            'latest_trading_day': quote.get('07. latest trading day')
                        })
                
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue
        
        return quotes
    
    def get_all_movers(self, limit=100):
        """
        Get price data for S&P 500 stocks
        limit: number of stocks to fetch (default 100 due to API limits)
        """
        print(f"Fetching data for {limit} S&P 500 stocks...")
        print("This may take a few minutes due to API rate limits...")
        
        tickers_to_fetch = self.sp500_tickers[:limit]
        all_quotes = self.get_batch_quotes(tickers_to_fetch)
        
        return all_quotes
    
    def get_top_gainers_losers(self, limit=100, top_n=10):
        """
        Get top gainers and losers from S&P 500
        """
        quotes = self.get_all_movers(limit)
        
        if not quotes:
            return {'gainers': [], 'losers': []}
        
        # Sort by change percentage
        sorted_quotes = sorted(quotes, key=lambda x: x['change_pct'], reverse=True)
        
        # Get top gainers and losers
        gainers = sorted_quotes[:top_n]
        losers = sorted_quotes[-top_n:]
        losers.reverse()  # Show worst performers first
        
        # Generate signals for each
        for stock in gainers:
            stock['signal'] = self._generate_signal(stock['change_pct'], 'gainer')
            stock['sentiment'] = self._infer_sentiment(stock['change_pct'])
        
        for stock in losers:
            stock['signal'] = self._generate_signal(stock['change_pct'], 'loser')
            stock['sentiment'] = self._infer_sentiment(stock['change_pct'])
        
        return {
            'gainers': gainers,
            'losers': losers,
            'total_analyzed': len(quotes),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_signal(self, change_pct, mover_type):
        """
        Generate trading signal based on daily performance
        
        Logic:
        - Large moves (>5%) may indicate overextension or strong momentum
        - Consider mean reversion vs momentum continuation
        """
        if mover_type == 'gainer':
            if change_pct > 10:
                return "🟡 OVERBOUGHT"  # May be due for pullback
            elif change_pct > 5:
                return "🟢 STRONG BUY"  # Strong momentum
            elif change_pct > 3:
                return "🟢 BUY"  # Good momentum
            elif change_pct > 1.5:
                return "🟢 WEAK BUY"  # Modest gains
            else:
                return "⚪ NEUTRAL"
        
        else:  # loser
            if change_pct < -10:
                return "🟡 OVERSOLD"  # May be due for bounce
            elif change_pct < -5:
                return "🔴 STRONG SELL"  # Strong downward momentum
            elif change_pct < -3:
                return "🔴 SELL"  # Negative momentum
            elif change_pct < -1.5:
                return "🔴 WEAK SELL"  # Modest losses
            else:
                return "⚪ NEUTRAL"
    
    def _infer_sentiment(self, change_pct):
        """
        Infer sentiment from price movement
        """
        if change_pct > 3:
            return "Very Bullish"
        elif change_pct > 1:
            return "Bullish"
        elif change_pct > 0:
            return "Slightly Bullish"
        elif change_pct > -1:
            return "Slightly Bearish"
        elif change_pct > -3:
            return "Bearish"
        else:
            return "Very Bearish"
    
    def _safe_float(self, value):
        """Safely convert string to float"""
        if value is None or value == 'None' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def format_percentage(self, num):
        """Format percentage with + or - sign"""
        if num is None:
            return 'N/A'
        sign = '+' if num >= 0 else ''
        return f"{sign}{num:.2f}%"
    
    def format_volume(self, volume):
        """Format volume to readable format"""
        if volume is None:
            return 'N/A'
        
        if volume >= 1_000_000_000:
            return f"{volume/1_000_000_000:.2f}B"
        elif volume >= 1_000_000:
            return f"{volume/1_000_000:.2f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.2f}K"
        else:
            return f"{volume:,.0f}"
    
    def generate_html_table(self, movers_data, table_type='gainers'):
        """
        Generate HTML table for displaying gainers or losers
        """
        stocks = movers_data[table_type]
        
        if not stocks:
            return "<p>No data available</p>"
        
        title = "🚀 Top Gainers" if table_type == 'gainers' else "📉 Top Losers"
        
        html = f"""
        <div class="movers-section">
            <h2>{title}</h2>
            <table class="movers-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Ticker</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>Volume</th>
                        <th>Signal</th>
                        <th>Sentiment</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for idx, stock in enumerate(stocks, 1):
            change_class = 'positive' if stock['change_pct'] > 0 else 'negative'
            
            html += f"""
                    <tr>
                        <td>{idx}</td>
                        <td class="ticker">{stock['ticker']}</td>
                        <td>${stock['price']:.2f}</td>
                        <td class="{change_class}">{self.format_percentage(stock['change_pct'])}</td>
                        <td>{self.format_volume(stock['volume'])}</td>
                        <td class="signal">{stock['signal']}</td>
                        <td>{stock['sentiment']}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def generate_report(self, limit=100, top_n=10):
        """
        Generate complete report with both gainers and losers
        """
        print(f"\n{'='*60}")
        print(f"S&P 500 TOP MOVERS ANALYSIS")
        print(f"{'='*60}\n")
        
        movers_data = self.get_top_gainers_losers(limit, top_n)
        
        print(f"\n📊 Analysis complete!")
        print(f"Total stocks analyzed: {movers_data['total_analyzed']}")
        print(f"Timestamp: {movers_data['timestamp']}\n")
        
        # Print Top Gainers
        print(f"\n{'='*60}")
        print("🚀 TOP {top_n} GAINERS")
        print(f"{'='*60}")
        print(f"{'Rank':<6}{'Ticker':<8}{'Price':<12}{'Change':<12}{'Signal':<20}{'Sentiment':<15}")
        print("-" * 80)
        
        for idx, stock in enumerate(movers_data['gainers'], 1):
            print(f"{idx:<6}{stock['ticker']:<8}${stock['price']:<11.2f}"
                  f"{self.format_percentage(stock['change_pct']):<12}"
                  f"{stock['signal']:<20}{stock['sentiment']:<15}")
        
        # Print Top Losers
        print(f"\n{'='*60}")
        print(f"📉 TOP {top_n} LOSERS")
        print(f"{'='*60}")
        print(f"{'Rank':<6}{'Ticker':<8}{'Price':<12}{'Change':<12}{'Signal':<20}{'Sentiment':<15}")
        print("-" * 80)
        
        for idx, stock in enumerate(movers_data['losers'], 1):
            print(f"{idx:<6}{stock['ticker']:<8}${stock['price']:<11.2f}"
                  f"{self.format_percentage(stock['change_pct']):<12}"
                  f"{stock['signal']:<20}{stock['sentiment']:<15}")
        
        return movers_data


# Example usage
if __name__ == "__main__":
    # Replace with your Alpha Vantage API key
    API_KEY = "YOUR_ALPHAVANTAGE_API_KEY"
    
    analyzer = SP500MoversAnalyzer(API_KEY)
    
    # Get top 10 gainers and losers (from top 100 S&P 500 stocks)
    movers_data = analyzer.generate_report(limit=100, top_n=10)
    
    # Generate HTML tables
    gainers_html = analyzer.generate_html_table(movers_data, 'gainers')
    losers_html = analyzer.generate_html_table(movers_data, 'losers')
    
    # Save to file
    with open('movers_report.html', 'w') as f:
        f.write(gainers_html + losers_html)
    
    print("\n✅ Report generated successfully!")
