# Lambda: cwd-terraform-generator

This Lambda function scans the DynamoDB table `cwd-waste-recommendations` for all resources with `status = "Terminated"` and generates a `.tf` Terraform configuration file for deletion.

### 📂 Output Location
- S3 Bucket: `cwd-cost-usage-reports-as-2025`
- Prefix: `terraform-scripts/terraform-delete-[timestamp].tf`

### 🔐 IAM Permissions (Minimum Required)

```json
{
  "Action": [
    "dynamodb:Scan",
    "s3:PutObject"
  ],
  "Resource": [
    "arn:aws:dynamodb:ap-south-1:<ACCOUNT_ID>:table/cwd-waste-recommendations",
    "arn:aws:s3:::cwd-cost-usage-reports-as-2025/terraform-scripts/*"
  ]
}
🧪 Test Example
Insert this into the cwd-waste-recommendations table:

json
Copy
Edit
{
  "recommendation_id": "test-terraform-dummy",
  "created_at": "2025-07-21T18:00:00Z",
  "status": "Terminated",
  "service_type": "ec2",
  "resource_id": "i-0dummy123456789abc",
  "region": "ap-south-1"
}