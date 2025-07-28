import json
import boto3
from boto3.dynamodb.conditions import Attr
import decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('cwd-waste-recommendations')

# Custom encoder to handle Decimal serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, OPTIONS"
    }

    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": ""
        }

    try:
        # Scan for active recommendations
        response = table.scan(
            FilterExpression=Attr('status').eq('Active')
        )
        items = response.get('Items', [])

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "count": len(items),
                "recommendations": items
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": f"Failed to fetch recommendations: {str(e)}"})
        }
