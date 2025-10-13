"""
AWS Lambda handler for Market Sentiment Analyzer
"""
import json
import os
from datetime import datetime
from sentiment_analyzer import MarketSentimentAnalyzer
from email_sender import send_email_report

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    Triggered by EventBridge scheduler
    """
    print(f"Starting sentiment analysis at {datetime.now()}")
    
    try:
        # Get configuration from environment variables
        newsapi_key = os.environ.get('NEWSAPI_KEY')
        
        # Tickers configuration
        tickers = {
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'GOOGL': 'Google',
            'TSLA': 'Tesla',
            'NVDA': 'NVIDIA'
        }
        
        # Email configuration
        email_config = {
            'enabled': os.environ.get('EMAIL_ENABLED', 'true').lower() == 'true',
            'from_email': os.environ.get('EMAIL_FROM'),
            'to_email': os.environ.get('EMAIL_TO'),
            'app_password': os.environ.get('EMAIL_PASSWORD')
        }
        
        # Validate environment variables
        if not newsapi_key:
            raise ValueError("NEWSAPI_KEY environment variable not set")
        if email_config['enabled'] and not all([
            email_config['from_email'],
            email_config['to_email'],
            email_config['app_password']
        ]):
            raise ValueError("Email configuration incomplete")
        
        # Run analysis
        print("Initializing analyzer...")
        analyzer = MarketSentimentAnalyzer(newsapi_key)
        
        print("Generating report...")
        report, data = analyzer.generate_report(tickers)
        
        # Send email if enabled
        if email_config['enabled']:
            print("Sending email...")
            success = send_email_report(report, email_config)
            if success:
                print("Email sent successfully!")
            else:
                print("Email sending failed")
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Sentiment analysis completed successfully',
                'timestamp': datetime.now().isoformat(),
                'email_sent': email_config['enabled'],
                'stocks_analyzed': len(tickers)
            })
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error during sentiment analysis',
                'error': str(e),
:q                'timestamp': datetime.now().isoformat()
            })
        }
