# File: scripts/deploy.sh
# Deployment script for Lambda functions
# Run this to deploy updated Lambda functions to AWS

#!/bin/bash

# Deploy script for Cloud Waste Detector Lambda functions
# Region: ap-south-1
# Updated: 2025-06-26

echo "🚀 Deploying Cloud Waste Detector Lambda Functions..."

# Set AWS region
export AWS_DEFAULT_REGION=ap-south-1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if AWS CLI is configured
check_aws_config() {
    echo -e "${YELLOW}Checking AWS configuration...${NC}"
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${RED}❌ AWS CLI not configured or no access. Please run 'aws configure'${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ AWS CLI configured successfully${NC}"
}

# Function to update Lambda function code
update_lambda_function() {
    local function_name=$1
    local file_path=$2
    
    echo -e "${YELLOW}Updating Lambda function: ${function_name}...${NC}"
    
    # Create a temporary zip file
    cd src/lambda-functions/
    zip -q "${function_name}.zip" "${file_path##*/}"
    
    # Update the Lambda function
    if aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file "fileb://${function_name}.zip" \
        --region ap-south-1 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Successfully updated ${function_name}${NC}"
    else
        echo -e "${RED}❌ Failed to update ${function_name}${NC}"
        return 1
    fi
    
    # Clean up
    rm "${function_name}.zip"
    cd ../../
}

# Main deployment process
main() {
    echo "Starting deployment process..."
    
    # Check AWS configuration
    check_aws_config
    
    # Update Lambda functions
    echo -e "${YELLOW}Deploying Lambda functions...${NC}"
    
    update_lambda_function "cwd-data-collector" "cwd-data-collector.py"
    update_lambda_function "cwd-advanced-analytics" "cwd-advanced-analytics.py"
    
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test the functions in AWS Lambda console"
    echo "2. Check CloudWatch logs for any issues"
    echo "3. Verify EventBridge rules are working"
    echo "4. Monitor DynamoDB for new data"
}

# Run main function
main
