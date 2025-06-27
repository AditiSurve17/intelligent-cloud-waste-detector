#!/usr/bin/env python3
"""
Generate Missing ML Data Types
Ensures all required ML datasets are created and saved to S3
"""

import pandas as pd
import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np

# AWS Configuration
REGION = 'ap-south-1'
BUCKET_NAME = 'cwd-cost-usage-reports-as-2025'
USAGE_TABLE = 'cwd-processed-usage-data'

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)

print("🔧 GENERATING MISSING ML DATA TYPES")
print("="*50)

def extract_and_process_data():
    """Extract data from DynamoDB and process for ML"""
    print("📊 Extracting data from DynamoDB...")
    
    try:
        usage_table = dynamodb.Table(USAGE_TABLE)
        response = usage_table.scan()
        usage_data = response['Items']
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = usage_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            usage_data.extend(response['Items'])
        
        print(f"✅ Extracted {len(usage_data)} records")
        
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
        
        # Basic processing
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['unblended_cost'] = df['unblended_cost'].fillna(0)
        df['usage_amount'] = df['usage_amount'].fillna(0)
        
        print(f"✅ Processed DataFrame: {df.shape}")
        return df
        
    except Exception as e:
        print(f"❌ Data extraction failed: {e}")
        return None

def create_comprehensive_features(df):
    """Create comprehensive ML features"""
    print("⚙️ Creating comprehensive ML features...")
    
    try:
        # Daily aggregation
        daily_data = df.groupby('date').agg({
            'unblended_cost': ['sum', 'mean', 'count', 'std', 'min', 'max'],
            'usage_amount': ['sum', 'mean', 'std'],
            'resource_id': 'nunique',
            'service_type': 'nunique'
        }).reset_index()
        
        # Flatten column names
        daily_data.columns = [
            'date', 'total_cost', 'avg_cost', 'record_count', 'cost_std', 'min_cost', 'max_cost',
            'total_usage', 'avg_usage', 'usage_std', 'unique_resources', 'unique_services'
        ]
        
        # Sort by date and fill NaN
        daily_data = daily_data.sort_values('date').reset_index(drop=True)
        daily_data = daily_data.fillna(0)
        
        # Create advanced time series features
        
        # 1. Lag features
        for lag in [1, 2, 3, 7]:
            daily_data[f'cost_lag_{lag}'] = daily_data['total_cost'].shift(lag)
            daily_data[f'usage_lag_{lag}'] = daily_data['total_usage'].shift(lag)
        
        # 2. Rolling statistics
        for window in [3, 7, 14]:
            daily_data[f'cost_ma_{window}'] = daily_data['total_cost'].rolling(window=window).mean()
            daily_data[f'cost_std_{window}'] = daily_data['total_cost'].rolling(window=window).std()
            daily_data[f'usage_ma_{window}'] = daily_data['total_usage'].rolling(window=window).mean()
        
        # 3. Growth rates and changes
        daily_data['cost_growth_1d'] = daily_data['total_cost'].pct_change()
        daily_data['cost_growth_3d'] = daily_data['total_cost'].pct_change(periods=3)
        daily_data['cost_growth_7d'] = daily_data['total_cost'].pct_change(periods=7)
        
        # 4. Cyclical features
        daily_data['date_dt'] = pd.to_datetime(daily_data['date'])
        daily_data['day_of_week'] = daily_data['date_dt'].dt.dayofweek
        daily_data['day_of_month'] = daily_data['date_dt'].dt.day
        daily_data['month'] = daily_data['date_dt'].dt.month
        daily_data['is_weekend'] = (daily_data['day_of_week'] >= 5).astype(int)
        daily_data['is_month_start'] = (daily_data['day_of_month'] <= 3).astype(int)
        daily_data['is_month_end'] = (daily_data['day_of_month'] >= 28).astype(int)
        
        # 5. Trend and seasonal features
        daily_data['days_since_start'] = (daily_data['date_dt'] - daily_data['date_dt'].min()).dt.days
        daily_data['cost_trend'] = daily_data['total_cost'].rolling(window=7).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 7 else 0, raw=False
        )
        
        # 6. Efficiency metrics
        daily_data['cost_per_resource'] = daily_data['total_cost'] / daily_data['unique_resources'].replace(0, 1)
        daily_data['cost_per_usage'] = daily_data['total_cost'] / daily_data['total_usage'].replace(0, 1)
        daily_data['usage_efficiency'] = daily_data['total_usage'] / daily_data['record_count'].replace(0, 1)
        
        # 7. Volatility measures
        daily_data['cost_volatility'] = daily_data['total_cost'].rolling(window=7).std() / daily_data['total_cost'].rolling(window=7).mean()
        
        print(f"✅ Created comprehensive features: {daily_data.shape}")
        print(f"✅ Total features: {len(daily_data.columns)}")
        
        return daily_data
        
    except Exception as e:
        print(f"❌ Feature creation failed: {e}")
        return None

def create_prophet_dataset(daily_data):
    """Create Prophet-specific dataset"""
    print("📊 Creating Prophet dataset...")
    
    try:
        # Basic Prophet format
        prophet_data = pd.DataFrame({
            'ds': pd.to_datetime(daily_data['date']),
            'y': daily_data['total_cost']
        })
        
        # Add additional regressors for Prophet
        prophet_data['unique_resources'] = daily_data['unique_resources']
        prophet_data['unique_services'] = daily_data['unique_services']
        prophet_data['is_weekend'] = daily_data['is_weekend']
        prophet_data['day_of_month'] = daily_data['day_of_month']
        prophet_data['month'] = daily_data['month']
        prophet_data['cost_ma_7'] = daily_data['cost_ma_7']
        prophet_data['usage_ma_7'] = daily_data['usage_ma_7']
        
        # Remove any NaN values for Prophet
        prophet_data = prophet_data.dropna().reset_index(drop=True)
        
        print(f"✅ Prophet dataset created: {prophet_data.shape}")
        return prophet_data
        
    except Exception as e:
        print(f"❌ Prophet dataset creation failed: {e}")
        return None

