# AWS Real-Time Cost Monitor

This repository contains a Python script to monitor AWS resource costs across all regions in real-time. It fetches details from various AWS services, estimates accrued costs, and predicts future expenses.

---

## Prerequisites

Before running the script, you need to set up an IAM role with the necessary permissions.

### Step 1: Create an IAM Role

1. Sign in to the **AWS Management Console**.
2. Navigate to **IAM (Identity and Access Management)**.
3. Click on **Roles** > **Create role**.
4. Select **AWS service** as the trusted entity type.
5. Under **Use case**, select **EC2** (if you are running this script from an EC2 instance).
6. Click **Next: Permissions**.

### Step 2: Attach Policy to the Role

1. Click on **Create policy**.
2. Go to the **JSON** tab and paste the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:Describe*",
                "s3:ListAllMyBuckets",
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "rds:Describe*",
                "lambda:ListFunctions",
                "eks:ListClusters",
                "cloudwatch:Describe*",
                "cloudwatch:Get*",
                "dynamodb:ListTables",
                "dynamodb:DescribeTable",
                "elasticloadbalancing:Describe*",
                "pricing:GetProducts",
                "iam:ListRoles",
                "iam:GetRole",
                "iam:ListPolicies",
                "ce:GetCostAndUsage"
            ],
            "Resource": "*"
        }
    ]
}
```

3. Click **Review policy**.
4. Name the policy as `CostMonitoringReadOnlyPolicy` and click **Create policy**.

### Step 3: Attach the Policy to the Role

1. Go back to the **Create Role** wizard.
2. Click **Refresh** and search for `CostMonitoringReadOnlyPolicy`.
3. Select the policy and click **Next: Tags** (optional).
4. Click **Next: Review**.
5. Name the role **CostMonitoringPermissionGiverRole**.
6. Click **Create role**.

### Step 4: Attach the Role to an EC2 Instance

1. Navigate to **EC2** in the AWS console.
2. Select your running instance.
3. Click **Actions** > **Security** > **Modify IAM Role**.
4. Select `CostMonitoringPermissionGiverRole` from the list.
5. Click **Update IAM Role**.

---

## Installation & Usage

### Clone the Repository

```bash
git clone https://github.com/chinmaya-chhatre/aws-realtime-cost-monitor.git
cd aws-realtime-cost-monitor
```

### Install Dependencies

Ensure you have Python 3 and `boto3` installed:

```bash
pip install boto3
```

### Run the Script

```bash
python3 fetch_all_regions_resources.py
```

---

## Output

After running the script, you will find:

1. **`aws_cost_prediction.csv`** - A CSV file with the cost breakdown.
2. **`aws_cost_prediction.log`** - A log file with execution details.
