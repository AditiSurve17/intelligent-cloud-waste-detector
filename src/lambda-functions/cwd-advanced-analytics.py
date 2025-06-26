# File: src/lambda-functions/cwd-advanced-analytics.py
# Advanced analytics function for cost trend analysis and ML preparation
# Created: 2025-06-26 - Checkpoint 4

import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from boto3.dynamodb.conditions import Key, Attr
import statistics
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients for ap-south-1
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
s3_client = boto3.client('s3', region_name='ap-south-1')

# DynamoDB tables
usage_table = dynamodb.Table('cwd-processed-usage-data')
recommendations_table = dynamodb.Table('cwd-waste-recommendations')

def lambda_handler(event, context):
    """
    Advanced analytics function for cost trend analysis and ML preparation
    """
    
    try:
        logger.info("Starting advanced analytics processing...")
        
        # Perform various analytics
        analytics_results = {}
        
        # 1. Cost trend analysis
        cost_trends = analyze_cost_trends()
        analytics_results['cost_trends'] = cost_trends
        
        # 2. Service utilization analysis
        service_analysis = analyze_service_utilization()
        analytics_results['service_analysis'] = service_analysis
        
        # 3. Recommendation effectiveness tracking
        recommendation_analysis = analyze_recommendation_effectiveness()
        analytics_results['recommendation_analysis'] = recommendation_analysis
        
        # 4. Anomaly detection
        anomalies = detect_cost_anomalies()
        analytics_results['anomalies'] = anomalies
        
        # 5. Generate weekly summary
        weekly_summary = generate_weekly_summary()
        analytics_results['weekly_summary'] = weekly_summary
        
        # 6. Prepare ML features
        ml_features = prepare_ml_features()
        analytics_results['ml_features'] = ml_features
        
        # Store analytics results in S3
        store_analytics_results_s3(analytics_results)
        
        logger.info("Advanced analytics completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Advanced analytics completed successfully',
                'analytics_summary': {
                    'cost_trends_analyzed': len(cost_trends.get('daily_costs', {})),
                    'services_analyzed': len(service_analysis.get('services', {})),
                    'anomalies_detected': len(anomalies.get('anomalies', [])),
                    'ml_features_prepared': len(ml_features.get('features', []))
                },
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in advanced analytics: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def analyze_cost_trends():
    """Analyze cost trends over time for predictive modeling"""
    try:
        logger.info("Analyzing cost trends...")
        
        # Get last 7 days of usage data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = usage_table.scan(
            FilterExpression=Attr('timestamp').between(
                start_date.isoformat(),
                end_date.isoformat()
            )
        )
        
        usage_data = response['Items']
        
        # Group by date and service
        daily_costs = {}
        service_trends = {}
        
        for record in usage_data:
            record_date = record['timestamp'][:10]  # YYYY-MM-DD
            cost = float(record['unblended_cost'])
            service = record['service_type']
            
            if record_date not in daily_costs:
                daily_costs[record_date] = 0
            daily_costs[record_date] += cost
            
            if service not in service_trends:
                service_trends[service] = {}
            if record_date not in service_trends[service]:
                service_trends[service][record_date] = 0
            service_trends[service][record_date] += cost
        
        # Calculate trend statistics
        daily_values = list(daily_costs.values())
        trend_analysis = {
            'daily_costs': daily_costs,
            'service_trends': service_trends,
            'statistics': {
                'average_daily_cost': statistics.mean(daily_values) if daily_values else 0,
                'max_daily_cost': max(daily_values) if daily_values else 0,
                'min_daily_cost': min(daily_values) if daily_values else 0,
                'cost_variance': statistics.variance(daily_values) if len(daily_values) > 1 else 0,
                'total_days_analyzed': len(daily_costs),
                'trend_direction': calculate_trend_direction(daily_costs)
            }
        }
        
        logger.info(f"Cost trend analysis completed for {len(daily_costs)} days")
        return trend_analysis
        
    except Exception as e:
        logger.error(f"Error in cost trend analysis: {str(e)}")
        return {}

def calculate_trend_direction(daily_costs):
    """Calculate if costs are trending up, down, or stable"""
    if len(daily_costs) < 2:
        return "insufficient_data"
    
    sorted_dates = sorted(daily_costs.keys())
    recent_costs = [daily_costs[date] for date in sorted_dates[-3:]]
    earlier_costs = [daily_costs[date] for date in sorted_dates[:3]]
    
    if not recent_costs or not earlier_costs:
        return "insufficient_data"
    
    recent_avg = statistics.mean(recent_costs)
    earlier_avg = statistics.mean(earlier_costs)
    
    if recent_avg > earlier_avg * 1.1:
        return "increasing"
    elif recent_avg < earlier_avg * 0.9:
        return "decreasing"
    else:
        return "stable"

