"""
AWS Lambda handler for Market Sentiment Analyzer
"""
import json
import os
import boto3
from datetime import datetime
from sentiment_analyzer import MarketSentimentAnalyzer
from email_sender import send_email_report

def save_to_s3(data):
    """Save analysis results to S3"""
    s3_client = boto3.client('s3', region_name='eu-north-1')
    bucket_name = 'putcall-dashboard-data'
    
    # Prepare data for frontend
    dashboard_data = {
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'stocks': data  # Your analysis results
    }
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key='dashboard-data.json',
            Body=json.dumps(dashboard_data, indent=2),
            ContentType='application/json'
        )
        print("✅ Data saved to S3!")
        return True
    except Exception as e:
        print(f"❌ Error saving to S3: {e}")
        return False

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    Triggered by EventBridge scheduler
    """
    print(f"Starting sentiment analysis at {datetime.now()}")
    
    try:
        # Get configuration from environment variables
        newsapi_key = os.environ.get('NEWSAPI_KEY')
        alphavantage_key = os.environ.get('ALPHAVANTAGE_KEY')
        
        # Tickers configuration
        tickers_env = os.environ.get('TICKERS', 'AAPL:Apple,MSFT:Microsoft,GOOGL:Google,TSLA:Tesla,NVDA:NVIDIA')
        tickers = {}
        for ticker_pair in tickers_env.split(','):
            if ':' in ticker_pair:
                ticker, company = ticker_pair.strip().split(':', 1)
                tickers[ticker.strip()] = company.strip() 
        
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
        analyzer = MarketSentimentAnalyzer(newsapi_key, alphavantage_key)
        
        print("Generating report...")
        report, data = analyzer.generate_report(tickers)
        
        # Save to S3 for dashboard
        print("Saving to S3...")
        s3_success = save_to_s3(data)
        
        # Send email if enabled
        if email_config['enabled']:
            print("Sending email...")
            email_success = send_email_report(report, email_config)
            if email_success:
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
                'stocks_analyzed': len(tickers),
                's3_saved': s3_success
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
                'timestamp': datetime.now().isoformat()
            })
        }
