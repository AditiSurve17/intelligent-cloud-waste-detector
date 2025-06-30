#!/usr/bin/env python3
"""
Ensemble Forecasting: Prophet + ARIMA Combined Predictions
Advanced AWS Cost Forecasting with Dual-Model Validation
"""

import pandas as pd
import numpy as np
import boto3
import json
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("🚀 Creating Ensemble Forecasting System...")
print("🎯 Combining Prophet + ARIMA for Enhanced Predictions")

s3_client = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'cwd-cost-usage-reports-as-2025'

def load_model_results():
    """Load both Prophet and ARIMA results"""
    print("\n📥 Loading model results...")
    
    try:
        # Load Prophet results
        prophet_response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='ml-results/prophet_results_'
        )
        
        arima_response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='ml-results/arima_results_'
        )
        
        if 'Contents' not in prophet_response or 'Contents' not in arima_response:
            print("❌ Missing model results")
            return None, None
        
        # Get latest results
        prophet_file = sorted([obj['Key'] for obj in prophet_response['Contents']])[-1]
        arima_file = sorted([obj['Key'] for obj in arima_response['Contents']])[-1]
        
        # Load Prophet results
        prophet_data = s3_client.get_object(Bucket=bucket_name, Key=prophet_file)
        prophet_results = json.loads(prophet_data['Body'].read().decode('utf-8'))
        
        # Load ARIMA results
        arima_data = s3_client.get_object(Bucket=bucket_name, Key=arima_file)
        arima_results = json.loads(arima_data['Body'].read().decode('utf-8'))
        
        print("✅ Both model results loaded successfully")
        return prophet_results, arima_results
        
    except Exception as e:
        print(f"❌ Error loading results: {str(e)}")
        return None, None

def create_ensemble_forecast(prophet_results, arima_results):
    """Create ensemble predictions"""
    print("\n🔮 Creating Ensemble Predictions...")
    
    # Extract forecasts
    prophet_avg = prophet_results['forecast_summary']['avg_predicted_cost']
    arima_avg = arima_results['forecast_summary']['avg_predicted_cost']
    
    # Get model accuracies for weighting
    prophet_mape = prophet_results['performance_metrics']['mape']
    arima_mape = arima_results['performance_metrics']['mape']
    
    # Calculate weights (inverse of error - better models get higher weight)
    prophet_weight = (1 / prophet_mape) if prophet_mape > 0 else 0.5
    arima_weight = (1 / arima_mape) if arima_mape > 0 else 0.5
    
    # Normalize weights
    total_weight = prophet_weight + arima_weight
    prophet_weight = prophet_weight / total_weight
    arima_weight = arima_weight / total_weight
    
    # Ensemble prediction
    ensemble_avg = (prophet_avg * prophet_weight) + (arima_avg * arima_weight)
    
    # Confidence calculation
    model_agreement = abs(prophet_avg - arima_avg)
    confidence_score = max(0, 100 - (model_agreement / max(prophet_avg, arima_avg) * 100))
    
    print(f"📊 Ensemble Forecast Results:")
    print(f"   🔮 Prophet Prediction: ${prophet_avg:.2f}/day (weight: {prophet_weight:.1%})")
    print(f"   📊 ARIMA Prediction: ${arima_avg:.2f}/day (weight: {arima_weight:.1%})")
    print(f"   🎯 Ensemble Prediction: ${ensemble_avg:.2f}/day")
    print(f"   📈 Model Agreement: {confidence_score:.1f}%")
    
    if confidence_score > 80:
        print("✅ High confidence - models strongly agree")
    elif confidence_score > 60:
        print("✅ Good confidence - models moderately agree")
    else:
        print("⚠️  Lower confidence - models show significant disagreement")
    
    return {
        'ensemble_avg': ensemble_avg,
        'prophet_avg': prophet_avg,
        'arima_avg': arima_avg,
        'prophet_weight': prophet_weight,
        'arima_weight': arima_weight,
        'confidence_score': confidence_score,
        'model_agreement': model_agreement
    }

def create_comprehensive_summary(ensemble_results, prophet_results, arima_results):
    """Create comprehensive analysis summary"""
    print("\n📋 Creating Comprehensive Analysis...")
    
    summary = {
        'analysis_timestamp': datetime.now().isoformat(),
        'dual_model_system': {
            'prophet_model': {
                'type': 'machine_learning',
                'avg_prediction': prophet_results['forecast_summary']['avg_predicted_cost'],
                'accuracy_mape': prophet_results['performance_metrics']['mape'],
                'strengths': ['seasonality_detection', 'trend_analysis', 'holiday_effects']
            },
            'arima_model': {
                'type': 'statistical',
                'avg_prediction': arima_results['forecast_summary']['avg_predicted_cost'],
                'accuracy_mape': arima_results['performance_metrics']['mape'],
                'strengths': ['time_series_patterns', 'statistical_rigor', 'parameter_optimization']
            }
        },
        'ensemble_prediction': ensemble_results,
        'business_insights': {
            'cost_trend': 'decreasing' if ensemble_results['ensemble_avg'] < 2.50 else 'stable',
            'prediction_confidence': 'high' if ensemble_results['confidence_score'] > 80 else 'moderate',
            'recommended_action': 'monitor' if ensemble_results['confidence_score'] > 70 else 'investigate'
        },
        'waste_detection_alerts': {
            'high_cost_risk': ensemble_results['ensemble_avg'] > 3.00,
            'volatility_concern': abs(ensemble_results['prophet_avg'] - ensemble_results['arima_avg']) > 0.50,
            'trend_alert': False  # Would be triggered by actual trend analysis
        }
    }
    
    return summary

