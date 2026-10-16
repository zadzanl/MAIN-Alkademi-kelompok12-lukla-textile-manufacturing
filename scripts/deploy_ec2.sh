#!/bin/bash
set -e

# ==============================================================================
# Lukla Operations Engine — Automated EC2 Deployment Script
# Targets: Amazon Linux 2023 (Alkademi Hackathon EC2 Template)
# ==============================================================================

echo "=========================================="
echo " Starting Lukla EC2 Auto-Deployment"
echo "=========================================="

# 1. Wait for system cloud-init bootstrap to finish
echo "--> Checking cloud-init status..."
if command -v cloud-init >/dev/null 2>&1; then
    sudo cloud-init status --wait || true
fi

# 2. Setup PostgreSQL 15 if not already running
echo "--> Verifying PostgreSQL 15..."
if ! command -v psql >/dev/null 2>&1; then
    echo "    Installing postgresql15-server..."
    sudo dnf update -y
    sudo dnf install -y postgresql15-server postgresql15
fi

# Initialize DB if not initialized
if [ ! -d "/var/lib/pgsql/data/base" ]; then
    echo "    Initializing PostgreSQL data directory..."
    sudo postgresql-setup --initdb || true
fi

# Enable and start service
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create Database and Application User if not exists
echo "    Configuring myappdb and myappuser..."
sudo -u postgres psql -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'myappuser') THEN
        CREATE USER myappuser WITH ENCRYPTED PASSWORD 'password_rahasia_kamu';
    END IF;
END
\$\$;
"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'myappdb'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE DATABASE myappdb OWNER myappuser;"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE myappdb TO myappuser;"
sudo -u postgres psql -c "ALTER DATABASE myappdb OWNER TO myappuser;"

# 3. Setup Python Virtual Environment and Dependencies
echo "--> Setting up Python environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements.txt

# 4. Generate Production .env (No secret AWS keys; IAM Role auto-auth)
echo "--> Generating .env configuration..."
cat << 'EOF' > .env
# Database configuration
DATABASE_URL=postgresql://myappuser:password_rahasia_kamu@127.0.0.1:5432/myappdb
LUKLA_APP_DATABASE_URL=postgresql://myappuser:password_rahasia_kamu@127.0.0.1:5432/myappdb

# Amazon Bedrock LLM configuration (Role-based via IMDS)
COPILOT_DEFAULT_PROVIDER=bedrock
AWS_REGION=us-east-1
COPILOT_MODEL_NAME=us.amazon.nova-micro-v1:0
BEDROCK_MODEL_ID=us.amazon.nova-micro-v1:0
COPILOT_DEMO_MODE=false
AI_COPILOT_ENABLED=true

# Security
SECRET_KEY=lukla-secret-super-secure-key-for-jwt-signing-hs256
EOF

# 5. Run Database Migrations
echo "--> Running schema migrations on PostgreSQL..."
python3 scripts/init_ec2_db.py

# 6. Stop previous instance if running
echo "--> Restarting application process on port 3000..."
if [ -f "$HOME/app.pid" ]; then
    OLD_PID=$(cat "$HOME/app.pid" 2>/dev/null || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "    Stopping previous process (PID: $OLD_PID)..."
        kill "$OLD_PID" || true
        sleep 2
    fi
fi
pkill -f "uvicorn main:app" 2>/dev/null || true

# 7. Start unified application on 0.0.0.0:3000
nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port 3000 > "$HOME/app.log" 2>&1 &
APP_PID=$!
echo $APP_PID > "$HOME/app.pid"
echo "    Started main:app with PID $APP_PID (logs in ~/app.log)"

# 8. Verification probe
echo "--> Probing localhost:3000..."
sleep 3
if curl -s -I http://localhost:3000 | grep -q "200 OK"; then
    echo "=========================================================="
    echo " SUCCESS: Application is running on 0.0.0.0:3000!"
    echo "=========================================================="
else
    echo "    Warning: Check ~/app.log for details:"
    tail -n 20 "$HOME/app.log"
fi

# Detect Public IP
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" 2>/dev/null || true)
if [ -n "$TOKEN" ]; then
    PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
else
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo "<YOUR_EC2_PUBLIC_IP>")
fi

echo ""
echo "Deployment Details:"
echo "----------------------------------------------------------"
echo " Public IPv4  : $PUBLIC_IP"
echo " Port         : 3000"
echo " Portal URL   : http://${PUBLIC_IP}:3000/"
echo " AI Copilot   : http://${PUBLIC_IP}:3000/copilot"
echo " Sampling App : http://${PUBLIC_IP}:3000/sampling/"
echo " ERP UI Mock  : http://${PUBLIC_IP}:3000/ui"
echo " API Docs     : http://${PUBLIC_IP}:3000/docs"
echo "----------------------------------------------------------"
echo "Form Pelaporan: https://forms.gle/v6wZutpAhr8r9v4B7"
echo "=========================================================="
