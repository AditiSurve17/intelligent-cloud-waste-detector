# ✅ Checkpoint 17 – Terraform Generator Lambda (Postman-Based API)

## 🎯 Objective
Create a Lambda function that:
- Fetches **terminated** AWS resources from DynamoDB
- Generates corresponding **Terraform delete blocks**
- Uploads `.tf` files to S3
- Exposes both functionalities via API Gateway
- Can be fully tested using **Postman (no frontend required)**

---

## ✅ Completed Implementation

### 1. Lambda: `cwd-terraform-generator`
- Scans DynamoDB table `cwd-waste-recommendations` for `status = "Terminated"`
- Generates `.tf` delete blocks for:
  - `aws_instance` (EC2)
  - `aws_ebs_volume` (EBS)
  - `aws_s3_bucket` (S3)
  - `aws_db_instance` (RDS)
  - `aws_lambda_function` (Lambda)
- Uploads generated `.tf` files to:
s3://cwd-cost-usage-reports-as-2025/terraform-scripts/

markdown
Copy
Edit

### 2. API Gateway Setup
- **Resource path**: `/terraform`
- **Methods**:
- `GET /terraform`: Lists all `status=Terminated` resources
- `POST /terraform`: Accepts `resourceId` and generates a `.tf` file
- **CORS** enabled for all methods
- Tested using **Postman**

---

## 🔁 API Testing via Postman

### 🔹 GET /terraform
- **URL**:  
https://<api-id>.execute-api.ap-south-1.amazonaws.com/prod/terraform

markdown
Copy
Edit
- **Returns**: All terminated resource recommendations

### 🔹 POST /terraform
- **Request Body**:
```json
{
"resourceId": "i-0dummy123456789abc"
}
Returns:

json
Copy
Edit
{
  "terraform": "Terraform block...",
  "resource_id": "i-0dummy123456789abc",
  "resource_type": "ec2",
  "s3_location": "https://cwd-cost-usage-reports-as-2025.s3.amazonaws.com/terraform-scripts/ec2_i-0dummy123456789abc.tf",
  "generated_at": "2025-07-26T..."
}
📁 Resources Used
Resource Type	Name / Path
Lambda	cwd-terraform-generator
API Gateway	POST /terraform, GET /terraform
S3 Bucket	cwd-cost-usage-reports-as-2025
DynamoDB	cwd-waste-recommendations

🔐 IAM Permissions (Lambda Role)
json
Copy
Edit
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
✅ Outcome
Fully functional Terraform block generator

Zero UI dependency – tested via Postman

Terraform blocks stored and downloadable from S3

Easy to extend with new resource types or batch generation

Checkpoint 17: COMPLETE ✅