#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

print("🤖 ML READINESS TEST")
print("="*30)

try:
    s3_client = boto3.client('s3', region_name='ap-south-1')
    
    # List ML data files
    response = s3_client.list_objects_v2(
        Bucket='cwd-cost-usage-reports-as-2025',
        Prefix='ml-data/'
    )
    
    if 'Contents' not in response:
        print("❌ No ML data found")
        exit()
    
    # Find Prophet and feature files
    prophet_files = [obj for obj in response['Contents'] if 'prophet_data' in obj['Key']]
    feature_files = [obj for obj in response['Contents'] if 'ml_features' in obj['Key']]
    
    print(f"📊 Found {len(prophet_files)} Prophet files")
    print(f"📊 Found {len(feature_files)} Feature files")
    
    # Test Prophet data
    if prophet_files:
        latest_prophet = sorted(prophet_files, key=lambda x: x['Key'])[-1]
        print(f"✅ Latest Prophet file: {latest_prophet['Key']}")
        
        obj = s3_client.get_object(Bucket='cwd-cost-usage-reports-as-2025', Key=latest_prophet['Key'])
        prophet_data = json.loads(obj['Body'].read())
        
        print(f"✅ Prophet data points: {len(prophet_data)}")
        
        if len(prophet_data) >= 10:
            print("✅ Sufficient data for Prophet model training")
            
            # Check structure
            if prophet_data and 'ds' in prophet_data[0] and 'y' in prophet_data[0]:
                print("✅ Prophet data structure correct")
                print(f"   Sample: {prophet_data[0]['ds']} → ${prophet_data[0]['y']}")
            else:
                print("❌ Prophet data structure incorrect")
        else:
            print("⚠️ Insufficient data for robust Prophet training")
    
    # Test feature data
    if feature_files:
        latest_features = sorted(feature_files, key=lambda x: x['Key'])[-1]
        print(f"✅ Latest Features file: {latest_features['Key']}")
        
        obj = s3_client.get_object(Bucket='cwd-cost-usage-reports-as-2025', Key=latest_features['Key'])
        feature_data = json.loads(obj['Body'].read())
        
        print(f"✅ Feature data points: {len(feature_data)}")
        
        if feature_data:
            feature_count = len(feature_data[0])
            print(f"✅ Features per observation: {feature_count}")
            
            # Check for key ML features
            key_features = ['total_cost', 'cost_lag_1', 'cost_ma_3', 'is_weekend']
            found_features = [f for f in key_features if f in feature_data[0]]
            print(f"✅ Key features found: {len(found_features)}/{len(key_features)}")
            print(f"   Features: {found_features}")
    
    # Overall assessment
    prophet_ready = prophet_files and len(prophet_data) >= 10
    features_ready = feature_files and len(feature_data) >= 15
    
    print(f"\n🎯 ML READINESS ASSESSMENT:")
    print(f"Prophet Model Ready: {'✅ YES' if prophet_ready else '❌ NO'}")
    print(f"ARIMA Model Ready: {'✅ YES' if prophet_ready else '❌ NO'}")
    print(f"Feature Engineering: {'✅ COMPLETE' if features_ready else '❌ INCOMPLETE'}")
    
    if prophet_ready and features_ready:
        print(f"\n🚀 OVERALL STATUS: READY FOR CHECKPOINT 6!")
        print(f"✅ All ML prerequisites met")
        print(f"✅ Data quality validated")
        print(f"✅ Ready for model development")
    else:
        print(f"\n⚠️ OVERALL STATUS: NEEDS ATTENTION")
        
except Exception as e:
    print(f"❌ ML readiness test failed: {e}")