def create_arima_dataset(daily_data):
    """Create ARIMA-specific dataset"""
    print("📈 Creating ARIMA dataset...")
    
    try:
        # ARIMA needs a simple time series
        arima_data = daily_data[['date', 'total_cost']].copy()
        arima_data['date'] = pd.to_datetime(arima_data['date'])
        arima_data = arima_data.set_index('date').sort_index()
        
        # Ensure no missing values
        arima_data = arima_data.fillna(method='ffill').fillna(method='bfill')
        
        print(f"✅ ARIMA dataset created: {len(arima_data)} observations")
        return arima_data
        
    except Exception as e:
        print(f"❌ ARIMA dataset creation failed: {e}")
        return None

def save_all_datasets_to_s3(daily_features, prophet_data, arima_data):
    """Save all ML datasets to S3"""
    print("💾 Saving all ML datasets to S3...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_files = []
    
    def prepare_for_json(df):
        """Prepare DataFrame for JSON serialization"""
        df_copy = df.copy()
        for col in df_copy.columns:
            if df_copy[col].dtype == 'datetime64[ns]':
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
            elif 'date' in col and df_copy[col].dtype == 'object':
                df_copy[col] = df_copy[col].astype(str)
        return df_copy.fillna(0)
    
    try:
        # 1. Save comprehensive ML features
        if daily_features is not None and not daily_features.empty:
            ml_features_clean = daily_features.dropna().reset_index(drop=True)
            features_json = prepare_for_json(ml_features_clean).to_json(orient='records')
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f'ml-data/ml_features_{timestamp}.json',
                Body=features_json,
                ContentType='application/json'
            )
            saved_files.append(f'ml_features_{timestamp}.json')
            print("✅ ML features saved")
        
        # 2. Save Prophet data
        if prophet_data is not None and not prophet_data.empty:
            prophet_json = prepare_for_json(prophet_data).to_json(orient='records')
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f'ml-data/prophet_data_{timestamp}.json',
                Body=prophet_json,
                ContentType='application/json'
            )
            saved_files.append(f'prophet_data_{timestamp}.json')
            print("✅ Prophet data saved")
        
        # 3. Save ARIMA data
        if arima_data is not None and not arima_data.empty:
            arima_json = arima_data.to_json(date_format='iso')
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f'ml-data/arima_data_{timestamp}.json',
                Body=arima_json,
                ContentType='application/json'
            )
            saved_files.append(f'arima_data_{timestamp}.json')
            print("✅ ARIMA data saved")
        
        # 4. Save daily features (basic)
        if daily_features is not None and not daily_features.empty:
            daily_json = prepare_for_json(daily_features).to_json(orient='records')
            
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=f'ml-data/daily_features_{timestamp}.json',
                Body=daily_json,
                ContentType='application/json'
            )
            saved_files.append(f'daily_features_{timestamp}.json')
            print("✅ Daily features saved")
        
        # 5. Save metadata
        metadata = {
            'generation_timestamp': timestamp,
            'files_created': saved_files,
            'data_summary': {
                'daily_observations': len(daily_features) if daily_features is not None else 0,
                'prophet_observations': len(prophet_data) if prophet_data is not None else 0,
                'arima_observations': len(arima_data) if arima_data is not None else 0,
                'feature_count': len(daily_features.columns) if daily_features is not None else 0
            },
            'ml_readiness': {
                'prophet_ready': prophet_data is not None and len(prophet_data) >= 10,
                'arima_ready': arima_data is not None and len(arima_data) >= 20,
                'features_ready': daily_features is not None and len(daily_features) >= 15
            }
        }
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f'ml-data/metadata_{timestamp}.json',
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        saved_files.append(f'metadata_{timestamp}.json')
        print("✅ Metadata saved")
        
        print(f"\n📁 Successfully saved {len(saved_files)} files:")
        for file in saved_files:
            print(f"  - {file}")
        
        return True, saved_files
        
    except Exception as e:
        print(f"❌ S3 save failed: {e}")
        return False, []

def main():
    """Main execution function"""
    print("🚀 Starting comprehensive ML data generation...")
    
    # Extract and process data
    df = extract_and_process_data()
    if df is None:
        print("❌ Failed to extract data")
        return False
    
    # Create comprehensive features
    daily_features = create_comprehensive_features(df)
    if daily_features is None:
        print("❌ Failed to create features")
        return False
    
    # Create Prophet dataset
    prophet_data = create_prophet_dataset(daily_features)
    
    # Create ARIMA dataset
    arima_data = create_arima_dataset(daily_features)
    
    # Save all datasets
    success, files = save_all_datasets_to_s3(daily_features, prophet_data, arima_data)
    
    if success:
        print(f"\n🎉 ML DATA GENERATION COMPLETED SUCCESSFULLY!")
        print(f"✅ All required ML data types created")
        print(f"✅ Files saved to S3: ml-data/ folder")
        print(f"✅ Ready for Checkpoint 6: Model Development")
        return True
    else:
        print(f"\n❌ ML data generation failed")
        return False

if __name__ == "__main__":
    main()