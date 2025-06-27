#!/usr/bin/env python3
"""
Fixed Prophet Visualization Script
Fixes the plot_components() ax parameter issue
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

print("🎨 Creating Fixed Prophet Visualizations...")

# AWS Configuration
s3_client = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'cwd-cost-usage-reports-as-2025'

def load_latest_prophet_data():
    """Load the most recent Prophet data"""
    try:
        # List ML data files
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='ml-data/prophet_data_'
        )
        
        if 'Contents' not in response:
            print("❌ No Prophet data found")
            return None
        
        # Get latest file
        latest_file = sorted([obj['Key'] for obj in response['Contents']])[-1]
        print(f"📄 Loading: {latest_file}")
        
        # Load data
        response = s3_client.get_object(Bucket=bucket_name, Key=latest_file)
        prophet_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Convert to DataFrame
        df = pd.DataFrame(prophet_data)
        df['ds'] = pd.to_datetime(df['ds'])
        df['y'] = pd.to_numeric(df['y'])
        
        print(f"✅ Loaded {len(df)} observations")
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return None

def create_and_train_model(df):
    """Create and train Prophet model"""
    print("🔮 Training Prophet model...")
    
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0,
        interval_width=0.95
    )
    
    # Add regressors if available
    if 'weekend' in df.columns:
        model.add_regressor('weekend')
    if 'month_start' in df.columns:
        model.add_regressor('month_start')
    
    # Train model
    model.fit(df)
    print("✅ Model training completed")
    
    return model

def generate_forecast(model, df, days=30):
    """Generate forecast"""
    print(f"🔮 Generating {days}-day forecast...")
    
    # Create future dataframe
    future = model.make_future_dataframe(periods=days)
    
    # Add regressors for future dates
    if 'weekend' in df.columns:
        future['weekend'] = future['ds'].dt.weekday.isin([5, 6]).astype(int)
    if 'month_start' in df.columns:
        future['month_start'] = (future['ds'].dt.day == 1).astype(int)
    
    # Generate predictions
    forecast = model.predict(future)
    
    # Print results
    historical_avg = df['y'].mean()
    forecast_avg = forecast.tail(days)['yhat'].mean()
    trend_change = ((forecast_avg - historical_avg) / historical_avg) * 100
    
    print(f"📊 Results:")
    print(f"   📈 Historical Average: ${historical_avg:.2f}/day")
    print(f"   🔮 Predicted Average: ${forecast_avg:.2f}/day")
    print(f"   📈 Trend Change: {trend_change:+.1f}%")
    
    return forecast

def create_fixed_visualizations(model, forecast, df):
    """Create fixed visualizations without ax parameter issues"""
    print("\n📊 Creating fixed visualizations...")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 12))
    
    # Main forecast plot
    ax1 = plt.subplot(3, 1, 1)
    model.plot(forecast, ax=ax1)
    ax1.set_title('AWS Cost Forecast - Next 30 Days', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Daily Cost ($)', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    historical_data = forecast[forecast['ds'] <= df['ds'].max()]
    future_data = forecast[forecast['ds'] > df['ds'].max()]
    
    if len(future_data) > 0:
        ax1.axvline(x=df['ds'].max(), color='red', linestyle='--', alpha=0.7, label='Forecast Start')
        ax1.legend()
    
    # Components plot (using separate figure to avoid ax issues)
    ax2 = plt.subplot(3, 1, 2)
    
    # Manually plot trend component
    if 'trend' in forecast.columns:
        ax2.plot(forecast['ds'], forecast['trend'], color='blue', linewidth=2)
        ax2.set_title('Cost Trend Component', fontweight='bold')
        ax2.set_ylabel('Trend ($)', fontweight='bold')
        ax2.grid(True, alpha=0.3)
    
    # Weekly seasonality plot
    ax3 = plt.subplot(3, 1, 3)
    if 'weekly' in forecast.columns:
        ax3.plot(forecast['ds'], forecast['weekly'], color='green', linewidth=2)
        ax3.set_title('Weekly Seasonality (Weekend vs Weekday)', fontweight='bold')
        ax3.set_ylabel('Weekly Effect ($)', fontweight='bold')
        ax3.set_xlabel('Date', fontweight='bold')
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('aws_cost_forecast_fixed.png', dpi=150, bbox_inches='tight')
    print("✅ Fixed visualization saved: aws_cost_forecast_fixed.png")
    
    # Create summary statistics plot
    create_summary_plot(forecast, df)
    
    return fig

def create_summary_plot(forecast, df):
    """Create summary statistics visualization"""
    print("📈 Creating summary statistics plot...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Historical vs Predicted Costs
    historical_costs = df['y'].values
    future_costs = forecast.tail(30)['yhat'].values
    
    ax1.hist(historical_costs, bins=15, alpha=0.7, label='Historical', color='blue')
    ax1.hist(future_costs, bins=15, alpha=0.7, label='Predicted', color='orange')
    ax1.set_title('Cost Distribution Comparison')
    ax1.set_xlabel('Daily Cost ($)')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Daily Cost Timeline
    ax2.plot(df['ds'], df['y'], 'o-', label='Historical', color='blue', markersize=4)
    future_dates = forecast.tail(30)['ds']
    ax2.plot(future_dates, future_costs, 'o-', label='Predicted', color='orange', markersize=4)
    ax2.set_title('Daily Cost Timeline')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Daily Cost ($)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    # Confidence Intervals
    forecast_period = forecast.tail(30)
    ax3.fill_between(forecast_period['ds'], 
                    forecast_period['yhat_lower'], 
                    forecast_period['yhat_upper'], 
                    alpha=0.3, color='gray', label='95% Confidence')
    ax3.plot(forecast_period['ds'], forecast_period['yhat'], 'o-', color='red', label='Prediction')
    ax3.set_title('Forecast Confidence Intervals')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Daily Cost ($)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    # Cost Statistics
    stats_text = f"""
    Historical Statistics:
    • Average: ${df['y'].mean():.2f}/day
    • Min: ${df['y'].min():.2f}/day
    • Max: ${df['y'].max():.2f}/day
    • Std Dev: ${df['y'].std():.2f}
    
    Forecast Statistics:
    • Predicted Avg: ${future_costs.mean():.2f}/day
    • Trend: {((future_costs.mean() - df['y'].mean()) / df['y'].mean() * 100):+.1f}%
    • High Cost Days: {len([c for c in future_costs if c > df['y'].mean() * 1.2])}
    """
    
    ax4.text(0.1, 0.5, stats_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    ax4.set_title('Cost Statistics Summary')
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('aws_cost_summary.png', dpi=150, bbox_inches='tight')
    print("✅ Summary visualization saved: aws_cost_summary.png")

def main():
    """Main execution"""
    print("🎯 Fixed Prophet Visualization Generation")
    print("=" * 50)
    
    # Load data
    df = load_latest_prophet_data()
    if df is None:
        return
    
    # Create and train model
    model = create_and_train_model(df)
    
    # Generate forecast
    forecast = generate_forecast(model, df, days=30)
    
    # Create fixed visualizations
    create_fixed_visualizations(model, forecast, df)
    
    # Upload visualizations to S3
    try:
        s3_client.upload_file('aws_cost_forecast_fixed.png', 
                             bucket_name, 
                             'visualizations/aws_cost_forecast_fixed.png')
        s3_client.upload_file('aws_cost_summary.png', 
                             bucket_name, 
                             'visualizations/aws_cost_summary.png')
        print("✅ Visualizations uploaded to S3")
    except Exception as e:
        print(f"⚠️ S3 upload warning: {str(e)}")
    
    print("\n🎉 Fixed Visualization Generation Completed!")
    print("📊 Files created:")
    print("   • aws_cost_forecast_fixed.png")
    print("   • aws_cost_summary.png")
    print("💰 Cost: $0.00 (CloudShell remains FREE)")

if __name__ == "__main__":
    main()