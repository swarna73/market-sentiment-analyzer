#!/bin/bash

echo "================================================"
echo "  Market Sentiment Analyzer - S3 Deployment"
echo "================================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
FUNCTION_NAME="market-sentiment-analyzer"
S3_BUCKET="market-sentiment-lambda-deploy-$(date +%s)"
REGION="eu-north-1"  # Change if needed

# Clean up
echo -e "${BLUE}🧹 Cleaning up...${NC}"
rm -rf lambda_package sentiment-analyzer-lambda.zip

# Create package
echo -e "${BLUE}📦 Creating package...${NC}"
mkdir lambda_package

# Copy files
echo -e "${BLUE}📄 Copying files...${NC}"
cp sentiment_analyzer.py email_sender.py lambda_function.py financial_metrics.py lambda_package/

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install requests yfinance -t lambda_package/ --quiet

# Create zip
echo -e "${BLUE}🗜️  Creating zip...${NC}"
cd lambda_package && zip -r ../sentiment-analyzer-lambda.zip . -q && cd ..

SIZE=$(du -h sentiment-analyzer-lambda.zip | cut -f1)
echo -e "${GREEN}✅ Package created: $SIZE${NC}"
echo ""

# Check size
SIZE_BYTES=$(stat -f%z sentiment-analyzer-lambda.zip 2>/dev/null || stat -c%s sentiment-analyzer-lambda.zip 2>/dev/null)
if [ $SIZE_BYTES -gt 50000000 ]; then
    echo -e "${YELLOW}⚠️  Package is ${SIZE} (>50MB) - using S3 deployment${NC}"
    USE_S3=true
else
    echo -e "${GREEN}✅ Package size OK for direct upload${NC}"
    USE_S3=false
fi

echo ""
read -p "Upload to AWS Lambda? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

if [ "$USE_S3" = true ]; then
    echo ""
    echo -e "${BLUE}☁️  Deploying via S3...${NC}"
    
    # Create S3 bucket
    echo -e "${BLUE}📦 Creating S3 bucket...${NC}"
    aws s3 mb s3://${S3_BUCKET} --region ${REGION} 2>/dev/null
    
    # Upload to S3
    echo -e "${BLUE}⬆️  Uploading to S3...${NC}"
    aws s3 cp sentiment-analyzer-lambda.zip s3://${S3_BUCKET}/sentiment-analyzer-lambda.zip
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Uploaded to S3${NC}"
        
        # Update Lambda from S3
        echo -e "${BLUE}🔄 Updating Lambda function...${NC}"
        aws lambda update-function-code \
            --function-name ${FUNCTION_NAME} \
            --s3-bucket ${S3_BUCKET} \
            --s3-key sentiment-analyzer-lambda.zip \
            --region ${REGION}
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Lambda function updated successfully!${NC}"
            
            # Clean up S3 (optional)
            read -p "Delete S3 bucket? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                aws s3 rm s3://${S3_BUCKET}/sentiment-analyzer-lambda.zip
                aws s3 rb s3://${S3_BUCKET}
                echo -e "${GREEN}✅ S3 bucket cleaned up${NC}"
            else
                echo -e "${YELLOW}S3 bucket kept: ${S3_BUCKET}${NC}"
            fi
        else
            echo -e "${RED}❌ Lambda update failed${NC}"
        fi
    else
        echo -e "${RED}❌ S3 upload failed${NC}"
    fi
else
    # Direct upload for smaller packages
    echo -e "${BLUE}☁️  Uploading directly to Lambda...${NC}"
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --zip-file fileb://sentiment-analyzer-lambda.zip \
        --region ${REGION}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Successfully uploaded to Lambda!${NC}"
    else
        echo -e "${RED}❌ Upload failed${NC}"
    fi
fi

echo ""
echo "================================================"
echo -e "${GREEN}Test your function at:${NC}"
echo "https://console.aws.amazon.com/lambda/home#/functions/${FUNCTION_NAME}"
echo "================================================"