def analyze_service_utilization():
    """Analyze utilization patterns by service type"""
    try:
        logger.info("Analyzing service utilization...")
        
        response = usage_table.scan()
        usage_data = response['Items']
        
        service_stats = {}
        
        for record in usage_data:
            service = record['service_type']
            cost = float(record['unblended_cost'])
            usage = float(record['usage_amount'])
            
            if service not in service_stats:
                service_stats[service] = {
                    'total_cost': 0,
                    'total_usage': 0,
                    'resource_count': 0,
                    'costs': [],
                    'usage_amounts': []
                }
            
            service_stats[service]['total_cost'] += cost
            service_stats[service]['total_usage'] += usage
            service_stats[service]['resource_count'] += 1
            service_stats[service]['costs'].append(cost)
            service_stats[service]['usage_amounts'].append(usage)
        
        # Calculate service-level analytics
        service_analysis = {
            'services': {},
            'top_cost_services': [],
            'underutilized_services': []
        }
        
        for service, stats in service_stats.items():
            avg_cost = stats['total_cost'] / stats['resource_count']
            avg_usage = stats['total_usage'] / stats['resource_count']
            
            service_info = {
                'total_cost': stats['total_cost'],
                'average_cost_per_resource': avg_cost,
                'total_usage': stats['total_usage'],
                'average_usage_per_resource': avg_usage,
                'resource_count': stats['resource_count'],
                'cost_efficiency': stats['total_usage'] / stats['total_cost'] if stats['total_cost'] > 0 else 0,
                'cost_variance': statistics.variance(stats['costs']) if len(stats['costs']) > 1 else 0
            }
            
            service_analysis['services'][service] = service_info
            
            # Identify top cost services
            if stats['total_cost'] > 1.0:
                service_analysis['top_cost_services'].append({
                    'service': service,
                    'cost': stats['total_cost']
                })
            
            # Identify underutilized services
            if avg_usage < 10 and stats['total_cost'] > 0.5:
                service_analysis['underutilized_services'].append({
                    'service': service,
                    'avg_usage': avg_usage,
                    'cost': stats['total_cost']
                })
        
        service_analysis['top_cost_services'].sort(key=lambda x: x['cost'], reverse=True)
        
        logger.info(f"Service utilization analysis completed for {len(service_stats)} services")
        return service_analysis
        
    except Exception as e:
        logger.error(f"Error in service utilization analysis: {str(e)}")
        return {}

def analyze_recommendation_effectiveness():
    """Analyze how effective our recommendations have been"""
    try:
        logger.info("Analyzing recommendation effectiveness...")
        
        response = recommendations_table.scan()
        recommendations = response['Items']
        
        recommendation_stats = {
            'total_recommendations': len(recommendations),
            'by_priority': {'High': 0, 'Medium': 0, 'Low': 0},
            'by_status': {},
            'total_potential_savings': 0,
            'average_confidence': 0,
            'top_recommendations': []
        }
        
        confidence_scores = []
        
        for rec in recommendations:
            priority = rec.get('priority', 'Low')
            status = rec.get('status', 'Active')
            savings = float(rec.get('estimated_savings', 0))
            confidence = float(rec.get('confidence_score', 0))
            
            # Count by priority
            if priority in recommendation_stats['by_priority']:
                recommendation_stats['by_priority'][priority] += 1
            
            # Count by status
            if status not in recommendation_stats['by_status']:
                recommendation_stats['by_status'][status] = 0
            recommendation_stats['by_status'][status] += 1
            
            # Sum potential savings
            recommendation_stats['total_potential_savings'] += savings
            
            # Collect confidence scores
            if confidence > 0:
                confidence_scores.append(confidence)
            
            # Track top recommendations
            if savings > 1.0:
                recommendation_stats['top_recommendations'].append({
                    'recommendation_id': rec['recommendation_id'],
                    'resource_id': rec['resource_id'],
                    'service_type': rec['service_type'],
                    'estimated_savings': savings,
                    'priority': priority,
                    'confidence_score': confidence
                })
        
        if confidence_scores:
            recommendation_stats['average_confidence'] = statistics.mean(confidence_scores)
        
        recommendation_stats['top_recommendations'].sort(
            key=lambda x: x['estimated_savings'], reverse=True
        )
        
        logger.info(f"Recommendation effectiveness analysis completed")
        return recommendation_stats
        
    except Exception as e:
        logger.error(f"Error in recommendation effectiveness analysis: {str(e)}")
        return {}

def detect_cost_anomalies():
    """Detect unusual cost patterns"""
    try:
        logger.info("Detecting cost anomalies...")
        
        response = usage_table.scan()
        usage_data = response['Items']
        
        anomalies = []
        resource_costs = {}
        
        for record in usage_data:
            resource_id = record['resource_id']
            cost = float(record['unblended_cost'])
            
            if resource_id not in resource_costs:
                resource_costs[resource_id] = []
            resource_costs[resource_id].append(cost)
        
        # Detect anomalies
        for resource_id, costs in resource_costs.items():
            if len(costs) > 1:
                avg_cost = statistics.mean(costs)
                max_cost = max(costs)
                
                # Cost spike detection
                if max_cost > avg_cost * 3 and avg_cost > 0.1:
                    anomalies.append({
                        'type': 'cost_spike',
                        'resource_id': resource_id,
                        'average_cost': avg_cost,
                        'spike_cost': max_cost,
                        'severity': 'High' if max_cost > avg_cost * 5 else 'Medium',
                        'detected_at': datetime.now().isoformat()
                    })
        
        anomaly_summary = {
            'anomalies': anomalies,
            'total_anomalies': len(anomalies),
            'high_severity': len([a for a in anomalies if a['severity'] == 'High']),
            'medium_severity': len([a for a in anomalies if a['severity'] == 'Medium'])
        }
        
        logger.info(f"Anomaly detection completed: {len(anomalies)} anomalies detected")
        return anomaly_summary
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {str(e)}")
        return {}

