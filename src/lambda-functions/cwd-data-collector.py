import json
import boto3
import csv
import gzip
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Initialize AWS services for ap-south-1 region
s3_client = boto3.client('s3', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

def lambda_handler(event, context):
    """
    Main Lambda function to collect and process Cost & Usage Report data
    Optimized for ap-south-1 (Mumbai) region
    """
    try:
        print(f"Starting CUR data collection in ap-south-1 at {datetime.now()}")
        
        # Configuration
        cur_bucket = get_cur_bucket_name()
        if not cur_bucket:
            return create_error_response("CUR bucket not found")
        
        # Process CUR files
        processed_files = process_cur_files(cur_bucket)
        
        # Store processed data
        storage_result = store_processed_data(processed_files)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'CUR data collection completed successfully',
                'region': 'ap-south-1',
                'files_processed': len(processed_files),
                'timestamp': datetime.now().isoformat(),
                'storage_result': storage_result
            })
        }
        
        print(f"Completed successfully in ap-south-1. Processed {len(processed_files)} files")
        return response
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return create_error_response(str(e))

def get_cur_bucket_name():
    """
    Find the S3 bucket containing Cost & Usage Reports in ap-south-1
    """
    try:
        # List all buckets and find the one with 'cur' or 'cost-usage-reports' in name
        response = s3_client.list_buckets()
        
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            if 'cost-usage-reports' in bucket_name or 'cur' in bucket_name:
                # Verify bucket is in ap-south-1
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket_name)
                    bucket_region = location.get('LocationConstraint', 'us-east-1')
                    if bucket_region == 'ap-south-1':
                        print(f"Found CUR bucket in ap-south-1: {bucket_name}")
                        return bucket_name
                except Exception as e:
                    print(f"Could not get location for bucket {bucket_name}: {str(e)}")
                    continue
        
        print("No CUR bucket found in ap-south-1")
        return None
        
    except Exception as e:
        print(f"Error finding CUR bucket: {str(e)}")
        return None

def process_cur_files(bucket_name: str) -> List[Dict]:
    """
    Process CUR files from S3 bucket
    """
    processed_files = []
    
    try:
        # List objects in the CUR bucket
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='cost-usage-reports/'
        )
        
        if 'Contents' not in response:
            print("No CUR files found yet - this is normal for the first 24 hours")
            return processed_files
        
        # Process each CSV file
        for obj in response['Contents']:
            key = obj['Key']
            
            # Only process CSV files
            if key.endswith('.csv.gz') or key.endswith('.csv'):
                print(f"Processing file: {key}")
                file_data = process_single_cur_file(bucket_name, key)
                if file_data:
                    processed_files.append(file_data)
                
                # Limit processing for free tier (process max 5 files per run)
                if len(processed_files) >= 5:
                    print("Reached processing limit for free tier")
                    break
        
        return processed_files
        
    except Exception as e:
        print(f"Error processing CUR files: {str(e)}")
        return processed_files

def process_single_cur_file(bucket_name: str, key: str) -> Dict:
    """
    Process a single CUR file and extract key metrics
    """
    try:
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        file_content = response['Body'].read()
        
        # Handle gzipped files
        if key.endswith('.gz'):
            file_content = gzip.decompress(file_content)
        
        # Parse CSV content
        csv_content = file_content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        # Extract key metrics
        usage_data = []
        total_cost = 0
        service_costs = {}
        resource_usage = {}
        ap_south_1_costs = 0  # Track costs specific to ap-south-1
        
        for row in csv_reader:
            # Basic validation
            if not row.get('lineItem/UsageStartDate'):
                continue
            
            # Extract key information
            service = row.get('product/ProductName', 'Unknown')
            cost = float(row.get('lineItem/BlendedCost', 0))
            usage_amount = float(row.get('lineItem/UsageAmount', 0))
            resource_id = row.get('lineItem/ResourceId', '')
            usage_type = row.get('lineItem/UsageType', '')
            availability_zone = row.get('lineItem/AvailabilityZone', '')
            
            # Track ap-south-1 specific costs
            if 'ap-south-1' in availability_zone or 'aps1' in usage_type:
                ap_south_1_costs += cost
            
            # Aggregate data
            total_cost += cost
            service_costs[service] = service_costs.get(service, 0) + cost
            
            if resource_id:
                resource_usage[resource_id] = {
                    'service': service,
                    'usage_type': usage_type,
                    'usage_amount': usage_amount,
                    'cost': cost,
                    'availability_zone': availability_zone,
                    'last_updated': row.get('lineItem/UsageStartDate')
                }
            
            # Store individual usage record (limit for free tier)
            if len(usage_data) < 1000:  # Limit to prevent memory issues
                usage_data.append({
                    'timestamp': row.get('lineItem/UsageStartDate'),
                    'service': service,
                    'usage_type': usage_type,
                    'usage_amount': usage_amount,
                    'cost': cost,
                    'resource_id': resource_id,
                    'availability_zone': availability_zone
                })
        
        return {
            'file_key': key,
            'total_cost': total_cost,
            'ap_south_1_costs': ap_south_1_costs,
            'service_costs': service_costs,
            'resource_usage': resource_usage,
            'usage_data': usage_data,
            'processed_at': datetime.now().isoformat(),
            'region': 'ap-south-1'
        }
        
    except Exception as e:
        print(f"Error processing file {key}: {str(e)}")
        return None

def store_processed_data(processed_files: List[Dict]) -> Dict:
    """
    Store processed data (for now, just return summary)
    In next checkpoint, we'll store this in DynamoDB
    """
    try:
        total_files = len(processed_files)
        total_cost = sum(file_data['total_cost'] for file_data in processed_files)
        total_ap_south_costs = sum(file_data.get('ap_south_1_costs', 0) for file_data in processed_files)
        total_records = sum(len(file_data['usage_data']) for file_data in processed_files)
        
        # Aggregate service costs across all files
        all_service_costs = {}
        for file_data in processed_files:
            for service, cost in file_data['service_costs'].items():
                all_service_costs[service] = all_service_costs.get(service, 0) + cost
        
        summary = {
            'total_files_processed': total_files,
            'total_cost': round(total_cost, 4),
            'ap_south_1_costs': round(total_ap_south_costs, 4),
            'total_records': total_records,
            'top_services': sorted(all_service_costs.items(), 
                                 key=lambda x: x[1], reverse=True)[:5],
            'processing_timestamp': datetime.now().isoformat(),
            'region': 'ap-south-1'
        }
        
        print(f"Data summary for ap-south-1: {json.dumps(summary, indent=2)}")
        return summary
        
    except Exception as e:
        print(f"Error storing processed data: {str(e)}")
        return {'error': str(e)}

def create_error_response(error_message: str) -> Dict:
    """
    Create standardized error response
    """
    return {
        'statusCode': 500,
        'body': json.dumps({
            'error': error_message,
            'region': 'ap-south-1',
            'timestamp': datetime.now().isoformat()
        })
    }

# Regional optimization function
def optimize_for_mumbai_region():
    """
    Apply optimizations specific to ap-south-1 region
    """
    optimizations = {
        'region': 'ap-south-1',
        'timezone': 'Asia/Kolkata',
        'data_residency': 'India',
        'latency_optimized': True
    }
    return optimizations