"""
PRODUCTION-READY S&P 500 Movers Analyzer
Uses web scraping for faster results (no API rate limits)

This scrapes from Yahoo Finance or similar sources to get real-time movers data
Much faster than making 100+ API calls!
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

class FastSP500Movers:
    """
    Fast S&P 500 movers analyzer using web scraping
    Gets top gainers/losers in seconds instead of minutes
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_yahoo_movers(self, top_n=10):
        """
        Scrape Yahoo Finance for market movers
        This is much faster than API calls!
        """
        try:
            # Yahoo Finance has pre-computed gainers and losers
            gainers_url = "https://finance.yahoo.com/gainers"
            losers_url = "https://finance.yahoo.com/losers"
            
            gainers = self._scrape_yahoo_table(gainers_url, top_n)
            losers = self._scrape_yahoo_table(losers_url, top_n)
            
            # Add signals
            for stock in gainers:
                stock['signal'] = self._generate_signal(stock['change_pct'], 'gainer')
                stock['sentiment'] = self._infer_sentiment(stock['change_pct'])
            
            for stock in losers:
                stock['signal'] = self._generate_signal(stock['change_pct'], 'loser')
                stock['sentiment'] = self._infer_sentiment(stock['change_pct'])
            
            return {
                'gainers': gainers,
                'losers': losers,
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }
            
        except Exception as e:
            print(f"Error fetching Yahoo movers: {e}")
            return {'gainers': [], 'losers': [], 'error': str(e)}
    
    def _scrape_yahoo_table(self, url, limit=10):
        """
        Scrape Yahoo Finance table for gainers or losers
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Yahoo uses a table structure
            table = soup.find('table')
            if not table:
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header
            stocks = []
            
            for row in rows[:limit]:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 3:
                        continue
                    
                    # Extract data
                    ticker = cols[0].text.strip()
                    name = cols[1].text.strip() if len(cols) > 1 else ''
                    price = self._safe_float(cols[2].text.strip().replace(',', ''))
                    change = self._safe_float(cols[3].text.strip().replace(',', ''))
                    change_pct = self._safe_float(cols[4].text.strip().replace('%', ''))
                    volume = cols[5].text.strip() if len(cols) > 5 else 'N/A'
                    market_cap = cols[6].text.strip() if len(cols) > 6 else 'N/A'
                    
                    stocks.append({
                        'ticker': ticker,
                        'name': name,
                        'price': price,
                        'change': change,
                        'change_pct': change_pct,
                        'volume': volume,
                        'market_cap': market_cap
                    })
                    
                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
            
            return stocks
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []
    
    def get_finviz_movers(self, top_n=10):
        """
        Alternative: Scrape Finviz for S&P 500 movers
        Finviz has clean, easy-to-parse tables
        """
        try:
            # Finviz screener for S&P 500 sorted by performance
            gainers_url = "https://finviz.com/screener.ashx?v=111&f=idx_sp500&o=-change"
            losers_url = "https://finviz.com/screener.ashx?v=111&f=idx_sp500&o=change"
            
            gainers = self._scrape_finviz_table(gainers_url, top_n)
            losers = self._scrape_finviz_table(losers_url, top_n)
            
            # Add signals
            for stock in gainers:
                stock['signal'] = self._generate_signal(stock['change_pct'], 'gainer')
                stock['sentiment'] = self._infer_sentiment(stock['change_pct'])
            
            for stock in losers:
                stock['signal'] = self._generate_signal(stock['change_pct'], 'loser')
                stock['sentiment'] = self._infer_sentiment(stock['change_pct'])
            
            return {
                'gainers': gainers,
                'losers': losers,
                'timestamp': datetime.now().isoformat(),
                'source': 'Finviz'
            }
            
        except Exception as e:
            print(f"Error fetching Finviz movers: {e}")
            return {'gainers': [], 'losers': [], 'error': str(e)}
    
    def _scrape_finviz_table(self, url, limit=10):
        """
        Scrape Finviz screener table
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Finviz uses a specific table structure
            table = soup.find('table', {'class': 'table-light'})
            if not table:
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header
            stocks = []
            
            for row in rows[:limit]:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 12:
                        continue
                    
                    ticker = cols[1].text.strip()
                    name = cols[2].text.strip()
                    price = self._safe_float(cols[8].text.strip())
                    change_pct = self._safe_float(cols[9].text.strip().replace('%', ''))
                    volume = cols[10].text.strip()
                    
                    stocks.append({
                        'ticker': ticker,
                        'name': name,
                        'price': price,
                        'change_pct': change_pct,
                        'volume': volume
                    })
                    
                except Exception as e:
                    print(f"Error parsing Finviz row: {e}")
                    continue
            
            return stocks
            
        except Exception as e:
            print(f"Error scraping Finviz: {e}")
            return []
    
    def _generate_signal(self, change_pct, mover_type):
        """Generate trading signal based on daily performance"""
        if mover_type == 'gainer':
            if change_pct > 10:
                return "🟡 OVERBOUGHT"
            elif change_pct > 5:
                return "🟢 STRONG BUY"
            elif change_pct > 3:
                return "🟢 BUY"
            elif change_pct > 1.5:
                return "🟢 WEAK BUY"
            else:
                return "⚪ NEUTRAL"
        else:  # loser
            if change_pct < -10:
                return "🟡 OVERSOLD"
            elif change_pct < -5:
                return "🔴 STRONG SELL"
            elif change_pct < -3:
                return "🔴 SELL"
            elif change_pct < -1.5:
                return "🔴 WEAK SELL"
            else:
                return "⚪ NEUTRAL"
    
    def _infer_sentiment(self, change_pct):
        """Infer sentiment from price movement"""
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
        if not value or value == 'N/A':
            return None
        try:
            # Remove any non-numeric characters except . and -
            cleaned = ''.join(c for c in value if c.isdigit() or c in '.-')
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def format_percentage(self, num):
        """Format percentage with + or - sign"""
        if num is None:
            return 'N/A'
        sign = '+' if num >= 0 else ''
        return f"{sign}{num:.2f}%"
    
    def generate_json(self, movers_data):
        """
        Generate JSON output for API response
        """
        return json.dumps(movers_data, indent=2)
    
    def print_report(self, movers_data):
        """
        Print formatted console report
        """
        print(f"\n{'='*70}")
        print(f"S&P 500 TOP MOVERS - {movers_data.get('source', 'Unknown')}")
        print(f"Last Updated: {movers_data.get('timestamp', 'N/A')}")
        print(f"{'='*70}\n")
        
        # Print gainers
        print("🚀 TOP GAINERS")
        print("-" * 70)
        print(f"{'#':<4}{'Ticker':<8}{'Price':<12}{'Change':<12}{'Signal':<20}")
        print("-" * 70)
        
        for idx, stock in enumerate(movers_data.get('gainers', []), 1):
            print(f"{idx:<4}{stock['ticker']:<8}${stock['price']:<11.2f}"
                  f"{self.format_percentage(stock['change_pct']):<12}"
                  f"{stock['signal']:<20}")
        
        # Print losers
        print(f"\n📉 TOP LOSERS")
        print("-" * 70)
        print(f"{'#':<4}{'Ticker':<8}{'Price':<12}{'Change':<12}{'Signal':<20}")
        print("-" * 70)
        
        for idx, stock in enumerate(movers_data.get('losers', []), 1):
            print(f"{idx:<4}{stock['ticker']:<8}${stock['price']:<11.2f}"
                  f"{self.format_percentage(stock['change_pct']):<12}"
                  f"{stock['signal']:<20}")
        
        print(f"\n{'='*70}\n")


# Lambda handler example
def lambda_handler(event, context):
    """
    AWS Lambda handler for serving movers data
    """
    analyzer = FastSP500Movers()
    
    # Try Yahoo first, fallback to Finviz
    movers_data = analyzer.get_yahoo_movers(top_n=10)
    
    if not movers_data.get('gainers') or not movers_data.get('losers'):
        print("Yahoo failed, trying Finviz...")
        movers_data = analyzer.get_finviz_movers(top_n=10)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(movers_data)
    }


# Example usage
if __name__ == "__main__":
    analyzer = FastSP500Movers()
    
    print("Fetching S&P 500 movers...")
    movers = analyzer.get_yahoo_movers(top_n=10)
    
    if not movers.get('gainers'):
        print("Trying alternative source...")
        movers = analyzer.get_finviz_movers(top_n=10)
    
    analyzer.print_report(movers)
    
    # Save to JSON file
    with open('movers_data.json', 'w') as f:
        f.write(analyzer.generate_json(movers))
    
    print("✅ Data saved to movers_data.json")
