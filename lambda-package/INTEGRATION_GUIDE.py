"""
INTEGRATION GUIDE: Adding Top Gainers/Losers to Your Dashboard

This guide shows you how to integrate the SP500MoversAnalyzer into your existing
putcall.nl dashboard.
"""

# ============================================================================
# STEP 1: Update your Lambda function to include movers analysis
# ============================================================================

"""
In your main Lambda handler, add this import at the top:
"""
from sp500_movers import SP500MoversAnalyzer

"""
Then in your handler function, add this code after your existing analysis:
"""

def lambda_handler(event, context):
    # Your existing code...
    analyzer = MarketSentimentAnalyzer(NEWS_API_KEY, ALPHAVANTAGE_KEY)
    
    # Existing tickers analysis
    tickers = {
        'AAPL': 'Apple',
        'MSFT': 'Microsoft',
        'GOOGL': 'Google',
        'TSLA': 'Tesla',
        'NVDA': 'NVIDIA'
    }
    
    report, results = analyzer.generate_report(tickers)
    
    # NEW: Add top gainers and losers
    movers_analyzer = SP500MoversAnalyzer(ALPHAVANTAGE_KEY)
    
    # Note: Due to API rate limits, you might want to:
    # Option A: Cache this data (update every 5-10 minutes)
    # Option B: Use a smaller sample (limit=50 instead of 100)
    # Option C: Use a different data source for real-time movers
    
    movers_data = movers_analyzer.get_top_gainers_losers(limit=50, top_n=10)
    
    # Combine both datasets
    dashboard_data = {
        'main_stocks': results,
        'top_gainers': movers_data['gainers'],
        'top_losers': movers_data['losers'],
        'last_updated': datetime.now().isoformat()
    }
    
    # Return as JSON for your frontend
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(dashboard_data)
    }


# ============================================================================
# STEP 2: Update your HTML/JavaScript to display movers
# ============================================================================

"""
Add this JavaScript to your frontend to fetch and display movers:
"""

javascript_code = """
// Fetch movers data from your Lambda API
async function fetchMoversData() {
    try {
        const response = await fetch('YOUR_LAMBDA_API_URL');
        const data = await response.json();
        
        displayGainersLosers(data.top_gainers, data.top_losers);
    } catch (error) {
        console.error('Error fetching movers:', error);
    }
}

// Display gainers and losers in tables
function displayGainersLosers(gainers, losers) {
    const gainersTable = document.getElementById('gainers-table');
    const losersTable = document.getElementById('losers-table');
    
    // Populate gainers
    gainersTable.innerHTML = generateMoversTable(gainers, 'gainer');
    
    // Populate losers
    losersTable.innerHTML = generateMoversTable(losers, 'loser');
}

function generateMoversTable(stocks, type) {
    let html = `
        <table class="movers-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Ticker</th>
                    <th>Price</th>
                    <th>Change</th>
                    <th>Signal</th>
                    <th>Sentiment</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    stocks.forEach((stock, index) => {
        const changeClass = stock.change_pct > 0 ? 'positive' : 'negative';
        const signalClass = getSignalClass(stock.signal);
        
        html += `
            <tr>
                <td>${index + 1}</td>
                <td class="ticker">${stock.ticker}</td>
                <td>$${stock.price.toFixed(2)}</td>
                <td class="${changeClass}">${stock.change_pct > 0 ? '+' : ''}${stock.change_pct.toFixed(2)}%</td>
                <td class="signal ${signalClass}">${stock.signal}</td>
                <td>${stock.sentiment}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    return html;
}

function getSignalClass(signal) {
    if (signal.includes('BUY')) return 'signal-buy';
    if (signal.includes('SELL')) return 'signal-sell';
    if (signal.includes('OVERBOUGHT') || signal.includes('OVERSOLD')) return 'signal-caution';
    return 'signal-neutral';
}

// Update every 5 minutes
setInterval(fetchMoversData, 5 * 60 * 1000);
fetchMoversData(); // Initial load
"""

# ============================================================================
# STEP 3: Add CSS styling for movers tables
# ============================================================================

