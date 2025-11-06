cd ~/Documents/market-sentiment-analyzer

# Clean up
rm -rf lambda_package
rm sentiment-analyzer-lambda.zip

# Create fresh directory
mkdir lambda_package

# Install requests with pip3
pip3 install requests  beautifulsoup4 -t lambda_package/


# Copy your files
cp sentiment_analyzer.py lambda_package/
cp email_sender.py lambda_package/
cp lambda_function.py lambda_package/
cp financial_metrics.py lambda_package/
cp fast_sp500_movers.py lambda_package/
cp sp500_movers.py lambda_package/


# Create zip
cd lambda_package
zip -r ../sentiment-analyzer-lambda.zip .
cd ..

# Upload
aws lambda update-function-code \
  --function-name market-sentiment-analyzer \
  --zip-file fileb://sentiment-analyzer-lambda.zip \
  --region eu-north-1
