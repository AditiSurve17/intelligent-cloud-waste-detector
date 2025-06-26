# File: scripts/setup-aws.sh
# AWS infrastructure setup script
# Run this to create all necessary AWS resources

#!/bin/bash

# AWS Infrastructure Setup Script
# Cloud Waste Detector Project
# Region: ap-south-1

echo "🏗️ Setting up AWS infrastructure for Cloud Waste Detector..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGION="ap-south-1"
BUCKET_NAME="cwd-cost-usage-reports-as-2025"
ROLE_NAME="CloudWasteDetector-LambdaRole"

# Function to create S3 bucket
create_s3_bucket() {
    echo -e "${YELLOW}Creating S3 bucket: ${BUCKET_NAME}...${NC}"
    
    if aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" 2>/dev/null; then
        echo -e "${GREEN}✅ S3 bucket created successfully${NC}"
    else
        echo -e "${BLUE}ℹ️ S3 bucket already exists or creation skipped${NC}"
    fi
}

# Function to create DynamoDB tables
create_dynamodb_tables() {
    echo -e "${YELLOW}Creating DynamoDB tables...${NC}"
    
    # Create usage data table
    if aws dynamodb create-table \
        --table-name "cwd-processed-usage-data" \
        --attribute-definitions \
            AttributeName=resource_id,AttributeType=S \
            AttributeName=timestamp,AttributeType=S \
        --key-schema \
            AttributeName=resource_id,KeyType=HASH \
            AttributeName=timestamp,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Usage data table created${NC}"
    else
        echo -e "${BLUE}ℹ️ Usage data table already exists${NC}"
    fi
    
    # Create recommendations table
    if aws dynamodb create-table \
        --table-name "cwd-waste-recommendations" \
        --attribute-definitions \
            AttributeName=recommendation_id,AttributeType=S \
            AttributeName=created_at,AttributeType=S \
        --key-schema \
            AttributeName=recommendation_id,KeyType=HASH \
            AttributeName=created_at,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Recommendations table created${NC}"
    else
        echo -e "${BLUE}ℹ️ Recommendations table already exists${NC}"
    fi
}

# Function to create IAM role
create_iam_role() {
    echo -e "${YELLOW}Creating IAM role: ${ROLE_NAME}...${NC}"
    
    # Trust policy for Lambda
    cat > /tmp/trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
    
    if aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file:///tmp/trust-policy.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ IAM role created${NC}"
    else
        echo -e "${BLUE}ℹ️ IAM role already exists${NC}"
    fi
    
    # Attach policies
    aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>/dev/null
    aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess" 2>/dev/null
    aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess" 2>/dev/null
    
    # Clean up
    rm /tmp/trust-policy.json
}

# Main setup function
main() {
    echo "Starting AWS infrastructure setup..."
    echo "Region: $REGION"
    echo ""
    
    create_s3_bucket
    create_dynamodb_tables
    create_iam_role
    
    echo ""
    echo -e "${GREEN}🎉 AWS infrastructure setup completed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Deploy Lambda functions using scripts/deploy.sh"
    echo "2. Set up EventBridge rules in AWS console"
    echo "3. Configure Cost & Usage Reports"
    echo "4. Upload sample data for testing"
}

# Run main function
main
