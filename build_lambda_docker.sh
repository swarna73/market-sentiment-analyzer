#!/bin/bash

echo "================================================"
echo "  Building Lambda Package with Docker"
echo "================================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Clean up completely
echo -e "${BLUE}🧹 Complete cleanup...${NC}"
rm -rf lambda_package sentiment-analyzer-lambda.zip build_temp

# Create fresh directories
mkdir -p build_temp/python

# Build dependencies ONLY in a clean directory
echo -e "${BLUE}🐳 Building dependencies in Lambda environment...${NC}"
docker run --rm \
    --entrypoint /bin/bash \
    -v "$PWD/build_temp/python":/var/task \
    public.ecr.aws/lambda/python:3.11 \
    -c "pip install --upgrade pip && pip install requests 'numpy<2.0' 'yfinance' pandas multitasking lxml -t /var/task/ --no-cache-dir && rm -rf /var/task/*.dist-info"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Now create final package with source files
echo -e "${BLUE}📦 Creating final package...${NC}"
mkdir -p lambda_package

# Copy dependencies
cp -r build_temp/python/* lambda_package/

# Copy source files (on top of dependencies)
cp sentiment_analyzer.py lambda_package/
cp email_sender.py lambda_package/
cp lambda_function.py lambda_package/
cp financial_metrics.py lambda_package/

# Create deployment package
echo -e "${BLUE}🗜️  Creating deployment package...${NC}"
cd lambda_package
zip -r ../sentiment-analyzer-lambda.zip . -q
cd ..

# Cleanup build temp
rm -rf build_temp

SIZE=$(du -h sentiment-analyzer-lambda.zip | cut -f1)
echo ""
echo -e "${GREEN}✅ Package created: $SIZE${NC}"
echo ""

# Upload
REGION="eu-north-1"
FUNCTION_NAME="market-sentiment-analyzer"

read -p "Upload to AWS Lambda? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}☁️  Uploading to Lambda...${NC}"
    
    SIZE_BYTES=$(stat -f%z sentiment-analyzer-lambda.zip 2>/dev/null || stat -c%s sentiment-analyzer-lambda.zip 2>/dev/null)
    
    if [ $SIZE_BYTES -gt 50000000 ]; then
        echo -e "${BLUE}📦 Using S3 (package > 50MB)...${NC}"
        S3_BUCKET="lambda-deploy-temp-$(date +%s)"
        
        aws s3 mb s3://${S3_BUCKET} --region ${REGION} 2>/dev/null
        aws s3 cp sentiment-analyzer-lambda.zip s3://${S3_BUCKET}/
        
        aws lambda update-function-code \
            --function-name ${FUNCTION_NAME} \
            --s3-bucket ${S3_BUCKET} \
            --s3-key sentiment-analyzer-lambda.zip \
            --region ${REGION}
        
        UPLOAD_STATUS=$?
        
        aws s3 rm s3://${S3_BUCKET}/sentiment-analyzer-lambda.zip
        aws s3 rb s3://${S3_BUCKET}
        
        if [ $UPLOAD_STATUS -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully deployed!${NC}"
        fi
    else
        aws lambda update-function-code \
            --function-name ${FUNCTION_NAME} \
            --zip-file fileb://sentiment-analyzer-lambda.zip \
            --region ${REGION}
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Successfully deployed!${NC}"
        fi
    fi
fi

echo ""
echo "Test at: https://eu-north-1.console.aws.amazon.com/lambda"
