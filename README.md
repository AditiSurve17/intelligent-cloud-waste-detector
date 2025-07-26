# ☁️ Intelligent Cloud Resource Waste Detector

![AWS](https://img.shields.io/badge/AWS-Free%20Tier-orange?logo=amazon-aws)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Backend](https://img.shields.io/badge/API-Tested%20via-Postman-blue?logo=postman)
![Tech](https://img.shields.io/badge/ML%20Model-Prophet%2FARIMA%20Simulated-lightgrey)

A fully serverless system to automatically detect, forecast, and eliminate cloud resource wastage in AWS using Lambda, DynamoDB, CloudWatch, and ML forecasts — all within AWS **Free Tier limits**. No UI required — all APIs are testable via **Postman**.

---

## 📌 Project Objectives

- ✅ Ingest and process AWS Cost & Usage data
- ✅ Predict future cloud usage using time series forecasting (Prophet, ARIMA)
- ✅ Detect anomalies and generate intelligent waste-saving recommendations
- ✅ Auto-generate Terraform scripts for resource cleanup
- ✅ Monitor and send alerts via CloudWatch + SNS
- ✅ Postman-based API testing 


---

## 🧠 Key Features

| Feature                      | Description |
|-----------------------------|-------------|
| 🔁 **Automated Data Ingestion** | CUR data collected hourly via Lambda |
| 📊 **Forecasting Engine**       | ML predictions via Prophet/ARIMA simulated using CLI |
| 📉 **Anomaly & Trend Detection**| Detects unusual cloud cost spikes or drops |
| 🛠 **Terraform Script Generator**| Auto-generates `.tf` delete scripts for waste |
| 📨 **Alerts & Reports**         | Real-time + weekly summary alerts via SNS |
| 🔐 **Free Tier Optimized**      | All services are within AWS free usage limits |
| 🧪 **Postman Ready**            | Fully testable APIs with JSON payloads |

---

## 🧱 Tech Stack

- **AWS Services**: Lambda, S3, DynamoDB, CloudWatch, SNS, API Gateway
- **ML Engine**: Prophet, ARIMA (simulated via CLI, CloudShell)
- **Languages**: Python (Boto3), Bash
- **Tools**: Postman, Terraform, CloudShell
- **Monitoring**: CloudWatch Alarms + SNS Email Reports

---

## 🚀 API Endpoints

> All endpoints are deployed via **AWS API Gateway**  
> Replace `{api-url}` with your deployment base URL

| Method | Endpoint                            | Description                      |
|--------|-------------------------------------|----------------------------------|
| GET    | `/recommendations`                 | Get daily optimization tips      |
| GET    | `/analytics`                       | Get prediction + trend report    |
| GET    | `/terraform/files`                 | List generated `.tf` files       |
| GET    | `/terraform/download?file=name.tf` | Download specific Terraform file |

🧪 Test these using Postman or `curl`.


---

## 📦 Sample Output (from DynamoDB)

📬 Weekly Report Sample
Delivered via SNS topic cloud-waste-weekly-summary

✅ Total Spend Forecast

📉 Trend (Increasing/Decreasing)

🔍 Top 3 Cost Spikes

