import schedule
import time
from datetime import datetime
import json
import os
from sentiment_analyzer import MarketSentimentAnalyzer
from config import NEWSAPI_KEY, TICKERS, EMAIL_CONFIG
from email_sender import send_email_report

# Create reports directory if it doesn't exist
if not os.path.exists('reports'):
    os.makedirs('reports')

def run_daily_analysis():
    """Run the sentiment analysis and send via email"""
    print(f"\n{'='*60}")
    print(f"🕐 Running scheduled analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Run analysis
        analyzer = MarketSentimentAnalyzer(NEWSAPI_KEY)
        report, data = analyzer.generate_report(TICKERS)
        
        # Save reports locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save text report
        report_file = f'reports/sentiment_report_{timestamp}.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"💾 Saved report to: {report_file}")
        
        # Save JSON data
        data_file = f'reports/sentiment_data_{timestamp}.json'
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved data to: {data_file}")
        
        # Send email
        if EMAIL_CONFIG.get('enabled', False):
            print("📧 Sending email...")
            send_email_report(report, EMAIL_CONFIG)
        else:
            print("⏭️  Email disabled in config")
        
        print(f"\n{'='*60}")
        print("✅ Analysis complete!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main scheduler loop"""
    print("=" * 60)
    print("📅 MARKET SENTIMENT ANALYZER - SCHEDULER")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scheduled time: 7:00 AM daily")
    print(f"Email delivery: {'Enabled' if EMAIL_CONFIG.get('enabled') else 'Disabled'}")
    print("=" * 60)
    print("\n⏳ Waiting for scheduled time...")
    print("Press Ctrl+C to stop\n")
    
    # Schedule the job
    schedule.every().day.at("07:00").do(run_daily_analysis)
    
    # Optional: Run immediately on start for testing
    # Uncomment the next line if you want to test right away
    # run_daily_analysis()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped by user")

if __name__ == "__main__":
    main()
