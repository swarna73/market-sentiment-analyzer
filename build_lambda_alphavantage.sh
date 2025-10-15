#!/bin/bash

echo "================================================"
echo "  Building Lambda with Alpha Vantage"
echo "================================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Complete cleanup
echo -e "${BLUE}🧹 Complete cleanup...${NC}"
sudo rm -rf lambda_package
rm -f sentiment-analyzer-lambda.zip

# Create fresh package
mkdir -p lambda_package

# Install requests FIRST
echo -e "${BLUE}📥 Installing requests...${NC}"
pip install requests -t lambda_package/ --quiet

# Then copy source files
echo -e "${BLUE}📄 Copying source files...${NC}"
cp sentiment_analyzer.py lambda_package/
cp email_sender.py lambda_package/
cp lambda_function.py lambda_package/
cp financial_metrics.py lambda_package/

# Create zip
echo -e "${BLUE}🗜️  Creating zip...${NC}"
cd lambda_package
zip -r ../sentiment-analyzer-lambda.zip . -q
cd ..

SIZE=$(du -h sentiment-analyzer-lambda.zip | cut -f1)
echo -e "${GREEN}✅ Package created: $SIZE${NC}"

# Check if requests is in the package
if unzip -l sentiment-analyzer-lambda.zip | grep -q "requests/"; then
    echo -e "${GREEN}✅ Requests library included${NC}"
else
    echo -e "${RED}⚠️  Warning: requests library not found!${NC}"
fi

echo ""

# Upload
REGION="eu-north-1"
FUNCTION_NAME="market-sentiment-analyzer"

read -p "Upload to AWS Lambda? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}☁️  Uploading...${NC}"
    
    aws lambda update-function-code \
        --function-name ${FUNCTION_NAME} \
        --zip-file fileb://sentiment-analyzer-lambda.zip \
        --region ${REGION}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Deployed!${NC}"
    fi
fi

echo ""
echo "Done!"
