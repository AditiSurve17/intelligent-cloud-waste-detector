import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import decimal
from decimal import Decimal

# Custom JSON encoder to handle Decimal and nested DynamoDB types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: self.default(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.default(i) for i in obj]
        return super(DecimalEncoder, self).default(obj)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('cwd-daily-predictions')

def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, OPTIONS"
    }

    # Handle CORS
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": ""
        }

    try:
        # Scan all records to find latest prediction
        response = table.scan()
        items = response.get('Items', [])

        if not items:
            return {
                "statusCode": 404,
                "headers": cors_headers,
                "body": json.dumps({"error": "No prediction data found."})
            }

        # Sort by prediction_date descending
        latest = sorted(items, key=lambda x: x['prediction_date'], reverse=True)[0]

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"latest_prediction": latest}, cls=DecimalEncoder)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": f"Failed to fetch prediction: {str(e)}"})
        }
