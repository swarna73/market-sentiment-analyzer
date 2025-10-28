"""
Dynamic Stock Picker Lambda Function
Runs daily at 10:30 PM CET to find top gainers/losers
"""
import json
import os
import boto3
from datetime import datetime, timedelta
import requests
from sentiment_analyzer import MarketSentimentAnalyzer

class DynamicStockPicker:
    def __init__(self, alphavantage_key):
        self.alphavantage_key = alphavantage_key
        self.s3_client = boto3.client('s3', region_name='eu-north-1')
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', 'putcall-dashboard-data')
        
    def get_sp500_gainers_losers(self, limit=5):
        """
        Get top gainers and losers from major stocks
        Using Alpha Vantage's TOP_GAINERS_LOSERS endpoint
        """
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'TOP_GAINERS_LOSERS',
            'apikey': self.alphavantage_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'top_gainers' in data and 'top_losers' in data:
                gainers = data['top_gainers'][:limit]
                losers = data['top_losers'][:limit]
                
                # Extract tickers and company names
                gainer_stocks = {}
                loser_stocks = {}
                
                for stock in gainers:
                    ticker = stock['ticker']
                    # Try to get company name from OVERVIEW API
                    company_name = self._get_company_name(ticker)
                    gainer_stocks[ticker] = company_name
                
                for stock in losers:
                    ticker = stock['ticker']
                    company_name = self._get_company_name(ticker)
                    loser_stocks[ticker] = company_name
                
                return {
                    'gainers': gainer_stocks,
                    'losers': loser_stocks,
                    'success': True
                }
            else:
                print(f"Unexpected API response: {data}")
                return self._get_fallback_stocks()
                
        except Exception as e:
            print(f"Error fetching gainers/losers: {e}")
            return self._get_fallback_stocks()
    
    def _get_company_name(self, ticker):
        """Get company name from Alpha Vantage OVERVIEW"""
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'OVERVIEW',
            'symbol': ticker,
            'apikey': self.alphavantage_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            return data.get('Name', ticker)
        except:
            return ticker
    
    def _get_fallback_stocks(self):
        """Fallback to popular tech/market stocks if API fails"""
        return {
            'gainers': {
                'NVDA': 'NVIDIA',
                'MSFT': 'Microsoft',
                'AAPL': 'Apple',
                'GOOGL': 'Google',
                'META': 'Meta'
            },
            'losers': {
                'TSLA': 'Tesla',
                'AMD': 'AMD',
                'INTC': 'Intel',
                'DIS': 'Disney',
                'NFLX': 'Netflix'
            },
            'success': False
        }
    
    def analyze_stocks(self, stocks):
        """Run sentiment analysis on selected stocks"""
        newsapi_key = os.environ.get('NEWSAPI_KEY')
        alphavantage_key = os.environ.get('ALPHAVANTAGE_KEY')
        
        analyzer = MarketSentimentAnalyzer(newsapi_key)
        results = []
        
        print(f"Analyzing {len(stocks)} stocks...")
        for ticker, company in stocks.items():
            print(f"Analyzing {ticker}...")
            try:
                result = analyzer.analyze_ticker_with_fundamentals(ticker, company)
                results.append(result)
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")
        
        return results
    
    def save_to_s3(self, data, filename='dashboard-data.json'):
        """Save analysis results to S3"""
        try:
            json_data = json.dumps(data, indent=2)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=json_data,
                ContentType='application/json',
                CacheControl='max-age=300',  # Cache for 5 minutes
                ACL='public-read'  # Make publicly readable
            )
            
            print(f"Data saved to s3://{self.bucket_name}/{filename}")
            return True
        except Exception as e:
            print(f"Error saving to S3: {e}")
            return False


def lambda_handler(event, context):
    """
    Lambda handler for dynamic stock selection
    Runs at 10:30 PM CET daily
    """
    print(f"Starting dynamic stock picker at {datetime.now()}")
    
    try:
        alphavantage_key = os.environ.get('ALPHAVANTAGE_KEY')
        
        if not alphavantage_key:
            raise ValueError("ALPHAVANTAGE_KEY not set")
        
        # Initialize picker
        picker = DynamicStockPicker(alphavantage_key)
        
        # Get top gainers and losers
        print("Fetching top gainers and losers...")
        stock_data = picker.get_sp500_gainers_losers(limit=5)
        
        # Combine all stocks for analysis
        all_stocks = {**stock_data['gainers'], **stock_data['losers']}
        
        print(f"Selected stocks: {list(all_stocks.keys())}")
        
        # Analyze all stocks
        analysis_results = picker.analyze_stocks(all_stocks)
        
        # Separate into gainers and losers
        gainer_results = [r for r in analysis_results if r['ticker'] in stock_data['gainers']]
        loser_results = [r for r in analysis_results if r['ticker'] in stock_data['losers']]
        
        # Prepare final data structure
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'gainers': gainer_results,
            'losers': loser_results,
            'metadata': {
                'total_stocks': len(analysis_results),
                'data_source': 'Alpha Vantage',
                'auto_selected': stock_data['success']
            }
        }
        
        # Save to S3
        success = picker.save_to_s3(dashboard_data)
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Dashboard data updated successfully',
                    'stocks_analyzed': len(all_stocks),
                    'timestamp': datetime.now().isoformat()
                })
            }
        else:
            raise Exception("Failed to save to S3")
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error updating dashboard data',
                'error': str(e)
            })
        }
