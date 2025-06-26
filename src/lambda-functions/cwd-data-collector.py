# File: src/lambda-functions/cwd-data-collector.py
# Enhanced Lambda function with scheduling support and advanced waste detection
# Updated: 2025-06-26 - Checkpoint 4

import json
import boto3
import gzip
import csv
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import uuid
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients for ap-south-1
s3_client = boto3.client('s3', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# Your DynamoDB tables
usage_table = dynamodb.Table('cwd-processed-usage-data')
recommendations_table = dynamodb.Table('cwd-waste-recommendations')

def lambda_handler(event, context):
    """
    Enhanced Lambda function supporting both S3 events and scheduled processing
    """
    
    try:
        processed_records = 0
        recommendations_count = 0
        
        # Determine event type
        if 'source' in event and event['source'] == 'aws.events':
            # Scheduled event from EventBridge
            logger.info("Processing scheduled event - scanning S3 bucket for new files")
            processed_records, recommendations_count = process_scheduled_event(event)
            
        elif 'Records' in event:
            # S3 event (original functionality)
            logger.info("Processing S3 event")
            processed_records, recommendations_count = process_s3_event(event)
            
        elif event.get('test_direct'):
            # Direct test (existing functionality)
            logger.info("Processing direct test")
            processed_records, recommendations_count = test_with_sample_data()
            
        else:
            logger.warning("Unknown event type")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Unknown event type',
                    'timestamp': datetime.now().isoformat()
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed cost data',
                'processed_records': processed_records,
                'recommendations_count': recommendations_count,
                'timestamp': datetime.now().isoformat(),
                'event_type': get_event_type(event)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def get_event_type(event):
    """Determine event type for logging"""
    if 'source' in event and event['source'] == 'aws.events':
        return 'scheduled'
    elif 'Records' in event:
        return 's3_trigger'
    elif event.get('test_direct'):
        return 'direct_test'
    else:
        return 'unknown'

def process_scheduled_event(event):
    """Process scheduled events - scan S3 bucket for unprocessed files"""
    try:
        bucket_name = event.get('detail', {}).get('bucket', 'cwd-cost-usage-reports-as-2025')
        
        # List all CSV files in bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        
        if 'Contents' not in response:
            logger.info("No files found in bucket")
            return 0, 0
        
        processed_records = 0
        recommendations_count = 0
        
        # Process recent CSV files (last 24 hours or all if forced)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for obj in response['Contents']:
            key = obj['Key']
            last_modified = obj['LastModified'].replace(tzinfo=None)
            
            # Skip non-CSV files and old files
            if not key.endswith('.csv') or 'Manifest' in key:
                continue
                
            # Process recent files or if forced
            if last_modified > cutoff_time or event.get('detail', {}).get('processAllFiles', False):
                logger.info(f"Processing scheduled file: {key}")
                
                # Process this file
                usage_data = process_cur_file(bucket_name, key)
                processed_records += len(usage_data)
                
                if usage_data:
                    # Store usage data
                    store_usage_data(usage_data)
                    
                    # Generate recommendations
                    recommendations = analyze_waste_patterns(usage_data)
                    recommendations_count += len(recommendations)
                    
                    # Store recommendations
                    store_recommendations(recommendations)
        
        logger.info(f"Scheduled processing completed: {processed_records} records, {recommendations_count} recommendations")
        return processed_records, recommendations_count
        
    except Exception as e:
        logger.error(f"Error in scheduled processing: {str(e)}")
        return 0, 0

def process_s3_event(event):
    """Process S3 events (original functionality)"""
    processed_records = 0
    recommendations_count = 0
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        logger.info(f"Processing S3 event file: {key}")
        
        # Skip manifest files
        if 'Manifest' in key or key.endswith('.json'):
            logger.info("Skipping manifest file")
            continue
        
        # Process CUR data
        usage_data = process_cur_file(bucket, key)
        processed_records += len(usage_data)
        
        if usage_data:
            # Store usage data
            store_usage_data(usage_data)
            
            # Generate recommendations
            recommendations = analyze_waste_patterns(usage_data)
            recommendations_count += len(recommendations)
            
            # Store recommendations
            store_recommendations(recommendations)
    
    return processed_records, recommendations_count

def process_cur_file(bucket, key):
    """Process Cost and Usage Report file from S3"""
    try:
        logger.info(f"Processing file: {key} from bucket: {bucket}")
        
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        
        # Handle gzipped files
        if key.endswith('.gz'):
            content = gzip.decompress(response['Body'].read()).decode('utf-8')
        else:
            content = response['Body'].read().decode('utf-8')
        
        # Parse CSV data with enhanced error handling
        lines = content.splitlines()
        logger.info(f"File has {len(lines)} lines")
        
        if len(lines) < 2:
            logger.warning(f"File {key} has insufficient data")
            return []
        
        csv_reader = csv.DictReader(lines)
        usage_data = []
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Support both AWS CUR format and simplified format
                resource_data = {
                    'resource_id': (row.get('lineItem/ResourceId') or row.get('ResourceId') or f'unknown-{uuid.uuid4().hex[:8]}'),
                    'service_type': (row.get('product/ProductName') or row.get('ProductName') or 'Unknown Service'),
                    'usage_type': (row.get('lineItem/UsageType') or row.get('UsageType') or 'Unknown Usage'),
                    'usage_amount': float(row.get('lineItem/UsageAmount') or row.get('UsageAmount') or 0),
                    'unblended_cost': float(row.get('lineItem/UnblendedCost') or row.get('UnblendedCost') or 0),
                    'usage_start_date': (row.get('lineItem/UsageStartDate') or row.get('UsageStartDate') or ''),
                    'usage_end_date': (row.get('lineItem/UsageEndDate') or row.get('UsageEndDate') or ''),
                    'availability_zone': (row.get('lineItem/AvailabilityZone') or row.get('AvailabilityZone') or 'ap-south-1a'),
                    'instance_type': (row.get('product/instanceType') or row.get('instanceType') or 'unknown'),
                    'operation': (row.get('lineItem/Operation') or row.get('Operation') or 'unknown'),
                    'region': (row.get('product/region') or row.get('region') or 'ap-south-1'),
                    'timestamp': datetime.now().isoformat(),
                    'processed_date': datetime.now().strftime('%Y-%m-%d'),
                    'file_source': key
                }
                
                # Only include records with actual usage or cost
                if resource_data['usage_amount'] > 0 or resource_data['unblended_cost'] > 0:
                    usage_data.append(resource_data)
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row {row_num} in {key}: {e}")
                continue
        
        logger.info(f"Successfully processed {len(usage_data)} valid usage records from {key}")
        return usage_data
        
    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}")
        return []

