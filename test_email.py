"""
Quick test script to verify email delivery works before scheduling
"""
from sentiment_analyzer import MarketSentimentAnalyzer
from config import NEWSAPI_KEY, TICKERS, EMAIL_CONFIG
from email_sender import send_email_report

print("=" * 60)
print("📧 EMAIL TEST - Market Sentiment Analyzer")
print("=" * 60)
print(f"\nFrom: {EMAIL_CONFIG['from_email']}")
print(f"To: {EMAIL_CONFIG['to_email']}")
print(f"Email enabled: {EMAIL_CONFIG.get('enabled', False)}")
print("\n" + "=" * 60)

if not EMAIL_CONFIG.get('enabled', False):
    print("\n⚠️  Email is disabled in config!")
    print("Set EMAIL_CONFIG['enabled'] = True in config.py")
    exit(1)

print("\n🔍 Running sentiment analysis...")
print("(This may take 30-60 seconds)\n")

try:
    # Run the analysis
    analyzer = MarketSentimentAnalyzer(NEWSAPI_KEY)
    report, data = analyzer.generate_report(TICKERS)
    
    print("\n✅ Analysis complete!")
    print("\n" + "=" * 60)
    print("PREVIEW OF REPORT:")
    print("=" * 60)
    # Show first 500 characters of report
    print(report[:500] + "...\n")
    
    # Send the email
    print("=" * 60)
    print("📧 Sending email...")
    print("=" * 60)
    
    success = send_email_report(report, EMAIL_CONFIG)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Check your inbox!")
        print("=" * 60)
        print(f"\nEmail sent to: {EMAIL_CONFIG['to_email']}")
        print("If you don't see it, check your spam folder.")
        print("\nYou're ready to start the scheduler!")
        print("Run: python scheduler.py")
    else:
        print("\n" + "=" * 60)
        print("❌ EMAIL FAILED")
        print("=" * 60)
        print("\nCommon issues:")
        print("1. App password incorrect (should be 16 chars, no spaces)")
        print("2. Email address wrong")
        print("3. 2-Step Verification not enabled on Gmail")
        print("4. Need to enable 'Less secure app access' (for non-Gmail)")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nCheck your config.py settings!")
