#!/bin/bash
set -e

# ==============================================================================
# Lukla Operations Engine — Automated EC2 Deployment Script
# Targets: Amazon Linux 2023 deployment template
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
    sudo dnf install -y postgresql15-server postgresql15 postgresql15-contrib
elif [ ! -f "/usr/share/pgsql/extension/btree_gist.control" ]; then
    echo "    Installing postgresql15-contrib..."
    sudo dnf install -y postgresql15-contrib || true
fi

# Initialize DB if not initialized (use sudo test because /var/lib/pgsql is mode 700)
if ! sudo test -d "/var/lib/pgsql/data/base"; then
    echo "    Initializing PostgreSQL data directory..."
    sudo postgresql-setup --initdb || true
fi

# Configure pg_hba.conf to allow password (scram-sha-256 / md5) authentication over 127.0.0.1 and ::1 instead of ident
sudo sed -i -E 's/(127\.0\.0\.1\/32\s+)ident/\1scram-sha-256/g; s/(::1\/128\s+)ident/\1scram-sha-256/g' /var/lib/pgsql/data/pg_hba.conf

# Enable and restart service to apply pg_hba.conf
sudo systemctl enable postgresql
sudo systemctl restart postgresql

# Create Database, Application User, Runtime Role, and Extensions
echo "    Configuring myappdb, myappuser, lukla_app, and extensions..."
(
    cd /tmp
    sudo -u postgres psql -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'myappuser') THEN
        CREATE USER myappuser WITH ENCRYPTED PASSWORD 'password_rahasia_kamu' CREATEDB CREATEROLE;
    ELSE
        ALTER USER myappuser WITH CREATEDB CREATEROLE;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lukla_app') THEN
        CREATE ROLE lukla_app WITH LOGIN PASSWORD 'lukla_secret' NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END
\$\$;
"
    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'myappdb'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE myappdb OWNER myappuser;"

    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE myappdb TO myappuser;"
    sudo -u postgres psql -c "ALTER DATABASE myappdb OWNER TO myappuser;"
    sudo -u postgres psql -d myappdb -c "CREATE EXTENSION IF NOT EXISTS btree_gist;" || true
    sudo -u postgres psql -d myappdb -c "GRANT ALL ON SCHEMA public TO myappuser;"
)

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
configured_openrouter_key="${OPENROUTER_API_KEY:-}"
if [ -z "$configured_openrouter_key" ] && [ -f .env ]; then
    configured_openrouter_key="$(sed -n 's/^OPENROUTER_API_KEY=//p' .env | head -n 1)"
fi

cat << EOF > .env
# Database configuration
DATABASE_URL=postgresql://myappuser:password_rahasia_kamu@127.0.0.1:5432/myappdb
LUKLA_APP_DATABASE_URL=postgresql://myappuser:password_rahasia_kamu@127.0.0.1:5432/myappdb

# LLM configuration (free model default + Bedrock support)
COPILOT_DEFAULT_PROVIDER=openrouter
OPENROUTER_API_KEY=$configured_openrouter_key
COPILOT_MODEL_NAME=nvidia/nemotron-3-super-120b-a12b:free
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.amazon.nova-micro-v1:0
COPILOT_DEMO_MODE=true
AI_COPILOT_ENABLED=true

# Security
SECRET_KEY=lukla-secret-super-secure-key-for-jwt-signing-hs256
EOF

# 5. Run Database Migrations
echo "--> Running schema migrations on PostgreSQL..."
python3 scripts/init_ec2_db.py

APP_PORT="${APP_PORT:-80}"

# 6. Configure port binding for unprivileged user and enable port 3000 redirection
echo "--> Configuring network ports (Port ${APP_PORT} default, Port 3000 redirect)..."
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80 >/dev/null 2>&1 || true
echo "net.ipv4.ip_unprivileged_port_start=80" | sudo tee /etc/sysctl.d/99-unprivileged-ports.conf >/dev/null 2>&1 || true

# Redirect port 3000 to port 80 so requests to both ports are handled
if [ "$APP_PORT" = "80" ]; then
    sudo iptables -t nat -C PREROUTING -p tcp --dport 3000 -j REDIRECT --to-port 80 2>/dev/null || \
    sudo iptables -t nat -A PREROUTING -p tcp --dport 3000 -j REDIRECT --to-port 80 2>/dev/null || true
fi

# 7. Stop previous instance if running
echo "--> Restarting application process on port ${APP_PORT}..."
if [ -f "$HOME/app.pid" ]; then
    OLD_PID=$(cat "$HOME/app.pid" 2>/dev/null || true)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "    Stopping previous process (PID: $OLD_PID)..."
        kill "$OLD_PID" || true
        sleep 2
    fi
fi
pkill -f "uvicorn main:app" 2>/dev/null || true

# 8. Start unified application on 0.0.0.0:${APP_PORT}
nohup .venv/bin/uvicorn main:app --host 0.0.0.0 --port "$APP_PORT" > "$HOME/app.log" 2>&1 &
APP_PID=$!
echo $APP_PID > "$HOME/app.pid"
echo "    Started main:app with PID $APP_PID on port $APP_PORT (logs in ~/app.log)"

# 9. Verification probe
echo "--> Probing localhost:${APP_PORT}..."
sleep 3
if curl -s -I "http://localhost:${APP_PORT}" | grep -q "200 OK"; then
    echo "=========================================================="
    echo " SUCCESS: Application is running on 0.0.0.0:${APP_PORT}!"
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
echo " Port         : $APP_PORT (and redirected from 3000)"
echo " Portal URL   : http://${PUBLIC_IP}/"
echo " AI Copilot   : http://${PUBLIC_IP}/copilot"
echo " Sampling App : http://${PUBLIC_IP}/sampling/"
echo " ERP UI Mock  : http://${PUBLIC_IP}/ui"
echo " API Docs     : http://${PUBLIC_IP}/docs"
echo "----------------------------------------------------------"
echo "Form Pelaporan: https://forms.gle/v6wZutpAhr8r9v4B7"
echo "=========================================================="
