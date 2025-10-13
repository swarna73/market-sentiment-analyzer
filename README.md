## ☁️ Cloud Deployment (AWS Lambda)

The system can run 24/7 in the cloud using AWS Lambda, independent of your local machine.

### Benefits
- ✅ Runs even when your computer is off
- ✅ 99.99% uptime
- ✅ Completely free (within AWS free tier)
- ✅ Zero maintenance
- ✅ Automatic scaling

### Quick Deploy to AWS Lambda

1. **Create deployment package:**
```bash
# Install dependencies
mkdir lambda_package
pip install requests -t lambda_package/
cp sentiment_analyzer.py email_sender.py lambda_function.py lambda_package/

# Create zip
cd lambda_package && zip -r ../sentiment-analyzer-lambda.zip . && cd ..
```

2. **Deploy via AWS Console:**
   - Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda)
   - Create function: `market-sentiment-analyzer`
   - Runtime: Python 3.11
   - Upload `sentiment-analyzer-lambda.zip`
   - Set timeout: 5 minutes, Memory: 512 MB

3. **Add environment variables:**
   - `NEWSAPI_KEY`
   - `EMAIL_ENABLED`
   - `EMAIL_FROM`
   - `EMAIL_TO`
   - `EMAIL_PASSWORD`

4. **Schedule with EventBridge:**
   - Add trigger: EventBridge (CloudWatch Events)
   - Schedule: `cron(0 5 ? * MON-FRI *)` (7 AM CET, Mon-Fri)
   - Adjust timezone as needed

### Cost
**$0.00** - Stays within AWS free tier (1M requests/month, ~20 actual runs/month)

### Monitoring
View logs in CloudWatch to monitor execution and troubleshoot issues.

---
