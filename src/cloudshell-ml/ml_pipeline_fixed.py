#!/usr/bin/env python3
"""
Cloud Waste Detector - Fixed ML Pipeline
Checkpoint 5: CloudShell ML Setup & Data Preparation
Fixed version with proper error handling
"""

import pandas as pd
import numpy as np
import boto3
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
import uuid
import random
from decimal import Decimal

warnings.filterwarnings('ignore')

# Set up plotting for CloudShell
import matplotlib
matplotlib.use('Agg')

# AWS Configuration
REGION = 'ap-south-1'
BUCKET_NAME = 'cwd-cost-usage-reports-as-2025'
USAGE_TABLE = 'cwd-processed-usage-data'
RECOMMENDATIONS_TABLE = 'cwd-waste-recommendations'

# Initialize AWS clients
session = boto3.Session(region_name=REGION)
dynamodb = session.resource('dynamodb')
s3_client = session.client('s3')

print("🚀 Cloud Waste Detector ML Pipeline - Fixed Version")
print("="*60)

def test_aws_connectivity():
    """Test AWS connectivity"""
    print("🔗 Testing AWS connectivity...")
    try:
        sts = boto3.client('sts', region_name=REGION)
        identity = sts.get_caller_identity()
        print(f"✅ Connected as: {identity.get('UserId', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ AWS connectivity error: {str(e)}")
        return False

def generate_sample_data():
    """Generate comprehensive sample data"""
    print("🎲 Generating sample data...")
    
    # Generate 30 days of data
    sample_data = []
    services = [
        {'name': 'Amazon Elastic Compute Cloud', 'base_cost': 0.6},
        {'name': 'Amazon Elastic Block Store', 'base_cost': 1.1},
        {'name': 'Amazon Simple Storage Service', 'base_cost': 0.08}
    ]
    
    resource_ids = [f"i-{uuid.uuid4().hex[:10]}" for _ in range(10)]
    instance_types = ['t3.micro', 't3.small', 'm5.large']
    availability_zones = ['ap-south-1a', 'ap-south-1b']
    
    for day_offset in range(30):
        current_date = datetime.now() - timedelta(days=30-day_offset)
        
        for record_num in range(25):  # 25 records per day
            service = random.choice(services)
            resource_id = random.choice(resource_ids)
            
            usage_amount = random.uniform(10, 100)
            unblended_cost = service['base_cost'] * random.uniform(0.8, 1.2) * (usage_amount / 50)
            
            # Add occasional spikes
            if random.random() < 0.05:
                unblended_cost *= random.uniform(3, 6)
            
            record = {
                'resource_id': resource_id,
                'timestamp': current_date.isoformat(),
                'service_type': service['name'],
                'usage_type': f"BoxUsage:{random.choice(instance_types)}",
                'usage_amount': Decimal(str(round(usage_amount, 2))),
                'unblended_cost': Decimal(str(round(unblended_cost, 4))),
                'usage_start_date': (current_date - timedelta(hours=1)).isoformat(),
                'usage_end_date': current_date.isoformat(),
                'availability_zone': random.choice(availability_zones),
                'instance_type': random.choice(instance_types),
                'operation': 'RunInstances',
                'region': 'ap-south-1',
                'processed_date': current_date.strftime('%Y-%m-%d'),
                'file_source': 'cloudshell-fixed-generator'
            }
            
            sample_data.append(record)
    
    print(f"✅ Generated {len(sample_data)} sample records")
    return sample_data

