# ✅ Checkpoint 15 – CloudWatch Metrics & Dashboard

### 🎯 Objective
Visualize resource wastage alerts in AWS CloudWatch to monitor high-priority inefficient resources using custom metrics and dashboards.

---

### 🔧 Tasks Completed
- Published custom CloudWatch metric `WasteAlert` from Lambda.
- Metric includes dimensions: `Priority` and `ResourceId`.
- Confirmed successful ingestion of 5 metric points.
- Created **CloudWatch Dashboard**: `CloudWaste-Insights`
- Added widget: **Line graph** visualizing `WasteAlert` metric per resource by priority.

---

### 📊 Widget Details
- **Metric**: `CloudWasteDetector/WasteAlert`
- **Split by**: `Priority`, `ResourceId`
- **Widget Type**: Line chart
- **Monitored Resources**:
  - EC2 Instance: `i-099988...`
  - EBS Volume: `vol-09876...`
  - Sample/Unknown: `unknown-resource-001`, `arn:aws:dynamodb...`

---

### ✅ Outcome
A real-time, insightful dashboard that visualizes resource waste, enables monitoring of optimization impact, and assists in proactive cloud cost governance.

