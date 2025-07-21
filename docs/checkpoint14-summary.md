✅ Checkpoint 14 Summary: CloudWatch Metrics & SNS Alert Integration
📌 Objective
Enable real-time monitoring and alerting for cloud waste by:

Publishing custom CloudWatch metrics from the analyze_waste_patterns function

Sending SNS alerts for high-priority waste recommendations

📁 Files Modified
src/lambda-functions/cwd-data-collector.py

🔧 Changes Implemented
✅ Imported boto3 SNS and CloudWatch clients.

✅ Defined SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:<account-id>:cloud-waste-alerts'.

✅ Inside analyze_waste_patterns():

Published a CloudWatch metric:

Namespace: CloudWasteDetector

Metric: WasteAlert

Dimensions: ResourceId, Priority

Value: wastage_score

Sent an SNS alert with:

📬 Resource ID

💰 Cost

📊 Wastage Score

⚠️ Priority

📝 Recommendation Summary

📊 Output Observed
Custom metrics WasteAlert, WasteAlertsCount, and DailyWastageScore are visible in CloudWatch > Metrics.

Received SNS email notifications on high-waste alerts.

💸 Cost Control
All metric submissions and alerts operate within Free Tier as:

PutMetricData is free for custom metrics (up to 10k per month).

SNS email alerts are free (first 1,000/month).

🔒 IAM Permission Requirements
The Lambda execution role must have the following permissions:

json
Copy
Edit
{
  "Effect": "Allow",
  "Action": [
    "cloudwatch:PutMetricData",
    "sns:Publish"
  ],
  "Resource": "*"
}
🧪 Test Result
Successfully invoked the Lambda with test_direct, resulting in:

📦 3 processed records

🧠 2 waste recommendations

📈 2 CloudWatch metrics published

✉️ 1 SNS alert received