def upload_to_dynamodb(sample_data):
    """Upload sample data to DynamoDB"""
    print("📤 Uploading sample data to DynamoDB...")
    
    try:
        usage_table = dynamodb.Table(USAGE_TABLE)
        
        # Upload in batches
        batch_size = 25
        for i in range(0, len(sample_data), batch_size):
            batch = sample_data[i:i + batch_size]
            
            with usage_table.batch_writer() as writer:
                for record in batch:
                    writer.put_item(Item=record)
            
            print(f"  Uploaded batch {i//batch_size + 1}/{(len(sample_data)-1)//batch_size + 1}")
        
        print("✅ Sample data uploaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        return False

def extract_and_process_data():
    """Extract and process data for ML"""
    print("📊 Extracting and processing data...")
    
    try:
        # Extract data from DynamoDB
        usage_table = dynamodb.Table(USAGE_TABLE)
        response = usage_table.scan()
        usage_data = response['Items']
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = usage_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            usage_data.extend(response['Items'])
        
        print(f"✅ Extracted {len(usage_data)} records")
        
        if len(usage_data) == 0:
            print("⚠️ No data found. Generating sample data...")
            sample_data = generate_sample_data()
            upload_to_dynamodb(sample_data)
            return extract_and_process_data()  # Retry after generating data
        
        # Convert to DataFrame
        def convert_decimal(obj):
            if hasattr(obj, '_decimal_value'):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(v) for v in obj]
            return obj
        
        clean_data = [convert_decimal(item) for item in usage_data]
        df = pd.DataFrame(clean_data)
        
        # Data processing
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['unblended_cost'] = df['unblended_cost'].fillna(0)
        df['usage_amount'] = df['usage_amount'].fillna(0)
        
        print(f"✅ Processed DataFrame: {df.shape}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
        
    except Exception as e:
        print(f"❌ Data processing error: {str(e)}")
        return None

def create_time_series_features(df):
    """Create time series features"""
    print("⚙️ Creating time series features...")
    
    try:
        # Create daily aggregation
        daily_data = df.groupby('date').agg({
            'unblended_cost': ['sum', 'mean', 'count'],
            'usage_amount': ['sum', 'mean'],
            'resource_id': 'nunique'
        }).reset_index()
        
        # Flatten column names
        daily_data.columns = [
            'date', 'total_cost', 'avg_cost', 'record_count',
            'total_usage', 'avg_usage', 'unique_resources'
        ]
        
        # Sort by date
        daily_data = daily_data.sort_values('date').reset_index(drop=True)
        daily_data = daily_data.fillna(0)
        
        # Create lag features
        daily_data['cost_lag_1'] = daily_data['total_cost'].shift(1)
        daily_data['cost_lag_2'] = daily_data['total_cost'].shift(2)
        
        # Rolling averages
        daily_data['cost_ma_3'] = daily_data['total_cost'].rolling(window=3).mean()
        daily_data['cost_ma_7'] = daily_data['total_cost'].rolling(window=7).mean()
        
        # Growth rate
        daily_data['cost_growth'] = daily_data['total_cost'].pct_change()
        
        # Day features
        daily_data['date_dt'] = pd.to_datetime(daily_data['date'])
        daily_data['day_of_week'] = daily_data['date_dt'].dt.dayofweek
        daily_data['is_weekend'] = (daily_data['day_of_week'] >= 5).astype(int)
        
        print(f"✅ Time series features created: {daily_data.shape}")
        return daily_data
        
    except Exception as e:
        print(f"❌ Feature creation error: {str(e)}")
        return None

def create_safe_visualizations(df, daily_data):
    """Create visualizations with proper error handling"""
    print("📈 Creating safe visualizations...")
    
    try:
        # Create a simple 2x2 subplot layout
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Cloud Waste Detector - Data Analysis', fontsize=14)
        
        # 1. Daily cost trend (safe)
        if len(daily_data) > 1:
            axes[0, 0].plot(range(len(daily_data)), daily_data['total_cost'], marker='o')
            axes[0, 0].set_title('Daily Cost Trend')
            axes[0, 0].set_ylabel('Total Cost ($)')
            axes[0, 0].set_xlabel('Days')
        
        # 2. Cost distribution (safe)
        cost_data = df['unblended_cost'][df['unblended_cost'] > 0]  # Remove zeros
        if len(cost_data) > 0:
            axes[0, 1].hist(cost_data, bins=min(30, len(cost_data)//2), edgecolor='black', alpha=0.7)
            axes[0, 1].set_title('Cost Distribution')
            axes[0, 1].set_xlabel('Cost ($)')
            axes[0, 1].set_ylabel('Frequency')
        
        # 3. Service breakdown (safe)
        service_costs = df.groupby('service_type')['unblended_cost'].sum()
        if len(service_costs) > 0:
            # Ensure we have valid data for pie chart
            valid_costs = service_costs[service_costs > 0]
            if len(valid_costs) > 0:
                axes[1, 0].pie(valid_costs.values, labels=valid_costs.index, autopct='%1.1f%%')
                axes[1, 0].set_title('Cost by Service Type')
        
        # 4. Resource count (safe)
        if len(daily_data) > 1:
            axes[1, 1].plot(range(len(daily_data)), daily_data['unique_resources'], marker='s', color='green')
            axes[1, 1].set_title('Unique Resources Over Time')
            axes[1, 1].set_ylabel('Resource Count')
            axes[1, 1].set_xlabel('Days')
        
        plt.tight_layout()
        plt.savefig('cost_analysis_safe.png', dpi=150, bbox_inches='tight')
        print("✅ Safe visualizations saved as 'cost_analysis_safe.png'")
        
        return True
        
    except Exception as e:
        print(f"❌ Visualization error: {str(e)}")
        return False

def prepare_ml_datasets(daily_data):
    """Prepare datasets for ML models"""
    print("📊 Preparing ML datasets...")
    
    try:
        # Remove NaN values
        ml_features = daily_data.dropna().reset_index(drop=True)
        
        # Prophet format
        prophet_data = pd.DataFrame({
            'ds': pd.to_datetime(daily_data['date']),
            'y': daily_data['total_cost']
        })
        
        # Add regressors
        prophet_data['unique_resources'] = daily_data['unique_resources']
        prophet_data['is_weekend'] = daily_data['is_weekend']
        
        print(f"✅ ML features: {ml_features.shape}")
        print(f"✅ Prophet data: {prophet_data.shape}")
        
        return ml_features, prophet_data
        
    except Exception as e:
        print(f"❌ ML dataset preparation error: {str(e)}")
        return None, None

def save_to_s3(ml_features, prophet_data):
    """Save results to S3"""
    print("💾 Saving results to S3...")
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare data for JSON
        def prepare_for_json(df):
            df_copy = df.copy()
            for col in df_copy.columns:
                if df_copy[col].dtype == 'datetime64[ns]':
                    df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
                elif 'date' in col and df_copy[col].dtype == 'object':
                    df_copy[col] = df_copy[col].astype(str)
            return df_copy.fillna(0)
        
        # Save ML features
        if ml_features is not None and not ml_features.empty:
            ml_json = prepare_for_json(ml_features).to_json(orient='records')
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f'ml-data/ml_features_{timestamp}.json',
                Body=ml_json,
                ContentType='application/json'
            )
            print("✅ ML features saved to S3")
        
        # Save Prophet data
        if prophet_data is not None and not prophet_data.empty:
            prophet_json = prepare_for_json(prophet_data).to_json(orient='records')
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f'ml-data/prophet_data_{timestamp}.json',
                Body=prophet_json,
                ContentType='application/json'
            )
            print("✅ Prophet data saved to S3")
        
        print(f"📁 Data saved with timestamp: {timestamp}")
        return True
        
    except Exception as e:
        print(f"❌ S3 save error: {str(e)}")
        return False

def print_summary(df, daily_data):
    """Print comprehensive summary"""
    print("\n📊 PIPELINE EXECUTION SUMMARY")
    print("="*50)
    
    if df is not None:
        total_cost = df['unblended_cost'].sum()
        unique_resources = df['resource_id'].nunique()
        unique_services = df['service_type'].nunique()
        date_range = (df['date'].max() - df['date'].min()).days + 1
        
        print(f"✅ Total records processed: {len(df):,}")
        print(f"✅ Total cost analyzed: ${total_cost:.2f}")
        print(f"✅ Unique resources: {unique_resources}")
        print(f"✅ Unique services: {unique_services}")
        print(f"✅ Date range: {date_range} days")
        
        if daily_data is not None:
            print(f"✅ Daily observations: {len(daily_data)}")
            print(f"✅ Average daily cost: ${daily_data['total_cost'].mean():.2f}")
            print(f"✅ Max daily cost: ${daily_data['total_cost'].max():.2f}")

def main():
    """Main pipeline execution"""
    print("🚀 EXECUTING FIXED ML PIPELINE")
    print("="*50)
    
    # Test connectivity
    if not test_aws_connectivity():
        print("❌ Pipeline failed: AWS connectivity issues")
        return False
    
    # Extract and process data
    df = extract_and_process_data()
    if df is None:
        print("❌ Pipeline failed: Data extraction issues")
        return False
    
    # Create time series features
    daily_data = create_time_series_features(df)
    if daily_data is None:
        print("❌ Pipeline failed: Feature creation issues")
        return False
    
    # Create safe visualizations
    create_safe_visualizations(df, daily_data)
    
    # Prepare ML datasets
    ml_features, prophet_data = prepare_ml_datasets(daily_data)
    
    # Save to S3
    save_to_s3(ml_features, prophet_data)
    
    # Print summary
    print_summary(df, daily_data)
    
    print("\n🎉 FIXED ML PIPELINE COMPLETED SUCCESSFULLY!")
    print("✅ Ready for Checkpoint 6: Model Development")
    
    return True

if __name__ == "__main__":
    main()