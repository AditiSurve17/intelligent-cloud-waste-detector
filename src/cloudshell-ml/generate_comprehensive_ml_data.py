#!/usr/bin/env python3
"""
Enhanced ML Data Generator for Prophet & ARIMA Training
Generates 45+ days of realistic AWS usage patterns
Region: ap-south-1 (Mumbai)
"""

import pandas as pd
import numpy as np
import boto3
import json
from datetime import datetime, timedelta
import random
import warnings
warnings.filterwarnings('ignore')

print("🚀 Generating Comprehensive ML Training Data...")
print("📍 Region: ap-south-1 (Mumbai)")
print("🎯 Target: 45+ days of realistic AWS usage patterns")

# AWS Configuration
s3_client = boto3.client('s3', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
bucket_name = 'cwd-cost-usage-reports-as-2025'

def generate_realistic_aws_costs(days=45):
    """Generate realistic AWS cost patterns"""
    print(f"\n📊 Generating {days} days of AWS usage data...")
    
    # Base configuration for realistic patterns
    base_daily_cost = 2.50  # Typical small business AWS daily spend
    
    # Create date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    cost_data = []
    
    for i, date in enumerate(date_range):
        # Realistic cost patterns
        
        # 1. Base growth trend (3% monthly growth)
        growth_factor = 1 + (0.03 * i / 30)
        
        # 2. Weekly seasonality (lower costs on weekends)
        weekday = date.weekday()
        if weekday >= 5:  # Weekend
            weekend_factor = 0.7  # 30% lower on weekends
        else:
            weekend_factor = 1.0
        
        # 3. Monthly patterns (higher at month start/end)
        day_of_month = date.day
        if day_of_month <= 3 or day_of_month >= 28:
            monthly_factor = 1.2  # 20% higher at month boundaries
        else:
            monthly_factor = 1.0
        
        # 4. Random daily variation (±25%)
        random_factor = np.random.normal(1.0, 0.15)
        random_factor = max(0.5, min(1.5, random_factor))  # Cap variation
        
        # 5. Occasional cost spikes (simulating scaling events)
        if np.random.random() < 0.1:  # 10% chance
            spike_factor = np.random.uniform(1.5, 2.5)
        else:
            spike_factor = 1.0
        
        # Calculate final cost
        daily_cost = (base_daily_cost * growth_factor * weekend_factor * 
                     monthly_factor * random_factor * spike_factor)
        
        # Ensure minimum cost
        daily_cost = max(0.50, daily_cost)
        
        cost_data.append({
            'date': date,
            'cost': round(daily_cost, 2),
            'weekday': weekday,
            'weekend': 1 if weekday >= 5 else 0,
            'month_start': 1 if day_of_month <= 3 else 0,
            'month_end': 1 if day_of_month >= 28 else 0,
            'growth_factor': growth_factor,
            'spike_event': 1 if spike_factor > 1.2 else 0
        })
    
    df = pd.DataFrame(cost_data)
    print(f"✅ Generated {len(df)} days of cost data")
    print(f"💰 Cost range: ${df['cost'].min():.2f} - ${df['cost'].max():.2f}")
    print(f"📈 Average daily cost: ${df['cost'].mean():.2f}")
    
    return df

def create_prophet_format(df):
    """Convert to Prophet format (ds, y columns)"""
    print("\n🔮 Creating Prophet-formatted dataset...")
    
    prophet_data = []
    for _, row in df.iterrows():
        prophet_data.append({
            'ds': row['date'].strftime('%Y-%m-%d'),
            'y': row['cost'],
            'weekend': row['weekend'],
            'month_start': row['month_start'],
            'month_end': row['month_end'],
            'spike_event': row['spike_event']
        })
    
    print(f"✅ Prophet format ready: {len(prophet_data)} observations")
    return prophet_data

def create_arima_format(df):
    """Convert to ARIMA format (time series)"""
    print("\n📊 Creating ARIMA-formatted dataset...")
    
    arima_data = []
    for _, row in df.iterrows():
        arima_data.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'value': row['cost'],
            'timestamp': int(row['date'].timestamp())
        })
    
    print(f"✅ ARIMA format ready: {len(arima_data)} time series points")
    return arima_data

def create_feature_engineering(df):
    """Create comprehensive feature set"""
    print("\n🛠️ Engineering comprehensive features...")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    features = []
    for i, row in df.iterrows():
        feature_set = {
            'date': row['date'].strftime('%Y-%m-%d'),
            'cost': row['cost'],
            
            # Basic features
            'weekday': row['weekday'],
            'weekend': row['weekend'],
            'month_start': row['month_start'],
            'month_end': row['month_end'],
            'day_of_month': row['date'].day,
            'month': row['date'].month,
            
            # Lag features (previous days)
            'cost_lag_1': df.iloc[i-1]['cost'] if i > 0 else row['cost'],
            'cost_lag_2': df.iloc[i-2]['cost'] if i > 1 else row['cost'],
            'cost_lag_3': df.iloc[i-3]['cost'] if i > 2 else row['cost'],
            'cost_lag_7': df.iloc[i-7]['cost'] if i > 6 else row['cost'],
            
            # Rolling averages
            'cost_ma_3': df.iloc[max(0, i-2):i+1]['cost'].mean(),
            'cost_ma_7': df.iloc[max(0, i-6):i+1]['cost'].mean(),
            'cost_ma_14': df.iloc[max(0, i-13):i+1]['cost'].mean(),
            
            # Growth rates
            'growth_1d': ((row['cost'] / df.iloc[i-1]['cost']) - 1) * 100 if i > 0 else 0,
            'growth_7d': ((row['cost'] / df.iloc[i-7]['cost']) - 1) * 100 if i > 6 else 0,
            
            # Volatility measures
            'volatility_7d': df.iloc[max(0, i-6):i+1]['cost'].std(),
            'cost_cv': df.iloc[max(0, i-6):i+1]['cost'].std() / df.iloc[max(0, i-6):i+1]['cost'].mean() if i > 0 else 0,
            
            # Anomaly indicators
            'spike_event': row['spike_event'],
            'cost_zscore': (row['cost'] - df.iloc[max(0, i-13):i+1]['cost'].mean()) / 
                          df.iloc[max(0, i-13):i+1]['cost'].std() if i > 13 else 0
        }
        
        features.append(feature_set)
    
    print(f"✅ Feature engineering completed: {len(features[0])} features per observation")
    return features

