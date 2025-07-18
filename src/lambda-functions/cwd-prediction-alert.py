import boto3
import os
import json
from datetime import datetime

SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:YOUR_ACCOUNT_ID:cwd-prediction-alerts'  # Replace this

def lambda_handler(event, context):
    """
    This function is triggered by cwd-prediction-runner when a high-cost forecast is detected.
    It sends an SNS alert with forecast summary.
    """

    try:
        prediction_summary = event.get('prediction_summary', {})
        confidence_score = prediction_summary.get('confidence_score')
        forecast = prediction_summary.get('forecast')
        
        message = f"""
🚨 High Cost Forecast Detected!
==============================
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 Forecasted Cost: ${forecast:.2f}
📊 Confidence Score: {confidence_score:.1f}%
📈 Model Prediction: Ensemble
==============================
        """

        sns = boto3.client('sns', region_name='ap-south-1')
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='[CloudWasteDetector] ALERT: High Cost Forecast!',
            Message=message.strip()
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'SNS Alert Sent', 'prediction': forecast})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
