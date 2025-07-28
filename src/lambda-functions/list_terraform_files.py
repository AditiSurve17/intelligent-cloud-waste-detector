import json
import boto3

# S3 bucket and prefix
BUCKET_NAME = 'cwd-cost-usage-reports-as-2025'
FOLDER_PREFIX = 'terraform/generated/'

def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET, OPTIONS"
    }

    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": ""
        }

    try:
        s3 = boto3.client('s3')

        # List objects in S3 folder
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=FOLDER_PREFIX
        )

        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if key.endswith('.tf'):
                    files.append({
                        'filename': key.split('/')[-1],
                        'path': key,
                        'url': f'https://{BUCKET_NAME}.s3.amazonaws.com/{key}'
                    })

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"terraform_files": files})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": f"Failed to list files: {str(e)}"})
        }