def save_to_s3(data, filename, description):
    """Save data to S3"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    key = f'ml-data/{filename}_{timestamp}.json'
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(data, indent=2, default=str),
        ContentType='application/json'
    )
    
    print(f"✅ {description} saved: s3://{bucket_name}/{key}")
    return key

def create_metadata(prophet_data, arima_data, features):
    """Create metadata about the generated datasets"""
    metadata = {
        'generation_timestamp': datetime.now().isoformat(),
        'data_quality': 'A_GRADE',
        'prophet_observations': len(prophet_data),
        'arima_observations': len(arima_data),
        'feature_count': len(features[0]) if features else 0,
        'date_range': {
            'start': prophet_data[0]['ds'],
            'end': prophet_data[-1]['ds'],
            'days': len(prophet_data)
        },
        'cost_statistics': {
            'min_cost': min([d['y'] for d in prophet_data]),
            'max_cost': max([d['y'] for d in prophet_data]),
            'avg_cost': sum([d['y'] for d in prophet_data]) / len(prophet_data),
            'total_cost': sum([d['y'] for d in prophet_data])
        },
        'patterns_included': [
            'weekly_seasonality',
            'monthly_patterns',
            'growth_trends',
            'random_variation',
            'cost_spikes',
            'weekend_effects'
        ],
        'model_readiness': {
            'prophet_ready': len(prophet_data) >= 30,
            'arima_ready': len(arima_data) >= 30,
            'features_ready': len(features) > 0
        }
    }
    
    return metadata

def main():
    """Main execution function"""
    print("🎯 Comprehensive ML Data Generation")
    print("=" * 50)
    
    # Generate realistic cost data
    df = generate_realistic_aws_costs(days=45)
    
    # Create Prophet format
    prophet_data = create_prophet_format(df)
    
    # Create ARIMA format
    arima_data = create_arima_format(df)
    
    # Create comprehensive features
    features = create_feature_engineering(df)
    
    # Create metadata
    metadata = create_metadata(prophet_data, arima_data, features)
    
    # Save all datasets to S3
    print("\n💾 Saving comprehensive datasets to S3...")
    
    prophet_key = save_to_s3(prophet_data, 'prophet_data', 'Prophet training data')
    arima_key = save_to_s3(arima_data, 'arima_data', 'ARIMA training data')
    features_key = save_to_s3(features, 'ml_features', 'ML feature set')
    metadata_key = save_to_s3(metadata, 'metadata', 'Dataset metadata')
    
    # Create daily aggregated features for time series analysis
    daily_features = []
    for feature in features:
        daily_features.append({
            'date': feature['date'],
            'cost': feature['cost'],
            'cost_ma_7': feature['cost_ma_7'],
            'growth_7d': feature['growth_7d'],
            'volatility_7d': feature['volatility_7d'],
            'weekend': feature['weekend'],
            'spike_event': feature['spike_event']
        })
    
    daily_key = save_to_s3(daily_features, 'daily_features', 'Daily feature summary')
    
    print("\n🎉 Comprehensive ML Data Generation Completed!")
    print("📊 Dataset Summary:")
    print(f"   🔮 Prophet: {len(prophet_data)} observations (need 30+)")
    print(f"   📊 ARIMA: {len(arima_data)} time series points")
    print(f"   🛠️ Features: {len(features[0])} engineered features")
    print(f"   📅 Date range: {metadata['date_range']['days']} days")
    print(f"   💰 Total simulated cost: ${metadata['cost_statistics']['total_cost']:.2f}")
    
    print(f"\n✅ Model Readiness Status:")
    print(f"   🔮 Prophet Ready: {'YES' if metadata['model_readiness']['prophet_ready'] else 'NO'}")
    print(f"   📊 ARIMA Ready: {'YES' if metadata['model_readiness']['arima_ready'] else 'NO'}")
    print(f"   🛠️ Features Ready: {'YES' if metadata['model_readiness']['features_ready'] else 'NO'}")
    
    print("\n💰 Cost Impact: $0.00 (S3 storage within free tier)")
    
    print("\n🎯 Next Steps:")
    print("1. Run test_ml_readiness.py to verify")
    print("2. Proceed with Prophet model development")
    print("3. Compare with ARIMA model performance")

if __name__ == "__main__":
    main()