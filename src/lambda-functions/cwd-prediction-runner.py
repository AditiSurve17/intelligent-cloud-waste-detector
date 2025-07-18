import boto3
import json
from datetime import datetime
from decimal import Decimal

s3 = boto3.client('s3', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

BUCKET = 'cwd-cost-usage-reports-as-2025'
PREDICTION_TABLE = 'cwd-daily-predictions'

def lambda_handler(event, context):
    try:
        # Step 1: Load latest Prophet & ARIMA results
        prophet_key = get_latest_key('ml-results/prophet_results_')
        arima_key = get_latest_key('ml-results/arima_results_')

        prophet = load_json_from_s3(prophet_key)
        arima = load_json_from_s3(arima_key)

        # Step 2: Calculate ensemble prediction
        p_avg = prophet['forecast_summary']['avg_predicted_cost']
        a_avg = arima['forecast_summary']['avg_predicted_cost']
        p_mape = prophet['performance_metrics']['mape']
        a_mape = arima['performance_metrics']['mape']

        w_p = (1 / p_mape)
        w_a = (1 / a_mape)
        total_w = w_p + w_a
        w_p /= total_w
        w_a /= total_w

        ensemble = (p_avg * w_p + a_avg * w_a)
        agreement = 100 - abs(p_avg - a_avg) / max(p_avg, a_avg) * 100

        result = {
            'prediction_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'ensemble_prediction': round(ensemble, 3),
            'confidence_score': round(agreement, 1),
            'trend': 'decreasing' if ensemble < 2.50 else 'stable',
            'recommendation': 'monitor' if agreement > 70 else 'investigate',
            'forecast_range': {
                'min': round(min(p_avg, a_avg), 2),
                'max': round(max(p_avg, a_avg), 2)
            },
            'created_at': datetime.utcnow().isoformat()
        }

        # Step 3: Store in DynamoDB
        table = dynamodb.Table(PREDICTION_TABLE)
        table.put_item(Item=json.loads(json.dumps(result), parse_float=Decimal))

        # Step 4: Store in S3
        file_key = f"predictions/prediction-{result['prediction_date'].replace('-', '')}.json"
        s3.put_object(
            Bucket=BUCKET,
            Key=file_key,
            Body=json.dumps(result, indent=2),
            ContentType='application/json'
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Ensemble prediction saved',
                'prediction': result
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_latest_key(prefix):
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    if 'Contents' not in response:
        raise Exception(f"No files found for prefix {prefix}")
    return sorted([obj['Key'] for obj in response['Contents']])[-1]

def load_json_from_s3(key):
    response = s3.get_object(Bucket=BUCKET, Key=key)
    return json.loads(response['Body'].read().decode('utf-8'))
