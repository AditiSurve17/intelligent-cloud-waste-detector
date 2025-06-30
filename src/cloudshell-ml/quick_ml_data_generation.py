#!/usr/bin/env python3
"""
Backup ML Data Generation for Validation
Recreate comprehensive dataset for advanced validation (Backup Version)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def generate_comprehensive_ml_data():
    """Generate 45+ days of realistic AWS cost data with patterns"""
    print("🏗️ Generating Comprehensive ML Dataset...")
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate date range (45+ days)
    start_date = datetime(2025, 5, 15)  # Start in mid-May
    dates = pd.date_range(start=start_date, periods=50, freq='D')
    
    data = []
    base_cost = 2.65  # Our historical baseline
    
    for i, date in enumerate(dates):
        # Day of week effect (weekends typically lower)
        day_of_week = date.weekday()
        weekend_factor = 0.7 if day_of_week >= 5 else 1.0
        
        # Monthly cycle (higher costs at month start/end)
        day_of_month = date.day
        if day_of_month <= 5 or day_of_month >= 25:
            monthly_factor = 1.15
        else:
            monthly_factor = 1.0
        
        # Overall trend (slight increase over time)
        trend_factor = 1 + (i * 0.002)  # 0.2% increase per day
        
        # Random variation
        noise = np.random.normal(0, 0.15)
        
        # Calculate daily cost
        daily_cost = base_cost * weekend_factor * monthly_factor * trend_factor + noise
        daily_cost = max(0.50, daily_cost)  # Minimum cost floor
        
        # Add some feature engineering
        lag_1 = data[-1]['daily_cost'] if len(data) > 0 else daily_cost
        lag_7 = data[-7]['daily_cost'] if len(data) >= 7 else daily_cost
        
        rolling_avg_7 = np.mean([d['daily_cost'] for d in data[-6:]]) if len(data) >= 6 else daily_cost
        
        growth_rate = ((daily_cost - lag_1) / lag_1) * 100 if lag_1 > 0 else 0
        
        row = {
            'date': date,
            'daily_cost': round(daily_cost, 2),
            'day_of_week': day_of_week,
            'is_weekend': 1 if day_of_week >= 5 else 0,
            'day_of_month': day_of_month,
            'is_month_boundary': 1 if day_of_month <= 5 or day_of_month >= 25 else 0,
            'lag_1_cost': round(lag_1, 2),
            'lag_7_cost': round(lag_7, 2),
            'rolling_avg_7': round(rolling_avg_7, 2),
            'growth_rate': round(growth_rate, 1),
            'volatility': round(abs(growth_rate), 1),
            'cost_deviation': round(((daily_cost - rolling_avg_7) / rolling_avg_7) * 100, 1) if rolling_avg_7 > 0 else 0
        }
        
        data.append(row)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Add more engineered features
    df['rolling_avg_3'] = df['daily_cost'].rolling(window=3, min_periods=1).mean().round(2)
    df['rolling_std_7'] = df['daily_cost'].rolling(window=7, min_periods=1).std().round(3)
    df['cost_trend'] = df['daily_cost'].diff().round(3)
    
    print(f"✅ Generated {len(df)} days of ML training data")
    print(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"💰 Cost range: ${df['daily_cost'].min():.2f} - ${df['daily_cost'].max():.2f}")
    print(f"📊 Average daily cost: ${df['daily_cost'].mean():.2f}")
    
    # Save to CSV
    df.to_csv('comprehensive_ml_data_backup.csv', index=False)
    print("✅ Saved as: comprehensive_ml_data_backup.csv")
    
    return df

def main():
    """Backup data generation main function"""
    print("🚀 Backup ML Data Generation for Validation")
    print("=" * 50)
    
    # Generate the data
    df = generate_comprehensive_ml_data()
    
    # Show sample of data
    print(f"\n📊 Sample of Generated Data:")
    print(df[['date', 'daily_cost', 'is_weekend', 'growth_rate', 'cost_deviation']].head(10).to_string(index=False))
    
    print(f"\n✅ Ready for Advanced Validation!")
    print(f"💰 Cost: $0.00 (CloudShell Free Tier)")

if __name__ == "__main__":
    main()