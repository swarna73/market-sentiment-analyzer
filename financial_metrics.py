"""
Financial Metrics Module using Alpha Vantage API
No numpy/pandas dependencies - Lambda friendly
"""
import requests
from datetime import datetime

class FinancialMetricsAnalyzer:
    def __init__(self, api_key=None):
        """
        Initialize with Alpha Vantage API key
        Get free key at: https://www.alphavantage.co/support/#api-key
        """
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_stock_fundamentals(self, ticker):
        """
        Fetch fundamental financial metrics for a stock
        """
        if not self.api_key:
            return {
                'ticker': ticker,
                'success': False,
                'error': 'No Alpha Vantage API key provided',
                'metrics': {}
            }
        
        try:
            # Get company overview (includes most financial metrics)
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if we got data
            if not data or 'Symbol' not in data:
                return {
                    'ticker': ticker,
                    'success': False,
                    'error': 'No data returned from Alpha Vantage',
                    'metrics': {}
                }
            
            # Parse the metrics
            metrics = {
                # Price Information
                'current_price': self._safe_float(data.get('Price')),
                '52_week_high': self._safe_float(data.get('52WeekHigh')),
                '52_week_low': self._safe_float(data.get('52WeekLow')),
                
                # Valuation Metrics
                'market_cap': self._safe_float(data.get('MarketCapitalization')),
                'pe_ratio': self._safe_float(data.get('PERatio')),
                'forward_pe': self._safe_float(data.get('ForwardPE')),
                'peg_ratio': self._safe_float(data.get('PEGRatio')),
                'price_to_book': self._safe_float(data.get('PriceToBookRatio')),
                'price_to_sales': self._safe_float(data.get('PriceToSalesRatioTTM')),
                'ev_to_ebitda': self._safe_float(data.get('EVToEBITDA')),
                
                # Profitability Metrics
                'profit_margin': self._safe_float(data.get('ProfitMargin')),
                'operating_margin': self._safe_float(data.get('OperatingMarginTTM')),
                'return_on_equity': self._safe_float(data.get('ReturnOnEquityTTM')),
                'return_on_assets': self._safe_float(data.get('ReturnOnAssetsTTM')),
                'revenue': self._safe_float(data.get('RevenueTTM')),
                'revenue_per_share': self._safe_float(data.get('RevenuePerShareTTM')),
                'quarterly_revenue_growth': self._safe_float(data.get('QuarterlyRevenueGrowthYOY')),
                
                # Per Share Metrics
                'eps': self._safe_float(data.get('EPS')),
                'book_value': self._safe_float(data.get('BookValue')),
                'dividend_yield': self._safe_float(data.get('DividendYield')),
                'dividend_per_share': self._safe_float(data.get('DividendPerShare')),
                
                # Financial Health
                'debt_to_equity': self._safe_float(data.get('DebtToEquity')),
                'current_ratio': self._safe_float(data.get('CurrentRatio')),
                'quick_ratio': self._safe_float(data.get('QuickRatio')),
                
                # Trading Metrics
                'beta': self._safe_float(data.get('Beta')),
                
                # Other Info
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'description': data.get('Description', '')[:200] + '...',  # Truncate
            }
            
            return {
                'ticker': ticker,
                'success': True,
                'metrics': metrics,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker}: {e}")
            return {
                'ticker': ticker,
                'success': False,
                'error': str(e),
                'metrics': {}
            }
    
    def _safe_float(self, value):
        """Safely convert string to float, return None if invalid"""
        if value is None or value == 'None' or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def analyze_valuation(self, metrics):
        """Analyze if a stock is overvalued, undervalued, or fairly valued"""
        assessment = {
            'overall': 'Unknown',
            'signals': [],
            'concerns': [],
            'strengths': []
        }
        
        pe_ratio = metrics.get('pe_ratio')
        peg_ratio = metrics.get('peg_ratio')
        price_to_book = metrics.get('price_to_book')
        debt_to_equity = metrics.get('debt_to_equity')
        profit_margin = metrics.get('profit_margin')
        revenue_growth = metrics.get('quarterly_revenue_growth')
        
        # P/E Ratio Analysis
        if pe_ratio:
            if pe_ratio < 15:
                assessment['signals'].append(f"Low P/E ({pe_ratio:.2f}) - potentially undervalued")
            elif pe_ratio > 30:
                assessment['concerns'].append(f"High P/E ({pe_ratio:.2f}) - potentially overvalued")
            else:
                assessment['signals'].append(f"Moderate P/E ({pe_ratio:.2f}) - fairly valued")
        
        # PEG Ratio Analysis
        if peg_ratio and peg_ratio > 0:
            if peg_ratio < 1:
                assessment['strengths'].append(f"PEG ratio {peg_ratio:.2f} - good value relative to growth")
            elif peg_ratio > 2:
                assessment['concerns'].append(f"PEG ratio {peg_ratio:.2f} - expensive relative to growth")
        
        # Price to Book
        if price_to_book:
            if price_to_book < 1:
                assessment['signals'].append(f"P/B ratio {price_to_book:.2f} - trading below book value")
            elif price_to_book > 5:
                assessment['concerns'].append(f"P/B ratio {price_to_book:.2f} - trading at premium")
        
        # Debt Analysis
        if debt_to_equity:
            if debt_to_equity > 2:
                assessment['concerns'].append(f"High debt-to-equity ({debt_to_equity:.2f})")
            elif debt_to_equity < 0.5:
                assessment['strengths'].append(f"Low debt-to-equity ({debt_to_equity:.2f}) - strong balance sheet")
        
        # Profitability
        if profit_margin:
            if profit_margin > 0.20:
                assessment['strengths'].append(f"Strong profit margin ({profit_margin*100:.1f}%)")
            elif profit_margin < 0.05:
                assessment['concerns'].append(f"Low profit margin ({profit_margin*100:.1f}%)")
        
        # Growth
        if revenue_growth:
            if revenue_growth > 0.15:
                assessment['strengths'].append(f"Strong revenue growth ({revenue_growth*100:.1f}%)")
            elif revenue_growth < 0:
                assessment['concerns'].append(f"Declining revenue ({revenue_growth*100:.1f}%)")
        
        # Overall Assessment
        concern_count = len(assessment['concerns'])
        strength_count = len(assessment['strengths'])
        
        if strength_count > concern_count + 1:
            assessment['overall'] = 'Attractive'
        elif concern_count > strength_count + 1:
            assessment['overall'] = 'Concerns'
        else:
            assessment['overall'] = 'Mixed'
        
        return assessment
    
    def format_number(self, num):
        """Format large numbers to readable format"""
        if num is None:
            return 'N/A'
        
        if num >= 1_000_000_000_000:
            return f"${num/1_000_000_000_000:.2f}T"
        elif num >= 1_000_000_000:
            return f"${num/1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num/1_000_000:.2f}M"
        else:
            return f"${num:,.0f}"
    
    def format_percentage(self, num):
        """Format decimal to percentage"""
        if num is None:
            return 'N/A'
        return f"{num * 100:.2f}%"
    
    def format_ratio(self, num):
        """Format ratio with 2 decimal places"""
        if num is None:
            return 'N/A'
        return f"{num:.2f}"
