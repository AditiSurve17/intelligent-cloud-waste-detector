import boto3
import json
import os
from datetime import datetime
from boto3.dynamodb.conditions import Attr

# Initialize clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# DynamoDB table and S3 bucket details
DDB_TABLE = 'cwd-waste-recommendations'
S3_BUCKET = 'cwd-cost-usage-reports-as-2025'
S3_PREFIX = 'terraform-scripts/'

def lambda_handler(event, context):
    table = dynamodb.Table(DDB_TABLE)

    # Step 1: Filter only Terminated resources
    response = table.scan(
        FilterExpression=Attr('status').eq('Terminated')
    )
    terminated_resources = response.get('Items', [])

    if not terminated_resources:
        return {
            'statusCode': 200,
            'body': 'No terminated resources found.'
        }

    # Step 2: Build Terraform configuration
    terraform_blocks = []

    for item in terminated_resources:
        resource_type = item.get('service_type')         # e.g., 'ec2', 'ebs'
        resource_id = item.get('resource_id')            # e.g., 'i-1234567890abcdef'
        region = item.get('region', 'us-east-1')         # default to us-east-1

        tf_block = generate_terraform_block(resource_type, resource_id, region)
        if tf_block:
            terraform_blocks.append(tf_block)

    # Step 3: Create full .tf content
    full_tf_script = "\n\n".join(terraform_blocks)

    # Step 4: Generate S3 key
    timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    s3_key = f"{S3_PREFIX}terraform-delete-{timestamp}.tf"

    # Step 5: Upload to S3
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=full_tf_script.encode('utf-8'),
        ContentType='text/plain'
    )

    return {
        'statusCode': 200,
        'body': f"Terraform file generated and uploaded: s3://{S3_BUCKET}/{s3_key}"
    }

def generate_terraform_block(service_type, resource_id, region):
    resource_name = resource_id.replace('-', '_')

    if service_type.lower() == 'ec2':
        return f'''
# EC2 Terminated Resource
resource "aws_instance" "{resource_name}" {{
  # Placeholder block for import and destroy
  # Run: terraform import aws_instance.{resource_name} {resource_id}
  # Then: terraform destroy -target=aws_instance.{resource_name}
  provider = aws
}}

provider "aws" {{
  region = "{region}"
}}
'''.strip()

    elif service_type.lower() == 'ebs':
        return f'''
# EBS Volume Terminated
resource "aws_ebs_volume" "{resource_name}" {{
  # Placeholder block for import and destroy
  # Run: terraform import aws_ebs_volume.{resource_name} {resource_id}
  # Then: terraform destroy -target=aws_ebs_volume.{resource_name}
  provider = aws
}}

provider "aws" {{
  region = "{region}"
}}
'''.strip()

    # Add more services if needed
    else:
        return f'''
# Unsupported service type: {service_type}
# Manual review required for resource: {resource_id}
'''.strip()

