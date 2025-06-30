#!/usr/bin/env python3
"""
ARIMA Model Development for AWS Cost Forecasting
Checkpoint 7 - Intelligent Cloud Waste Detector
Statistical Time Series Approach
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
import warnings
warnings.filterwarnings('ignore')

# ARIMA and statistical libraries
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from sklearn.metrics import mean_absolute_error, mean_squared_error
import itertools

print("🚀 Starting ARIMA Model Development...")
print("📍 Region: ap-south-1 (Mumbai)")
print("📊 Approach: Statistical Time Series Forecasting")
print("💰 Cost: $0.00 (CloudShell is FREE)")

# AWS Configuration
s3_client = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'cwd-cost-usage-reports-as-2025'

def load_arima_data():
    """Load ARIMA-formatted time series data"""
    print("\n📥 Loading ARIMA data from S3...")
    
    try:
        # List ARIMA data files
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='ml-data/arima_data_'
        )
        
        if 'Contents' not in response:
            print("❌ No ARIMA data found")
            return None
        
        # Get latest ARIMA file
        arima_files = [obj['Key'] for obj in response['Contents']]
        latest_arima_file = sorted(arima_files)[-1]
        print(f"📄 Latest ARIMA data: {latest_arima_file}")
        
        # Load data
        response = s3_client.get_object(Bucket=bucket_name, Key=latest_arima_file)
        arima_data = json.loads(response['Body'].read().decode('utf-8'))
        
        # Convert to time series DataFrame
        df = pd.DataFrame(arima_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        df.set_index('date', inplace=True)
        
        # Create time series
        ts = df['value']
        
        print(f"✅ Loaded {len(ts)} time series observations")
        print(f"📅 Date range: {ts.index.min().date()} to {ts.index.max().date()}")
        print(f"💰 Cost range: ${ts.min():.2f} to ${ts.max():.2f}")
        
        return ts, latest_arima_file
        
    except Exception as e:
        print(f"❌ Error loading ARIMA data: {str(e)}")
        return None, None

def check_stationarity(ts):
    """Check if time series is stationary"""
    print("\n🔍 Testing Time Series Stationarity...")
    print("📚 What is Stationarity? A stationary series has constant mean/variance over time")
    
    # Augmented Dickey-Fuller test
    result = adfuller(ts.dropna())
    
    print(f"📊 Stationarity Test Results:")
    print(f"   📈 ADF Statistic: {result[0]:.4f}")
    print(f"   📈 p-value: {result[1]:.4f}")
    print(f"   📈 Critical Values:")
    for key, value in result[4].items():
        print(f"      {key}: {value:.4f}")
    
    is_stationary = result[1] <= 0.05
    
    if is_stationary:
        print("✅ Time series is stationary (good for ARIMA)")
    else:
        print("⚠️  Time series is non-stationary (needs differencing)")
    
    return is_stationary, result

def make_stationary(ts):
    """Make time series stationary through differencing"""
    print("\n🔧 Making Time Series Stationary...")
    
    # First differencing
    ts_diff1 = ts.diff().dropna()
    
    # Test stationarity of differenced series
    result = adfuller(ts_diff1)
    
    if result[1] <= 0.05:
        print("✅ First differencing achieved stationarity")
        return ts_diff1, 1
    else:
        print("🔧 Trying second differencing...")
        ts_diff2 = ts_diff1.diff().dropna()
        result2 = adfuller(ts_diff2)
        
        if result2[1] <= 0.05:
            print("✅ Second differencing achieved stationarity")
            return ts_diff2, 2
        else:
            print("⚠️  Using first differencing (may need manual tuning)")
            return ts_diff1, 1

def find_optimal_parameters(ts, max_p=3, max_d=2, max_q=3):
    """Find optimal ARIMA parameters using grid search"""
    print("\n🎯 Finding Optimal ARIMA Parameters...")
    print("📚 What are p,d,q? p=autoregressive, d=differencing, q=moving average")
    
    # Generate all combinations of p, d, q
    p_values = range(0, max_p + 1)
    d_values = range(0, max_d + 1)
    q_values = range(0, max_q + 1)
    
    best_aic = float('inf')
    best_params = None
    best_model = None
    
    results = []
    
    print("🔍 Testing parameter combinations...")
    
    for p, d, q in itertools.product(p_values, d_values, q_values):
        try:
            # Fit ARIMA model
            model = ARIMA(ts, order=(p, d, q))
            fitted_model = model.fit()
            
            aic = fitted_model.aic
            results.append({
                'params': (p, d, q),
                'aic': aic,
                'bic': fitted_model.bic,
                'converged': True
            })
            
            if aic < best_aic:
                best_aic = aic
                best_params = (p, d, q)
                best_model = fitted_model
            
            print(f"   ARIMA({p},{d},{q}): AIC={aic:.2f}")
            
        except Exception as e:
            results.append({
                'params': (p, d, q),
                'aic': None,
                'error': str(e),
                'converged': False
            })
            continue
    
    print(f"\n🎯 Optimal Parameters Found:")
    print(f"   📊 Best ARIMA({best_params[0]},{best_params[1]},{best_params[2]})")
    print(f"   📊 AIC Score: {best_aic:.2f}")
    
    return best_params, best_model, results

def create_arima_model(ts, params=None):
    """Create and fit ARIMA model"""
    print("\n🔮 Training ARIMA Model...")
    
    if params is None:
        # Auto-find parameters
        params, model, search_results = find_optimal_parameters(ts)
    else:
        # Use provided parameters
        print(f"🎯 Using specified parameters: ARIMA{params}")
        model = ARIMA(ts, order=params)
        model = model.fit()
    
    print("✅ ARIMA model training completed!")
    
    # Model diagnostics
    print(f"\n📊 Model Diagnostics:")
    print(f"   📈 AIC: {model.aic:.2f}")
    print(f"   📈 BIC: {model.bic:.2f}")
    print(f"   📈 Log Likelihood: {model.llf:.2f}")
    
    return model, params

def generate_arima_forecasts(model, periods=30):
    """Generate ARIMA forecasts"""
    print(f"\n🔮 Generating {periods}-day ARIMA forecasts...")
    
    # Generate forecast
    forecast = model.forecast(steps=periods)
    conf_int = model.get_forecast(steps=periods).conf_int()
    
    # Create forecast dates
    last_date = model.data.dates[-1]
    forecast_dates = pd.date_range(
        start=last_date + timedelta(days=1), 
        periods=periods, 
        freq='D'
    )
    
    # Create forecast DataFrame
    forecast_df = pd.DataFrame({
        'date': forecast_dates,
        'forecast': forecast,
        'lower_ci': conf_int.iloc[:, 0],
        'upper_ci': conf_int.iloc[:, 1]
    })
    
    # Calculate statistics
    historical_avg = model.data.endog.mean()
    forecast_avg = forecast.mean()
    trend_change = ((forecast_avg - historical_avg) / historical_avg) * 100
    
    print(f"📊 ARIMA Forecast Results:")
    print(f"📈 Historical Average: ${historical_avg:.2f}/day")
    print(f"🔮 Predicted Average: ${forecast_avg:.2f}/day")
    print(f"📈 Trend Change: {trend_change:+.1f}%")
    
    # Identify potential waste alerts
    high_cost_threshold = historical_avg * 1.5
    high_cost_days = forecast_df[forecast_df['forecast'] > high_cost_threshold]
    
    if len(high_cost_days) > 0:
        print(f"⚠️  WASTE ALERT: {len(high_cost_days)} days with >50% higher costs predicted")
        for _, day in high_cost_days.head(3).iterrows():
            print(f"   📅 {day['date'].date()}: ${day['forecast']:.2f} (vs ${historical_avg:.2f} avg)")
    
    return forecast_df, forecast, conf_int

def evaluate_arima_performance(model, ts):
    """Evaluate ARIMA model performance"""
    print("\n📈 Evaluating ARIMA Model Performance...")
    
    # Split data for validation
    split_point = int(len(ts) * 0.8)
    train_data = ts[:split_point]
    test_data = ts[split_point:]
    
    if len(test_data) < 5:
        print("⚠️  Limited data for validation")
        return None
    
    # Fit model on training data
    train_model = ARIMA(train_data, order=model.model.order)
    train_fitted = train_model.fit()
    
    # Forecast on test period
    forecast_steps = len(test_data)
    forecast_values = train_fitted.forecast(steps=forecast_steps)
    
    # Calculate metrics
    mae = mean_absolute_error(test_data, forecast_values)
    rmse = np.sqrt(mean_squared_error(test_data, forecast_values))
    mape = np.mean(np.abs((test_data - forecast_values) / test_data)) * 100
    
    print(f"🎯 ARIMA Model Accuracy Metrics:")
    print(f"   📊 Mean Absolute Error (MAE): ${mae:.2f}")
    print(f"   📊 Root Mean Square Error (RMSE): ${rmse:.2f}")
    print(f"   📊 Mean Absolute Percentage Error: {mape:.1f}%")
    
    if mape < 20:
        print("✅ Excellent accuracy (MAPE < 20%)")
    elif mape < 30:
        print("✅ Good accuracy (MAPE < 30%)")
    else:
        print("⚠️  Fair accuracy - consider parameter tuning")
    
    return {'mae': mae, 'rmse': rmse, 'mape': mape}

def compare_with_prophet(arima_forecast_avg, arima_trend):
    """Compare ARIMA results with Prophet predictions"""
    print("\n🔄 Comparing ARIMA vs Prophet Models...")
    
    try:
        # Load Prophet results
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='ml-results/prophet_results_'
        )
        
        if 'Contents' in response:
            latest_prophet = sorted([obj['Key'] for obj in response['Contents']])[-1]
            prophet_response = s3_client.get_object(Bucket=bucket_name, Key=latest_prophet)
            prophet_results = json.loads(prophet_response['Body'].read().decode('utf-8'))
            
            prophet_avg = prophet_results['forecast_summary']['avg_predicted_cost']
            prophet_mape = prophet_results['performance_metrics']['mape']
            
            print(f"📊 Model Comparison:")
            print(f"   🔮 Prophet Average: ${prophet_avg:.2f}/day")
            print(f"   📊 ARIMA Average: ${arima_forecast_avg:.2f}/day")
            print(f"   📈 Difference: ${abs(prophet_avg - arima_forecast_avg):.2f}/day")
            
            # Determine better model
            if abs(arima_trend) < 15 and abs(prophet_results['forecast_summary'].get('trend_direction', 0)) < 15:
                print("✅ Both models show stable cost predictions")
            elif arima_forecast_avg < prophet_avg:
                print("📊 ARIMA predicts lower costs")
            else:
                print("🔮 Prophet predicts lower costs")
                
            return {
                'prophet_avg': prophet_avg,
                'arima_avg': arima_forecast_avg,
                'difference': abs(prophet_avg - arima_forecast_avg)
            }
        
    except Exception as e:
        print(f"⚠️  Could not load Prophet results: {str(e)}")
    
    return None

def save_arima_results(forecast_df, metrics, params, model_comparison):
    """Save ARIMA results to S3"""
    print("\n💾 Saving ARIMA results to S3...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    results = {
        'timestamp': timestamp,
        'model_type': 'arima',
        'model_parameters': {
            'p': params[0],
            'd': params[1],
            'q': params[2]
        },
        'performance_metrics': metrics,
        'forecast_summary': {
            'avg_predicted_cost': float(forecast_df['forecast'].mean()),
            'trend_direction': 'increasing' if forecast_df['forecast'].iloc[-1] > forecast_df['forecast'].iloc[0] else 'decreasing',
            'confidence_interval_width': float(forecast_df['upper_ci'].mean() - forecast_df['lower_ci'].mean()),
            'volatility': float(forecast_df['forecast'].std())
        },
        'model_comparison': model_comparison,
        'forecast_data': forecast_df.to_dict('records')
    }
    
    # Save to S3
    results_key = f'ml-results/arima_results_{timestamp}.json'
    s3_client.put_object(
        Bucket=bucket_name,
        Key=results_key,
        Body=json.dumps(results, indent=2, default=str),
        ContentType='application/json'
    )
    
    print(f"✅ ARIMA results saved: s3://{bucket_name}/{results_key}")
    return results_key

def main():
    """Main execution function"""
    print("🎯 ARIMA Model Development for AWS Cost Forecasting")
    print("=" * 60)
    
    # Load ARIMA data
    ts, source_file = load_arima_data()
    if ts is None:
        return
    
    # Check and ensure stationarity
    is_stationary, stationarity_result = check_stationarity(ts)
    
    # Create and train ARIMA model
    model, params = create_arima_model(ts)
    
    # Generate forecasts
    forecast_df, forecast, conf_int = generate_arima_forecasts(model, periods=30)
    
    # Evaluate performance
    metrics = evaluate_arima_performance(model, ts)
    
    # Compare with Prophet
    comparison = compare_with_prophet(forecast_df['forecast'].mean(), 
                                    ((forecast_df['forecast'].mean() - ts.mean()) / ts.mean() * 100))
    
    # Save results
    if metrics:
        save_arima_results(forecast_df, metrics, params, comparison)
    
    print("\n🎉 ARIMA Model Development Completed!")
    print("📁 Results saved to S3 ml-results/ folder")
    print("💰 Total Cost: $0.00 (CloudShell remains FREE)")
    
    print("\n🎯 Next Steps:")
    print("1. Review ARIMA vs Prophet comparison")
    print("2. Analyze model agreement/disagreement")
    print("3. Prepare ensemble forecasting approach")

if __name__ == "__main__":
    main()