# Post-Planning & Post-Implementation Handoff: EC2 Unified Deployment

> [!IMPORTANT]
> **OPERATIONAL HANDOFF DIRECTIVE:**
> This document is the authoritative handoff specification for the downstream engineer or autonomous agent tasked with executing Phase 5 (EC2 instance launch, remote deployment, and submission).
> All codebase modifications, provider implementations, test suites, and deployment scripts have been **verified, committed, and pushed to `origin/master` (commit `d4e56b2`)**.

---

## 1. Handoff Baseline & Current State

- **Mainline Branch:** `master`
- **Mainline Commit:** `d4e56b2` (`feat(ec2): prepare unified deployment with Bedrock provider, root entrypoint, and automated setup`)
- **Remote Repository:** `https://github.com/zadzanl/MAIN-Alkademi-kelompok12-lukla-textile-manufacturing.git`
- **Verified AWS CLI Profile:** Authenticated as `arn:aws:iam::820242904049:user/student_12` in region `ap-southeast-1`.
- **Target Launch Template:** `main-ec2-template` (`lt-00e4f5effa1c630ad`), Version 1.
- **Mandatory Instance Tag:** `Key=Owner,Value=student_12`.
- **Security Group:** `sg-0ee4f83cd129e794a` (Inbound open for TCP ports 80 & 3000 to `0.0.0.0/0`).
- **Attached IAM Role:** `MainEC2Role` (Permissions for Amazon Bedrock Runtime in `us-east-1`).
- **Current Hold Status:** Step 5 is on standby awaiting operator launch approval.

---

## 2. Phase 5 Execution Runbook (Step-by-Step)

When instructed to proceed with deployment, follow these exact procedural steps:

### Step 5.1 — Launch the EC2 Instance via AWS CLI
Execute the verified launch command:
```powershell
aws ec2 run-instances `
  --launch-template LaunchTemplateId=lt-00e4f5effa1c630ad `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Owner,Value=student_12}]" `
  --region ap-southeast-1
```
*Expected Output:* JSON payload returning `InstanceId` (e.g. `i-0abcdef1234567890`) with initial state `"pending"`.

### Step 5.2 — Wait for Instance Status Checks
Query status until state is `running` and checks pass:
```powershell
aws ec2 wait instance-status-ok `
  --instance-ids <INSTANCE_ID> `
  --region ap-southeast-1
```
*(Alternatively, query via `aws ec2 describe-instance-status --instance-ids <INSTANCE_ID> --region ap-southeast-1`).*

### Step 5.3 — Capture the Public IPv4 Address
Retrieve the public IP assigned to the instance:
```powershell
aws ec2 describe-instances `
  --instance-ids <INSTANCE_ID> `
  --query "Reservations[0].Instances[0].PublicIpAddress" `
  --output text `
  --region ap-southeast-1
```
Record this IP (referred to below as `<PUBLIC_IP>`).

### Step 5.4 — Connect via AWS Console Session Manager
1. Log in to AWS Console via the mentor-provided link.
2. Select Region **Singapore (`ap-southeast-1`)** in the top-right corner.
3. Open **EC2 > Instances** and select your running instance (tagged `Owner: student_12`).
4. Click **Connect** > select **Session Manager** tab > click **Connect**.
*(A web-based interactive bash shell will open in a new tab).*

### Step 5.5 — Run the Automated Deployment Script
In the Session Manager terminal, switch to `ec2-user` and run:
```bash
# Switch to ec2-user
sudo su - ec2-user

# Wait for initial bootstrap to complete (Status should report done)
cloud-init status --wait

# Clone repository from master
git clone https://github.com/zadzanl/MAIN-Alkademi-kelompok12-lukla-textile-manufacturing.git
cd MAIN-Alkademi-kelompok12-lukla-textile-manufacturing

# Ensure deployment script has executable permissions
chmod +x scripts/deploy_ec2.sh

# Run the automated deployment
./scripts/deploy_ec2.sh
```

The script will automatically:
1. Verify and configure PostgreSQL 15 on `127.0.0.1:5432`.
2. Create database `myappdb` and user `myappuser` with password `password_rahasia_kamu`.
3. Create `.venv` and install `requirements.txt`.
4. Generate the production `.env` (configured for Bedrock `us-east-1` with no secrets).
5. Apply database migrations 001 through 013 via `scripts/init_ec2_db.py`.
6. Start `uvicorn main:app --host 0.0.0.0 --port 3000` via `nohup` (logs in `~/app.log`, PID in `~/app.pid`).
7. Perform local health probe (`curl -I http://localhost:3000`).

