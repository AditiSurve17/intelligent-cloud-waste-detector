import boto3
import json
import os
from datetime import datetime
from boto3.dynamodb.conditions import Attr, Key

# Initialize clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# DynamoDB table and S3 bucket details
DDB_TABLE = 'cwd-waste-recommendations'
S3_BUCKET = 'cwd-cost-usage-reports-as-2025'
S3_PREFIX = 'terraform-scripts/'

def lambda_handler(event, context):
    # Add CORS headers to all responses
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
    }
    
    # Handle preflight OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": ""
        }
    
    table = dynamodb.Table(DDB_TABLE)
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '')
    
    try:
        if http_method == 'GET':
            # Check if this is a request for recommendations
            if 'recommendations' in path or path.endswith('/terraform'):
                return handle_get_recommendations(table, cors_headers)
            else:
                return handle_get_recommendations(table, cors_headers)
        elif http_method == 'POST':
            # Handle POST request - generate terraform for specific resource
            return handle_generate_terraform(event, table, cors_headers)
        else:
            return {
                "statusCode": 405,
                "headers": cors_headers,
                "body": json.dumps({"error": "Method not allowed"})
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"})
        }

def handle_get_recommendations(table, cors_headers):
    """Handle GET request to fetch all recommendations"""
    try:
        response = table.scan()
        items = response.get("Items", [])
        
        # Transform data for frontend
        recommendations = []
        for item in items:
            recommendations.append({
                "resourceId": item.get('resource_id', ''),
                "resourceName": item.get('resource_name', item.get('resource_id', '')),
                "resourceType": item.get('service_type', 'unknown'),
                "region": item.get('region', 'us-east-1'),
                "reason": item.get('recommendation', 'No reason provided'),
                "cost_impact": float(item.get('cost_impact', 0)),
                "last_used": item.get('last_used', ''),
                "status": item.get('status', 'Terminated')
            })
        
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({
                "recommendations": recommendations,
                "count": len(recommendations)
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": f"Failed to fetch recommendations: {str(e)}"})
        }
        
def handle_generate_terraform(event, table, cors_headers):
    """Handle POST request to generate terraform script"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        resource_id = body.get('resourceId') or body.get('resource_id')
        resource_type = body.get('resourceType') or body.get('resourceType')
        
        if not resource_id:
            return {
                "statusCode": 400,
                "headers": cors_headers,
                "body": json.dumps({"error": "Missing resourceId in request body"})
            }
        
        # If resource_type not provided, fetch from DynamoDB
        if not resource_type:
            response = table.scan(
                FilterExpression=Attr('resource_id').eq(resource_id)
            )
            items = response.get("Items", [])
            
            if not items:
                return {
                    "statusCode": 404,
                    "headers": cors_headers,
                    "body": json.dumps({"error": f"No resource found with ID: {resource_id}"})
                }
            
            item = items[0]
            resource_type = item.get('service_type')
            region = item.get('region', 'us-east-1')
            resource_name = item.get('resource_name', resource_id)
            cost_impact = item.get('cost_impact', 0)
            recommendation = item.get('recommendation', 'Resource identified as wasteful')
        else:
            region = body.get('region', 'us-east-1')
            resource_name = resource_id
            cost_impact = 0
            recommendation = 'Resource identified as wasteful'
        
        # Generate Terraform block
        tf_block = generate_terraform_block(resource_type, resource_id, region)
        
        if not tf_block:
            return {
                "statusCode": 501,
                "headers": cors_headers,
                "body": json.dumps({"error": f"Terraform generation not supported for {resource_type}"})
            }
        
        # Upload to S3
        s3_key = f"{S3_PREFIX}{resource_type}_{resource_id.replace(':', '_').replace('/', '_')}.tf"
        s3_url = None
        try:
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=tf_block,
                ContentType='text/plain',
                Metadata={
                    'resource_id': resource_id,
                    'resource_type': resource_type,
                    'generated_by': 'intelligent-cloud-waste-detector',
                    'generated_at': datetime.now().isoformat()
                }
            )
            s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
        except Exception as s3_error:
            print(f"Failed to upload to S3: {str(s3_error)}")
            # Continue without S3 upload - still return the terraform block
        
        return {
            "statusCode": 200,
            "headers": {**cors_headers, "Content-Type": "application/json"},
            "body": json.dumps({
                "terraform": tf_block,
                "resource_id": resource_id,
                "resource_type": resource_type,
                "s3_location": s3_url,
                "s3_key": s3_key if s3_url else None,
                "generated_at": datetime.now().isoformat()
            })
        }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": f"Failed to generate terraform: {str(e)}"})
        }
                

def generate_terraform_block(service_type, resource_id, region):
    """Generate Terraform block based on service type"""
    resource_name = resource_id.replace('-', '_').replace(':', '_').replace('/', '_')
    
    if service_type.lower() == 'ec2':
        return f'''# EC2 Instance - Resource ID: {resource_id}
resource "aws_instance" "{resource_name}" {{
  # This is a placeholder for importing and destroying the resource
  # Step 1: Import the existing resource
  # terraform import aws_instance.{resource_name} {resource_id}
  # Step 2: Destroy the resource
  # terraform destroy -target=aws_instance.{resource_name}
}}

provider "aws" {{
  region = "{region}"
}}'''

    elif service_type.lower() == 'ebs':
        return f'''# EBS Volume - Resource ID: {resource_id}
resource "aws_ebs_volume" "{resource_name}" {{
  # This is a placeholder for importing and destroying the resource
  # Step 1: Import the existing resource
  # terraform import aws_ebs_volume.{resource_name} {resource_id}
  # Step 2: Destroy the resource
  # terraform destroy -target=aws_ebs_volume.{resource_name}
}}

provider "aws" {{
  region = "{region}"
}}'''

    elif service_type.lower() == 's3':
        return f'''# S3 Bucket - Resource ID: {resource_id}
resource "aws_s3_bucket" "{resource_name}" {{
  # This is a placeholder for importing and destroying the resource
  # Step 1: Import the existing resource
  # terraform import aws_s3_bucket.{resource_name} {resource_id}
  # Step 2: Destroy the resource
  # terraform destroy -target=aws_s3_bucket.{resource_name}
}}

provider "aws" {{
  region = "{region}"
}}'''

    elif service_type.lower() == 'rds':
        return f'''# RDS Instance - Resource ID: {resource_id}
resource "aws_db_instance" "{resource_name}" {{
  # This is a placeholder for importing and destroying the resource
  # Step 1: Import the existing resource
  # terraform import aws_db_instance.{resource_name} {resource_id}
  # Step 2: Destroy the resource
  # terraform destroy -target=aws_db_instance.{resource_name}
}}

provider "aws" {{
  region = "{region}"
}}'''

    elif service_type.lower() == 'lambda':
        return f'''# Lambda Function - Resource ID: {resource_id}
resource "aws_lambda_function" "{resource_name}" {{
  # This is a placeholder for importing and destroying the resource
  # Step 1: Import the existing resource
  # terraform import aws_lambda_function.{resource_name} {resource_id}
  # Step 2: Destroy the resource
  # terraform destroy -target=aws_lambda_function.{resource_name}
}}

provider "aws" {{
  region = "{region}"
}}'''

    else:
        return f'''# Unsupported service type: {service_type}
# Resource ID: {resource_id}
# Manual review and cleanup required
# 
# You may need to:
# 1. Identify the correct Terraform resource type for {service_type}
# 2. Create appropriate Terraform configuration
# 3. Import the resource using: terraform import <resource_type>.<name> {resource_id}
# 4. Apply destroy: terraform destroy -target=<resource_type>.<name>

provider "aws" {{
  region = "{region}"
}}'''