css_code = """
/* Top Gainers/Losers Section */
.movers-container {
    display: flex;
    gap: 2rem;
    margin: 2rem 0;
}

.movers-section {
    flex: 1;
    background: #1a1d2e;
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid #2a2d3e;
}

.movers-section h2 {
    color: #4a9eff;
    margin-bottom: 1rem;
    font-size: 1.5rem;
}

.movers-table {
    width: 100%;
    border-collapse: collapse;
}

.movers-table th {
    background: #252837;
    padding: 0.75rem;
    text-align: left;
    color: #8b92b0;
    font-weight: 600;
    border-bottom: 2px solid #2a2d3e;
}

.movers-table td {
    padding: 0.75rem;
    border-bottom: 1px solid #2a2d3e;
    color: #e0e6ed;
}

.movers-table .ticker {
    font-weight: bold;
    color: #4a9eff;
}

.movers-table .positive {
    color: #4caf50;
    font-weight: bold;
}

.movers-table .negative {
    color: #f44336;
    font-weight: bold;
}

.movers-table .signal {
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

.signal-buy {
    background: rgba(76, 175, 80, 0.2);
    color: #4caf50;
}

.signal-sell {
    background: rgba(244, 67, 54, 0.2);
    color: #f44336;
}

.signal-caution {
    background: rgba(255, 193, 7, 0.2);
    color: #ffc107;
}

.signal-neutral {
    background: rgba(158, 158, 158, 0.2);
    color: #9e9e9e;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .movers-container {
        flex-direction: column;
    }
}
"""


# ============================================================================
# STEP 4: HTML Structure
# ============================================================================

html_structure = """
<!-- Add this to your HTML body after your main stocks table -->

<div class="movers-container">
    <!-- Top Gainers -->
    <div class="movers-section">
        <h2>🚀 Top 10 Gainers</h2>
        <div id="gainers-table">
            Loading...
        </div>
    </div>
    
    <!-- Top Losers -->
    <div class="movers-section">
        <h2>📉 Top 10 Losers</h2>
        <div id="losers-table">
            Loading...
        </div>
    </div>
</div>
"""


# ============================================================================
# ALTERNATIVE: Use a Different Data Source (Recommended for Production)
# ============================================================================

"""
IMPORTANT NOTE:

Alpha Vantage has strict rate limits:
- Free tier: 5 API calls per minute, 500 per day
- Fetching 100 stocks would take 20 minutes!

BETTER OPTIONS for production:

1. **Yahoo Finance (yfinance)** - Free, no API key needed
   pip install yfinance
   
2. **Finnhub.io** - Free tier: 60 calls/minute
   https://finnhub.io/
   
3. **IEX Cloud** - Better rate limits
   https://iexcloud.io/
   
4. **Pre-computed data** - Have a separate Lambda that runs every 5 minutes
   to update movers data and stores it in DynamoDB/S3

5. **Web scraping** - Scrape from finviz.com or similar (check their ToS)

Here's a quick yfinance implementation:
"""

yfinance_example = """
import yfinance as yf
import pandas as pd

def get_sp500_movers_yfinance(top_n=10):
    # Download S&P 500 tickers list
    sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    tickers = sp500['Symbol'].tolist()[:100]  # Get first 100
    
    # Download data for all tickers at once (much faster!)
    data = yf.download(tickers, period='1d', group_by='ticker', threads=True)
    
    movers = []
    for ticker in tickers:
        try:
            close = data[ticker]['Close'].iloc[-1]
            prev_close = data[ticker]['Open'].iloc[-1]
            change_pct = ((close - prev_close) / prev_close) * 100
            
            movers.append({
                'ticker': ticker,
                'price': close,
                'change_pct': change_pct
            })
        except:
            continue
    
    movers_df = pd.DataFrame(movers)
    gainers = movers_df.nlargest(top_n, 'change_pct')
    losers = movers_df.nsmallest(top_n, 'change_pct')
    
    return gainers, losers
"""

print("Integration guide created!")
print("\nKey files:")
print("1. sp500_movers.py - The movers analyzer module")
print("2. This integration guide")
print("\nNext steps:")
print("- Add sp500_movers.py to your Lambda deployment")
print("- Update your Lambda handler to call the movers analyzer")
print("- Add the HTML/CSS/JS to your frontend")
print("- Consider using yfinance instead for better performance")
