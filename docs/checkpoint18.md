📍 Objective
Integrate a system that generates Terraform delete blocks for terminated cloud resources and exposes it through an API endpoint accessible from the frontend.

🔧 Work Completed
Lambda Function for Terraform Generation

A POST-based Lambda function was developed to:

Query DynamoDB for status = "Terminated" resources.

Auto-generate Terraform delete blocks (aws_instance, aws_ebs_volume, etc.).

Upload the generated .tf file to S3 with a timestamped name.

Return success message with S3 file path.

API Gateway Setup

Created resource path: /terraform

Methods configured:

POST /terraform → triggers Terraform generation Lambda

GET /terraform → fetches current terminated resource recommendations

Enabled CORS for frontend access.

Integrated test tools inside API Gateway to confirm request/response success.

Lambda Function for GET Method

Returns structured recommendations as:

json
Copy
Edit
{
  "recommendations": [
    {
      "resourceName": "i_123456",
      "resourceType": "ec2",
      "reason": "Idle for 14 days"
    }
  ]
}
Enables frontend to fetch and display recommendations.

Frontend Integration (React)

Updated RecommendationCard.js to:

Render resource cards.

On “Generate Locally”, create dummy Terraform block.

On “Generate via API”, trigger POST /terraform and copy backend-generated Terraform block to clipboard.

Used fetchRecommendations.js to call GET /terraform and render dynamic cards.

DynamoDB Table Queried

Table: cwd-waste-recommendations

Fields used:

resource_id, service_type, status, region, reason

S3 Upload Path

Bucket: cwd-cost-usage-reports-as-2025

Key Prefix: terraform-scripts/terraform-delete-<timestamp>.tf

🧪 Testing
Both GET and POST methods tested through:

API Gateway console

React frontend interface

Clipboard copying functionality verified