def store_usage_data(usage_data):
    """Store processed usage data with improved batch processing"""
    try:
        with usage_table.batch_writer() as batch:
            for record in usage_data:
                # Convert floats to Decimal for DynamoDB
                item = {
                    'resource_id': record['resource_id'],
                    'timestamp': record['timestamp'],
                    'service_type': record['service_type'],
                    'usage_type': record['usage_type'],
                    'usage_amount': Decimal(str(record['usage_amount'])),
                    'unblended_cost': Decimal(str(record['unblended_cost'])),
                    'usage_start_date': record['usage_start_date'],
                    'usage_end_date': record['usage_end_date'],
                    'availability_zone': record['availability_zone'],
                    'instance_type': record['instance_type'],
                    'operation': record['operation'],
                    'region': record['region'],
                    'processed_date': record['processed_date'],
                    'file_source': record['file_source']
                }
                batch.put_item(Item=item)
        
        logger.info(f"Successfully stored {len(usage_data)} usage records in DynamoDB")
        
    except Exception as e:
        logger.error(f"Error storing usage data: {str(e)}")

def analyze_waste_patterns(usage_data):
    """Enhanced waste detection with sophisticated algorithms"""
    recommendations = []
    
    # Group usage data by resource for analysis
    resource_usage = {}
    
    for record in usage_data:
        resource_id = record['resource_id']
        if resource_id not in resource_usage:
            resource_usage[resource_id] = {
                'service_type': record['service_type'],
                'total_cost': 0,
                'usage_records': [],
                'instance_type': record['instance_type'],
                'availability_zone': record['availability_zone'],
                'total_usage': 0
            }
        
        resource_usage[resource_id]['total_cost'] += record['unblended_cost']
        resource_usage[resource_id]['total_usage'] += record['usage_amount']
        resource_usage[resource_id]['usage_records'].append(record)
    
    # Enhanced waste detection algorithms
    for resource_id, usage in resource_usage.items():
        
        # Skip very low-cost resources
        if usage['total_cost'] < 0.01:
            continue
            
        wastage_score = 0
        recommendation_details = []
        priority = 'Low'
        
        # Algorithm 1: EC2 Low Utilization Detection
        if 'EC2' in usage['service_type'] or 'Compute' in usage['service_type']:
            avg_usage = usage['total_usage'] / len(usage['usage_records']) if usage['usage_records'] else 0
            
            if avg_usage < 5:  # Very low utilization
                wastage_score += 40
                recommendation_details.append("Critical: Very low EC2 utilization detected")
                priority = 'High'
            elif avg_usage < 20:  # Low utilization
                wastage_score += 25
                recommendation_details.append("Low EC2 utilization - consider downsizing")
                priority = 'Medium'
        
        # Algorithm 2: Storage Optimization
        if 'Storage' in usage['service_type'] or 'EBS' in usage['service_type']:
            if usage['total_cost'] > 1.0:
                wastage_score += 30
                recommendation_details.append("High storage costs - review utilization")
                priority = 'High' if priority == 'Low' else priority
        
        # Algorithm 3: Regional Optimization
        if usage['availability_zone'] != 'ap-south-1a':
            wastage_score += 10
            recommendation_details.append("Resource in non-primary AZ")
        
        # Create recommendation if wastage detected
        if wastage_score > 0:
            savings_percentage = min(wastage_score / 100, 0.8)
            estimated_savings = round(usage['total_cost'] * savings_percentage, 2)
            
            recommendation = {
                'recommendation_id': f"rec-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
                'resource_id': resource_id,
                'service_type': usage['service_type'],
                'wastage_score': wastage_score,
                'estimated_savings': estimated_savings,
                'estimated_monthly_savings': estimated_savings * 30,
                'recommendations': recommendation_details,
                'current_cost': usage['total_cost'],
                'instance_type': usage['instance_type'],
                'availability_zone': usage['availability_zone'],
                'priority': priority,
                'created_at': datetime.now().isoformat(),
                'status': 'Active',
                'confidence_score': min(wastage_score / 10, 10),
                'total_usage': usage['total_usage']
            }
            recommendations.append(recommendation)
    
    logger.info(f"Generated {len(recommendations)} waste recommendations")
    return recommendations