def create_ensemble_visualization(ensemble_results, summary):
    """Create comprehensive ensemble visualization"""
    print("\n📊 Creating ensemble visualization...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Model Comparison Bar Chart
    models = ['Prophet', 'ARIMA', 'Ensemble']
    predictions = [
        ensemble_results['prophet_avg'],
        ensemble_results['arima_avg'], 
        ensemble_results['ensemble_avg']
    ]
    colors = ['blue', 'red', 'green']
    
    bars = ax1.bar(models, predictions, color=colors, alpha=0.7)
    ax1.set_title('Model Predictions Comparison', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Predicted Daily Cost ($)', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, predictions):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'${value:.2f}', ha='center', va='bottom', fontweight='bold')
    
    # 2. Model Weights Pie Chart
    weights = [ensemble_results['prophet_weight'], ensemble_results['arima_weight']]
    labels = ['Prophet', 'ARIMA']
    colors_pie = ['lightblue', 'lightcoral']
    
    ax2.pie(weights, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Ensemble Model Weights', fontweight='bold', fontsize=12)
    
    # 3. Confidence Score Gauge
    confidence = ensemble_results['confidence_score']
    ax3.barh(['Confidence'], [confidence], color='green' if confidence > 80 else 'orange' if confidence > 60 else 'red')
    ax3.set_xlim(0, 100)
    ax3.set_title('Prediction Confidence Score', fontweight='bold', fontsize=12)
    ax3.set_xlabel('Confidence (%)', fontweight='bold')
    
    # Add confidence text
    ax3.text(confidence/2, 0, f'{confidence:.1f}%', ha='center', va='center', 
            fontweight='bold', fontsize=14, color='white')
    
    # 4. Business Summary
    summary_text = f"""
    🎯 ENSEMBLE FORECAST SUMMARY
    
    💰 Predicted Daily Cost: ${ensemble_results['ensemble_avg']:.2f}
    📊 Model Agreement: {ensemble_results['confidence_score']:.1f}%
    📈 Cost Trend: {summary['business_insights']['cost_trend'].title()}
    🎯 Confidence: {summary['business_insights']['prediction_confidence'].title()}
    
    📋 MODELS PERFORMANCE:
    🔮 Prophet: ${ensemble_results['prophet_avg']:.2f} (ML approach)
    📊 ARIMA: ${ensemble_results['arima_avg']:.2f} (Statistical)
    
    ⚠️  ALERTS:
    • High Cost Risk: {'YES' if summary['waste_detection_alerts']['high_cost_risk'] else 'NO'}
    • Volatility: {'HIGH' if summary['waste_detection_alerts']['volatility_concern'] else 'LOW'}
    """
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    ax4.set_title('Business Intelligence Summary', fontweight='bold', fontsize=12)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('ensemble_forecast_analysis.png', dpi=150, bbox_inches='tight')
    print("✅ Ensemble analysis saved: ensemble_forecast_analysis.png")

def save_ensemble_results(summary):
    """Save ensemble results to S3"""
    print("\n💾 Saving ensemble analysis to S3...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_key = f'ml-results/ensemble_analysis_{timestamp}.json'
    
    s3_client.put_object(
        Bucket=bucket_name,
        Key=results_key,
        Body=json.dumps(summary, indent=2, default=str),
        ContentType='application/json'
    )
    
    print(f"✅ Ensemble analysis saved: s3://{bucket_name}/{results_key}")
    return results_key

def main():
    """Main execution"""
    print("🎯 Ensemble Forecasting Analysis")
    print("=" * 50)
    
    # Load model results
    prophet_results, arima_results = load_model_results()
    if not prophet_results or not arima_results:
        return
    
    # Create ensemble forecast
    ensemble_results = create_ensemble_forecast(prophet_results, arima_results)
    
    # Create comprehensive summary
    summary = create_comprehensive_summary(ensemble_results, prophet_results, arima_results)
    
    # Create visualization
    create_ensemble_visualization(ensemble_results, summary)
    
    # Save results
    save_ensemble_results(summary)
    
    # Upload to S3
    try:
        s3_client.upload_file('ensemble_forecast_analysis.png', 
                             bucket_name, 
                             'visualizations/ensemble_forecast_analysis.png')
        print("✅ Ensemble visualization uploaded to S3")
    except Exception as e:
        print(f"⚠️ S3 upload warning: {str(e)}")
    
    print("\n🎉 Ensemble Forecasting Analysis Completed!")
    print("📊 Check ensemble_forecast_analysis.png for comprehensive analysis")
    print("💰 Total Cost: $0.00 (CloudShell remains FREE)")

if __name__ == "__main__":
    main()