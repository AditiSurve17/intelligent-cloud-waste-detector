#!/usr/bin/env python3
"""
Prophet Model Development for AWS Cost Forecasting
Checkpoint 6 - Intelligent Cloud Waste Detector
Region: ap-south-1 (Mumbai)
"""

import pandas as pd
import numpy as np
import boto3
import json
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # CloudShell compatibility
import matplotlib.pyplot as plt
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

print("🚀 Starting Prophet Model Development...")
print("📍 Region: ap-south-1 (Mumbai)")
print("💰 Cost: $0.00 (CloudShell is FREE)")

# AWS Configuration
s3_client = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'cwd-cost-usage-reports-as-2025'

def load_latest_ml_data():
    """Load the most recent ML datasets from S3"""
    print("\n📥 Loading ML data from S3...")
    
    try:
        # List ML data files
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='ml-data/'
        )
        
        if 'Contents' not in response:
            print("❌ No ML data found. Run generate_missing_ml_data.py first")
            return None, None
        
        # Find latest prophet data file
        prophet_files = [obj['Key'] for obj in response['Contents'] 
                        if 'prophet_data_' in obj['Key']]
        
        if not prophet_files:
            print("❌ No Prophet data found")
            return None, None
            
        latest_prophet_file = sorted(prophet_files)[-1]
        print(f"📄 Latest Prophet data: {latest_prophet_file}")
        
        # Load Prophet data
        response = s3_client.get_object(Bucket=bucket_name, Key=latest_prophet_file)
        prophet_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Convert to DataFrame
        df = pd.DataFrame(prophet_data)
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = pd.to_numeric(df['y'])
        
        print(f"✅ Loaded {len(df)} observations for Prophet training")
        print(f"📅 Date range: {df['ds'].min().date()} to {df['ds'].max().date()}")
        print(f"💰 Cost range: ${df['y'].min():.2f} to ${df['y'].max():.2f}")
        
        return df, latest_prophet_file
        
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return None, None

def create_prophet_model(df):
    """Create and train Prophet model"""
    print("\n🔮 Training Prophet Model...")
    print("📚 What is Prophet? Facebook's time series forecasting tool")
    print("🎯 Purpose: Predict future AWS costs and detect unusual patterns")
    
    # Initialize Prophet with custom settings
    model = Prophet(
        yearly_seasonality=False,      # Not enough data for yearly patterns
        weekly_seasonality=True,       # Weekend vs weekday patterns
        daily_seasonality=False,       # Daily patterns not relevant for costs
        changepoint_prior_scale=0.05,  # Flexible trend changes
        seasonality_prior_scale=10.0,  # Strong seasonal patterns
        interval_width=0.95            # 95% confidence intervals
    )
    
    # Add custom regressors if available
    if 'weekend' in df.columns:
        model.add_regressor('weekend')
        print("✅ Added weekend regressor")
    
    if 'month_start' in df.columns:
        model.add_regressor('month_start') 
        print("✅ Added month start regressor")
    
    # Train the model
    print("🎓 Training model on your AWS usage patterns...")
    model.fit(df)
    
    print("✅ Prophet model training completed!")
    return model

def generate_forecasts(model, df, days=30):
    """Generate future cost predictions"""
    print(f"\n🔮 Generating {days}-day cost forecasts...")
    
    # Create future dataframe
    future = model.make_future_dataframe(periods=days)
    
    # Add regressors for future dates if they exist
    if 'weekend' in df.columns:
        future['weekend'] = future['ds'].dt.weekday.isin([5, 6]).astype(int)
    
    if 'month_start' in df.columns:
        future['month_start'] = (future['ds'].dt.day == 1).astype(int)
    
    # Generate predictions
    forecast = model.predict(future)
    
    # Extract key metrics
    historical_avg = df['y'].mean()
    forecast_avg = forecast.tail(days)['yhat'].mean()
    trend_change = ((forecast_avg - historical_avg) / historical_avg) * 100
    
    print(f"📊 Forecast Results:")
    print(f"📈 Historical Average: ${historical_avg:.2f}/day")
    print(f"🔮 Predicted Average: ${forecast_avg:.2f}/day")
    print(f"📈 Trend Change: {trend_change:+.1f}%")
    
    # Identify potential waste alerts
    future_costs = forecast.tail(days)
    high_cost_days = future_costs[future_costs['yhat'] > historical_avg * 1.5]
    
    if len(high_cost_days) > 0:
        print(f"⚠️  WASTE ALERT: {len(high_cost_days)} days with >50% higher costs predicted")
        for _, day in high_cost_days.head(3).iterrows():
            print(f"   📅 {day['ds'].date()}: ${day['yhat']:.2f} (vs ${historical_avg:.2f} avg)")
    
    return forecast, future