---

## 3. Post-Deployment Verification Matrix

From your local machine or browser, verify each endpoint:

| Test Target | Target URL / Command | Expected Behavior |
|---|---|---|
| **Root Health Probe** | `curl -I http://<PUBLIC_IP>:3000/` | HTTP/1.1 200 OK |
| **Operations Hub Portal** | `http://<PUBLIC_IP>:3000/` in browser | Renders dark-mode portal with links to all apps |
| **AI Copilot Interface** | `http://<PUBLIC_IP>:3000/copilot` | Renders chat interface; query *"Berapa stok kain fleece?"* invokes Bedrock Nova Micro and returns live stock answer |
| **Sampling & Spec R&D** | `http://<PUBLIC_IP>:3000/sampling/` | Renders Time Study and Spec Versioning dashboard |
| **ERP Operations Mock** | `http://<PUBLIC_IP>:3000/ui` | Renders the full garment factory UI prototype |
| **OpenAPI Documentation** | `http://<PUBLIC_IP>:3000/docs` | Renders interactive Swagger UI with all 69+ endpoints |

---

## 4. Reporting Form Submission

Once verified, immediately submit the deployment record to the Alkademi mandatory form:
- **URL:** [https://forms.gle/v6wZutpAhr8r9v4B7](https://forms.gle/v6wZutpAhr8r9v4B7)
- **Nama Kelompok:** Kelompok 12 (Lukla Textile Manufacturing)
- **IP EC2:** `<PUBLIC_IP>`
- **Port:** `3000`

---

## 5. Failure Triage & Troubleshooting Runbook

### Issue A: `not authorized to perform ec2:RunInstances`
- **Cause:** Missing or misspelled `Owner` tag, or incorrect AWS Region.
- **Remedy:** Ensure `--region ap-southeast-1` and `--tag-specifications "ResourceType=instance,Tags=[{Key=Owner,Value=student_12}]"` match exactly.

### Issue B: Browser timeout when visiting `http://<PUBLIC_IP>:3000`
- **Cause 1:** Application listening on `127.0.0.1` instead of `0.0.0.0`.
  - *Fix:* Ensure uvicorn runs with `--host 0.0.0.0`.
- **Cause 2:** Protocol mismatch.
  - *Fix:* Ensure using `http://` (not `https://`). SSL is not terminated on port 3000.
- **Cause 3:** Instance was restarted and IP changed.
  - *Fix:* Check `aws ec2 describe-instances` for the updated Public IP.

### Issue C: `Bedrock AccessDeniedException` or `ResourceNotFoundException`
- **Cause:** AWS SDK attempting to call Bedrock in Singapore (`ap-southeast-1`) where models are not assigned, or incorrect model ID.
- **Remedy:** Verify `.env` contains:
  ```env
  COPILOT_DEFAULT_PROVIDER=bedrock
  AWS_REGION=us-east-1
  BEDROCK_MODEL_ID=us.amazon.nova-micro-v1:0
  ```
  Check `tail -n 50 ~/app.log` for raw AWS exception trace.

### Issue D: Process killed during startup (`Killed`)
- **Cause:** RAM starvation on 1 GB instance.
- **Remedy:** Run `free -h` in Session Manager. If swap is 0, activate the pre-allocated swap:
  ```bash
  sudo mkswap /swapfile 2>/dev/null || true
  sudo swapon /swapfile 2>/dev/null || true
  ```

---

## 6. Delegation Gate Stop Conditions

> **DELEGATION GATE ENFORCEMENT:**
> The downstream worker or agent must immediately halt and escalate with:
> `BLOCKED: <what differs> | <evidence> | <question>`
> under any of the following conditions:
> 1. The Launch Template `lt-00e4f5effa1c630ad` is deleted, modified, or unavailable.
> 2. The IAM credentials for `student_12` are revoked or return `AccessDenied` on `RunInstances`.
> 3. The public IPv4 address assigned to the instance fails to respond to TCP port 3000 after `scripts/deploy_ec2.sh` finishes without error.
> 4. Upstream maintainers mandate modifying core database schemas (001–012).
