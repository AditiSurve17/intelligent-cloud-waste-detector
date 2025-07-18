# File: prediction-api/app.py

from flask import Flask, jsonify
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime

app = Flask(__name__)

# AWS Configuration
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table_name = 'cwd-daily-predictions'
table = dynamodb.Table(table_name)

@app.route('/')
def root():
    return jsonify({"message": "🌤️ Cloud Waste Prediction API is live"})

@app.route('/api/prediction', methods=['GET'])
def get_latest_prediction():
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')

        response = table.query(
            KeyConditionExpression=Key('prediction_date').eq(today),
            ScanIndexForward=False,
            Limit=1
        )

        if response['Items']:
            item = response['Items'][0]

            # Convert Decimal to float
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)

            return jsonify({
                "status": "success",
                "prediction": item
            })
        else:
            return jsonify({"status": "error", "message": "No prediction found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