def generate_weekly_summary():
    """Generate a comprehensive weekly summary"""
    try:
        logger.info("Generating weekly summary...")
        
        # Get data from last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = usage_table.scan(
            FilterExpression=Attr('timestamp').between(
                start_date.isoformat(),
                end_date.isoformat()
            )
        )
        
        usage_data = response['Items']
        
        # Calculate weekly metrics
        total_cost = sum(float(record['unblended_cost']) for record in usage_data)
        total_usage = sum(float(record['usage_amount']) for record in usage_data)
        unique_resources = len(set(record['resource_id'] for record in usage_data))
        unique_services = len(set(record['service_type'] for record in usage_data))
        
        # Get active recommendations
        rec_response = recommendations_table.scan(
            FilterExpression=Attr('status').eq('Active')
        )
        active_recommendations = rec_response['Items']
        
        weekly_summary = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days_analyzed': 7
            },
            'cost_metrics': {
                'total_cost': total_cost,
                'average_daily_cost': total_cost / 7,
                'total_usage_units': total_usage
            },
            'resource_metrics': {
                'unique_resources': unique_resources,
                'unique_services': unique_services,
                'average_cost_per_resource': total_cost / unique_resources if unique_resources > 0 else 0
            },
            'recommendations': {
                'active_count': len(active_recommendations),
                'total_potential_savings': sum(float(rec.get('estimated_savings', 0)) for rec in active_recommendations),
                'high_priority_count': len([rec for rec in active_recommendations if rec.get('priority') == 'High'])
            },
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info("Weekly summary generated successfully")
        return weekly_summary
        
    except Exception as e:
        logger.error(f"Error generating weekly summary: {str(e)}")
        return {}

def prepare_ml_features():
    """Prepare features for machine learning models"""
    try:
        logger.info("Preparing ML features...")
        
        response = usage_table.scan()
        usage_data = response['Items']
        
        ml_features = []
        resource_data = {}
        
        for record in usage_data:
            resource_id = record['resource_id']
            if resource_id not in resource_data:
                resource_data[resource_id] = []
            resource_data[resource_id].append(record)
        
        # Create feature vectors
        for resource_id, records in resource_data.items():
            if len(records) > 0:
                total_cost = sum(float(r['unblended_cost']) for r in records)
                total_usage = sum(float(r['usage_amount']) for r in records)
                avg_cost = total_cost / len(records)
                avg_usage = total_usage / len(records)
                
                latest_record = max(records, key=lambda x: x['timestamp'])
                
                features = {
                    'resource_id': resource_id,
                    'service_type': latest_record['service_type'],
                    'instance_type': latest_record['instance_type'],
                    'availability_zone': latest_record['availability_zone'],
                    'region': latest_record['region'],
                    'total_cost': total_cost,
                    'average_cost': avg_cost,
                    'total_usage': total_usage,
                    'average_usage': avg_usage,
                    'usage_frequency': len(records),
                    'cost_per_usage_unit': total_cost / total_usage if total_usage > 0 else 0,
                    'days_active': len(set(r['timestamp'][:10] for r in records)),
                    'last_seen': latest_record['timestamp'],
                    'is_high_cost': 1 if total_cost > 1.0 else 0,
                    'is_low_utilization': 1 if avg_usage < 10 else 0,
                    'cost_category': 'high' if total_cost > 2.0 else 'medium' if total_cost > 0.5 else 'low'
                }
                
                ml_features.append(features)
        
        ml_summary = {
            'features': ml_features,
            'feature_count': len(ml_features),
            'feature_names': list(ml_features[0].keys()) if ml_features else [],
            'prepared_at': datetime.now().isoformat()
        }
        
        logger.info(f"ML features prepared for {len(ml_features)} resources")
        return ml_summary
        
    except Exception as e:
        logger.error(f"Error preparing ML features: {str(e)}")
        return {}

def store_analytics_results_s3(analytics_results):
    """Store analytics results in S3 for future use"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"analytics-report-{timestamp}.json"
        
        # Convert Decimal objects to float for JSON serialization
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decimal_to_float(v) for v in obj]
            return obj
        
        analytics_json = json.dumps(decimal_to_float(analytics_results), indent=2)
        
        # Upload to S3
        s3_client.put_object(
            Bucket='cwd-cost-usage-reports-as-2025',
            Key=f'analytics/{file_name}',
            Body=analytics_json,
            ContentType='application/json'
        )
        
        logger.info(f"Analytics results stored in S3: analytics/{file_name}")
        
    except Exception as e:
        logger.error(f"Error storing analytics results: {str(e)}")