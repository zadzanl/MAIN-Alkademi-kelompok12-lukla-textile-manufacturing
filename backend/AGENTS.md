# Backend Agent Guidelines & Security Memo

## Demo OpenRouter API Key Memo

> **Date:** 2026-10-16  
> **Status:** APPROVED DEMO CEILING (Active for Hackathon Evaluation)  
> **Classification:** Low-Risk Controlled Demo Credential  

### 1. Context & Purpose
The backend contains a hardcoded fallback API key for the Operations Copilot service (`backend/app/api/v1/copilot.py` and `backend/app/copilot/config.py`). This key was intentionally provisioned to provide a seamless, zero-configuration evaluation experience for hackathon judges and evaluators without requiring them to supply personal LLM API keys or configure local `.env` files.

### 2. Security Constraints & Safety Envelope
- **Free Models Only:** The key is strictly restricted on the OpenRouter dashboard to free-tier model routes (defaulting to `nvidia/nemotron-3-super-120b-a12b:free`).
- **Hard Spend Limit:** Account credit and lifetime usage cap is locked at **\$0.10 USD**.
- **No Production Blast Radius:** This key possesses zero privileges in AWS, PostgreSQL, or internal ERP systems. It cannot be used to incur billing beyond the \$0.10 ceiling or access private data.

### 3. Tracked Code Anchors
- `backend/app/api/v1/copilot.py` (`HARDCODED_DEMO_KEY`, `DEMO_COPILOT_SETTINGS`)
- `backend/app/copilot/config.py` (`COPILOT_API_KEY`, `COPILOT_MODEL_NAME`)
- `scripts/deploy_ec2.sh` (`OPENROUTER_API_KEY`)

### 4. AWS EC2 Production & Evaluation Guidance
When deploying to AWS EC2 per `Deploy aplikasi ke EC2.pdf`:
- **Amazon Bedrock Mode:** Set environment variable `COPILOT_DEFAULT_PROVIDER="bedrock"` to use the EC2 instance's attached IAM Role (`us.amazon.nova-micro-v1:0` in `us-east-1`). No API key is required or used in Bedrock mode.
- **OpenRouter Fallback:** If Bedrock is unavailable or not attached, the backend gracefully falls back to the free demo model via this low-risk token.
- **Post-Demo Decommissioning:** Decommission or rotate the key via the OpenRouter dashboard once hackathon evaluation concludes.
