# ✅ Checkpoint 11 Complete: Alert Notification System

## 📌 Objective
Enable email alerts for forecasted AWS cost spikes using SNS and Lambda.

---

## ✅ Implementation Summary

- Created **SNS Topic**: `cloud-waste-alerts`
- Subscribed user email (confirmed)
- Built `cwd-prediction-alert` Lambda
- Integrated alert logic with cost predictions from S3
- Configured IAM role for `SNS:Publish`
- Successfully received test email 🚀

---

## 🔒 Security

- IAM policy allows **only `sns:Publish`** to `cloud-waste-alerts`
- Alerts are triggered **only on ML-defined high-cost days**

---

## 💰 Cost

- SNS Email: $0.00 (Free Tier)
- Lambda Invocations: $0.00
- S3 Reads: <$0.01, covered by Free Tier

---

## 📩 Sample Alert (Received)

