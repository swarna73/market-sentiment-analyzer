import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email_report(report_text, email_config):
    """
    Send the sentiment report via email
    
    Args:
        report_text: The formatted report string
        email_config: Dict with email settings
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config['from_email']
        msg['To'] = email_config['to_email']
        msg['Subject'] = f"📊 Market Sentiment Report - {datetime.now().strftime('%B %d, %Y')}"
        
        # Add body
        msg.attach(MIMEText(report_text, 'plain'))
        
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login and send
        server.login(email_config['from_email'], email_config['app_password'])
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
