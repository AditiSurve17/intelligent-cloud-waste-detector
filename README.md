# Intelligent Cloud Waste Detector

## 🎯 Project Overview
AI-powered AWS resource waste detection with automated Terraform optimization. A 3-week beginner-friendly project focusing on cost optimization and machine learning forecasting.

**Current Status**: Week 2, Day 9 - Prophet Model Development Completed ✅

## 📊 Project Timeline
- **Week 1** (Days 1-7): ✅ Foundation & Data Pipeline
- **Week 2** (Days 8-14): 🔄 Machine Learning Models (Prophet ✅, ARIMA 🎯)
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

## 🤖 Machine Learning Pipeline

### Prophet Model (Completed ✅)
- **Training Data**: 45+ days of realistic AWS cost patterns
- **Accuracy**: <20% MAPE (excellent forecasting)
- **Predictions**: 30-day cost forecasting
- **Key Insight**: 24% cost reduction trend detected
- **Features**: Weekend seasonality, monthly patterns, spike detection

### ARIMA Model (Next 🎯)
- Statistical time series forecasting
- Model comparison and validation
- Enhanced prediction accuracy

## 📈 Key Results
- **Historical Average**: $2.66/day AWS spend
- **Predicted Average**: $2.01/day (24% reduction)
- **Waste Detection**: Automatic alerts for cost spikes
- **Model Performance**: Excellent accuracy achieved

## 🔧 Development Setup

### CloudShell Environment
```bash
# Location: AWS CloudShell (FREE)
# Directory: /home/cloudshell-user/cloud-waste-ml/
# Libraries: pandas, numpy, matplotlib, prophet, statsmodels