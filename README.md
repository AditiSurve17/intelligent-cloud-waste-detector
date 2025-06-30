# Intelligent Cloud Waste Detector

## 🎯 Project Overview
AI-powered AWS resource waste detection with automated Terraform optimization. A 3-week beginner-friendly project focusing on cost optimization and dual-model machine learning forecasting.

**Current Status**: Week 2, Day 10 - Dual-Model System Complete ✅

## 📊 Project Timeline
- **Week 1** (Days 1-7): ✅ Foundation & Data Pipeline
- **Week 2** (Days 8-14): 🔄 Machine Learning Models (Prophet ✅, ARIMA ✅, Ensemble ✅)
- **Week 3** (Days 15-21): 🔜 Dashboard & Automation

## 🏗️ Current Infrastructure
**Region**: ap-south-1 (Mumbai)  
**Account**: 266735843482  
**Cost Status**: $0.05 total (99.9% free tier compliance)

### Active AWS Services
- ✅ **S3 Bucket**: `cwd-cost-usage-reports-as-2025`
- ✅ **DynamoDB Tables**: Usage data & recommendations storage
- ✅ **Lambda Functions**: Data collection & analytics
- ✅ **EventBridge**: Automated scheduling (6-hour intervals)
- ✅ **CloudShell**: FREE ML development environment

## 🤖 Dual-Model Machine Learning Pipeline

### Prophet Model (Completed ✅)
- **Type**: Machine Learning time series forecasting
- **Training Data**: 45+ days of realistic AWS cost patterns
- **Accuracy**: Excellent (15-20% MAPE)
- **Prediction**: $2.01/day (-24% cost reduction trend)
- **Strengths**: Seasonality detection, trend analysis, holiday effects

### ARIMA Model (Completed ✅)
- **Type**: Statistical time series forecasting
- **Parameters**: ARIMA(1,0,1) optimized via grid search
- **Accuracy**: Fair (31% MAPE - typical for real-world data)
- **Prediction**: $2.74/day (+3% slight increase trend)
- **Strengths**: Statistical rigor, classical time series analysis

### Ensemble System (Completed ✅)
- **Approach**: Accuracy-weighted model combination
- **Ensemble Prediction**: $2.37/day (balanced forecast)
- **Model Agreement**: 73% confidence (moderate - normal)
- **Business Value**: Uncertainty quantification and scenario planning

## 📈 Key Results & Business Intelligence
- **Cost Prediction Range**: $2.01 - $2.74/day
- **Planning Recommendation**: Budget $2.37/day ±$0.37 uncertainty
- **Model Disagreement**: Valuable intelligence for risk management
- **Trend Analysis**: Prophet (optimistic) vs ARIMA (conservative)
- **Waste Detection**: Automatic alerts for cost spikes >50% baseline

## 🔧 Development Environment

### CloudShell ML Environment
```bash
# Location: AWS CloudShell (FREE)
# Directory: /home/cloudshell-user/cloud-waste-ml/
# Libraries: pandas, numpy, matplotlib, prophet, statsmodels, scikit-learn