def create_forecast_visualization(model, forecast, df):
    """Create forecast visualization"""
    print("\n📊 Creating forecast visualization...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Main forecast plot
    model.plot(forecast, ax=ax1)
    ax1.set_title('AWS Cost Forecast - Next 30 Days', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Daily Cost ($)')
    ax1.grid(True, alpha=0.3)
    
    # Components plot
    model.plot_components(forecast, ax=ax2)
    
    plt.tight_layout()
    plt.savefig('aws_cost_forecast.png', dpi=150, bbox_inches='tight')
    print("✅ Forecast visualization saved: aws_cost_forecast.png")
    
    return fig

def evaluate_model_performance(model, df):
    """Evaluate model accuracy"""
    print("\n📈 Evaluating Model Performance...")
    
    # Split data for validation (use last 20% for testing)
    split_point = int(len(df) * 0.8)
    train_df = df[:split_point].copy()
    test_df = df[split_point:].copy()
    
    if len(test_df) < 3:
        print("⚠️  Limited data for validation (need more historical data)")
        return None
    
    # Train on subset
    test_model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    
    if 'weekend' in train_df.columns:
        test_model.add_regressor('weekend')
    if 'month_start' in train_df.columns:
        test_model.add_regressor('month_start')
    
    test_model.fit(train_df)
    
    # Predict on test period
    future_test = test_model.make_future_dataframe(periods=len(test_df))
    if 'weekend' in df.columns:
        future_test['weekend'] = future_test['ds'].dt.weekday.isin([5, 6]).astype(int)
    if 'month_start' in df.columns:
        future_test['month_start'] = (future_test['ds'].dt.day == 1).astype(int)
    
    forecast_test = test_model.predict(future_test)
    
    # Calculate accuracy metrics
    predictions = forecast_test.tail(len(test_df))['yhat'].values
    actuals = test_df['y'].values
    
    mae = np.mean(np.abs(predictions - actuals))
    mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
    rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
    
    print(f"🎯 Model Accuracy Metrics:")
    print(f"   📊 Mean Absolute Error (MAE): ${mae:.2f}")
    print(f"   📊 Mean Absolute Percentage Error: {mape:.1f}%")
    print(f"   📊 Root Mean Square Error: ${rmse:.2f}")
    
    if mape < 20:
        print("✅ Excellent accuracy (MAPE < 20%)")
    elif mape < 30:
        print("✅ Good accuracy (MAPE < 30%)")
    else:
        print("⚠️  Fair accuracy - consider more data collection")
    
    return {'mae': mae, 'mape': mape, 'rmse': rmse}

def save_model_results(forecast, metrics, original_file):
    """Save model results to S3"""
    print("\n💾 Saving model results to S3...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Prepare results
    results = {
        'timestamp': timestamp,
        'model_type': 'prophet',
        'data_source': original_file,
        'forecast_periods': 30,
        'performance_metrics': metrics,
        'forecast_summary': {
            'avg_predicted_cost': float(forecast.tail(30)['yhat'].mean()),
            'trend_direction': 'increasing' if forecast.tail(30)['yhat'].mean() > forecast.head(30)['yhat'].mean() else 'decreasing',
            'confidence_interval_width': float(forecast.tail(30)['yhat_upper'].mean() - forecast.tail(30)['yhat_lower'].mean())
        }
    }
    
    # Save to S3
    results_key = f'ml-results/prophet_results_{timestamp}.json'
    s3_client.put_object(
        Bucket=bucket_name,
        Key=results_key,
        Body=json.dumps(results, indent=2),
        ContentType='application/json'
    )
    
    print(f"✅ Results saved: s3://{bucket_name}/{results_key}")
    return results_key

def main():
    """Main execution function"""
    print("🎯 Prophet Model Development for AWS Cost Forecasting")
    print("=" * 60)
    
    # Load data
    df, source_file = load_latest_ml_data()
    if df is None:
        return
    
    # Create and train model
    model = create_prophet_model(df)
    
    # Generate forecasts
    forecast, future = generate_forecasts(model, df, days=30)
    
    # Create visualization
    create_forecast_visualization(model, forecast, df)
    
    # Evaluate performance
    metrics = evaluate_model_performance(model, df)
    
    # Save results
    if metrics:
        save_model_results(forecast, metrics, source_file)
    
    print("\n🎉 Prophet Model Development Completed!")
    print("📊 Check aws_cost_forecast.png for visualizations")
    print("📁 Results saved to S3 ml-results/ folder")
    print("💰 Total Cost: $0.00 (CloudShell remains FREE)")
    
    print("\n🎯 Next Steps:")
    print("1. Review forecast visualization")
    print("2. Analyze waste alerts")
    print("3. Prepare for ARIMA model comparison")

if __name__ == "__main__":
    main()