def store_recommendations(recommendations):
    """Store recommendations with enhanced metadata"""
    try:
        with recommendations_table.batch_writer() as batch:
            for rec in recommendations:
                # Convert floats to Decimal for DynamoDB
                item = {
                    'recommendation_id': rec['recommendation_id'],
                    'created_at': rec['created_at'],
                    'resource_id': rec['resource_id'],
                    'service_type': rec['service_type'],
                    'wastage_score': Decimal(str(rec['wastage_score'])),
                    'estimated_savings': Decimal(str(rec['estimated_savings'])),
                    'estimated_monthly_savings': Decimal(str(rec['estimated_monthly_savings'])),
                    'recommendations': rec['recommendations'],
                    'current_cost': Decimal(str(rec['current_cost'])),
                    'instance_type': rec['instance_type'],
                    'availability_zone': rec['availability_zone'],
                    'priority': rec['priority'],
                    'status': rec['status'],
                    'confidence_score': Decimal(str(rec['confidence_score'])),
                    'total_usage': Decimal(str(rec['total_usage']))
                }
                batch.put_item(Item=item)
        
        logger.info(f"Successfully stored {len(recommendations)} recommendations in DynamoDB")
        
    except Exception as e:
        logger.error(f"Error storing recommendations: {str(e)}")

def test_with_sample_data():
    """Enhanced test function with comprehensive sample data"""
    sample_data = [
        {
            'resource_id': 'i-0123456789abcdef0',
            'service_type': 'Amazon Elastic Compute Cloud',
            'usage_type': 'BoxUsage:t3.micro',
            'usage_amount': 24.0,
            'unblended_cost': 0.50,
            'usage_start_date': '2025-06-22T00:00:00Z',
            'usage_end_date': '2025-06-22T24:00:00Z',
            'availability_zone': 'ap-south-1a',
            'instance_type': 't3.micro',
            'operation': 'RunInstances',
            'region': 'ap-south-1',
            'timestamp': datetime.now().isoformat(),
            'processed_date': datetime.now().strftime('%Y-%m-%d'),
            'file_source': 'test-data'
        }
    ]
    
    logger.info("Testing with enhanced sample data...")
    store_usage_data(sample_data)
    recommendations = analyze_waste_patterns(sample_data)
    store_recommendations(recommendations)
    
    return len(sample_data), len(recommendations)