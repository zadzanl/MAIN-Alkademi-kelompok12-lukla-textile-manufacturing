# Telegram Copilot Bot — Live Deployment & Setup Guide

Lukla Operations Engine integrates a mobile read-only Telegram Bot ("Lukla Assistant") connected directly to the in-process Copilot inference and role-filtered tool catalog.

---

## Architecture & Security Model

```
+-------------------+           HTTPS Webhook             +--------------------------------------+
|  Telegram Client  |  ================================>  | FastAPI (/api/v1/telegram/webhook)   |
|   (Mobile App)    |                                     | - Validates secret header token      |
+-------------------+                                     | - Enforces idempotency (update_id)   |
        ^                                                 | - Resolves server-side binding       |
        |                                                 | - Injects verified actor/tenant JWT  |
        | Telegram sendMessage (HTTP 200)                 +--------------------------------------+
        +-------------------------------------------------------- |
                                                                  v
                                                  +--------------------------------+
                                                  | Copilot Engine & Read Tools    |
                                                  | - Filtered by role (Owner, QC) |
                                                  | - Tenant data isolated via RLS |
                                                  +--------------------------------+
```

1. **Inbound Webhook (`POST /api/v1/telegram/webhook`):** Validates the `X-Telegram-Bot-Api-Secret-Token` header on every request before parsing payloads.
2. **Deterministic Role Granting:** Telegram usernames or caller headers are never trusted. Roles are bound server-side via single-use, admin-issued enrollment codes.
3. **Idempotency:** Retried Telegram webhook deliveries with identical `update_id` are recorded in `telegram_processed_updates` to prevent duplicate inference.
4. **Read-Only Invariant:** Any mutation requests generated in chat are rendered as non-executable text links / action shortcuts. State cannot be modified over Telegram.

---

## Prerequisites

Before enabling the bot in production or staging:
1. **Telegram Bot Token:** Obtained by messaging [@BotFather](https://t.me/BotFather) on Telegram (`/newbot`).
2. **Webhook Secret Token:** A high-entropy random string (1-256 characters) used to verify Telegram as the true caller.
   Generate one via:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Public HTTPS Webhook URL:** Telegram's Bot API **strictly requires HTTPS** with a valid SSL/TLS certificate. Plain HTTP (`http://...`) is rejected by Telegram servers.

---

## Providing HTTPS for EC2 / Local Deployments

Because `deploy_ec2.sh` runs Uvicorn on port 80/3000 directly, you must terminate TLS in front of the application:

### Option 1: Cloudflare Tunnel (Recommended for Hackathons & Quick Staging)
Zero open ports required, automatic free HTTPS certificate:
```bash
# On the EC2 host or staging server:
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' | sudo tee /etc/apt/sources.list.d/cloudflared.list
# Or download binary directly:
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
chmod +x cloudflared

# Launch tunnel to local application port:
./cloudflared tunnel --url http://127.0.0.1:80
```
This generates a public URL like `https://random-subdomain.trycloudflare.com`.
Your webhook URL is: `https://random-subdomain.trycloudflare.com/api/v1/telegram/webhook`.

### Option 2: Caddy Reverse Proxy (Production Domain)
Install Caddy for automatic Let's Encrypt SSL:
```bash
sudo dnf install -y 'dnf-command(copr)'
sudo dnf copr enable -y @caddy/caddy
sudo dnf install -y caddy

# Edit /etc/caddy/Caddyfile:
# your-domain.com {
#     reverse_proxy 127.0.0.1:80
# }

sudo systemctl restart caddy
```

---

## Configuring the Deployment

### Method A: Automated EC2 Deployment
Export the credentials in your deployment shell prior to running `scripts/deploy_ec2.sh`:

```bash
export TELEGRAM_BOT_ENABLED=true
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"
export TELEGRAM_WEBHOOK_SECRET="your-generated-random-secret"
export TELEGRAM_PUBLIC_WEBHOOK_URL="https://your-domain.com/api/v1/telegram/webhook"

./scripts/deploy_ec2.sh
```
`scripts/deploy_ec2.sh` automatically injects these into `.env` and reports their status in the final deployment summary.

### Method B: Manual `.env` Configuration
Add the following keys to your root `.env`:
```env
TELEGRAM_BOT_ENABLED=true
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_WEBHOOK_SECRET=your-generated-random-secret
TELEGRAM_PUBLIC_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook
TELEGRAM_MAX_MESSAGE_LENGTH=2000
TELEGRAM_ENROLLMENT_DEFAULT_TTL_SECONDS=900
```

---

## Registering and Verifying the Webhook

Use the built-in management script [`scripts/register_telegram_webhook.py`](file:///c:/Projects/hackathon-telegram-live-deployment/scripts/register_telegram_webhook.py):

### 1. Register Webhook
```bash
python scripts/register_telegram_webhook.py --url https://your-domain.com/api/v1/telegram/webhook
```
This sends `setWebhook` to Telegram's API with the secret token and allowed updates (`["message"]`).

### 2. Inspect Webhook Status & Bot Identity
```bash
python scripts/register_telegram_webhook.py --check
```
Output:
```
=================================================================
 TELEGRAM BOT & WEBHOOK HEALTH CHECK
=================================================================
[PASS] Bot Identity Confirmed:
       ID       : 123456789
       Name     : Lukla Assistant
       Username : @LuklaAssistantBot
       Token    : 123456789:***YZ
-----------------------------------------------------------------
[INFO] Webhook Configuration:
       URL             : https://your-domain.com/api/v1/telegram/webhook
       Has Custom Cert : False
       Pending Updates : 0
       Max Connections : 40
       Allowed Updates : ['message']
       Last Error      : None (Webhook delivery is clean)
=================================================================
```

### 3. Teardown / Unregister Webhook
If you ever need to remove the webhook or switch to local polling:
```bash
python scripts/register_telegram_webhook.py --delete --drop-pending-updates
```

---

## Admin Enrollment Flow

Users cannot talk to the bot until bound to a verified tenant actor:

1. **Admin Issues Code:**
   POST to `/api/v1/telegram/admin/enrollment-codes` with an admin Bearer token:
   ```json
   {
     "role": "QCInspector",
     "ttl_seconds": 900
   }
   ```
   Response returns a single-use code:
   ```json
   {
     "code": "7A8B9C2D1E4F",
     "expires_at": "2026-10-16T12:00:00Z",
     "role": "QCInspector"
   }
   ```

2. **User Claims Account:**
   The user opens Telegram, starts a chat with `@LuklaAssistantBot`, and sends:
   ```
   /start 7A8B9C2D1E4F
   ```
   The bot responds:
   ```
   Akun Telegram Anda berhasil didaftarkan ke Lukla Intelligence dengan peran: QCInspector.
   Anda sekarang dapat mengirimkan pertanyaan operasional (read-only).
   ```

3. **Revocation:**
   Admins can revoke access at any time via:
   `POST /api/v1/telegram/admin/bindings/{telegram_chat_id}/revoke`.
   Subsequent questions from that Telegram user receive access denied responses.

---

## Automated Verification

Verify that all security and functional gates pass:
```bash
python scripts/verify_telegram_copilot_gate.py
```
This tests:
- AC-1: Webhook integration path matches `/api/v1/copilot/chat`
- AC-2: Server-derived role isolation (cannot self-elevate)
- AC-3: Single-use enrollment code lifecycle
- AC-4: Revocation handling
- AC-5: Invalid secret & malformed payload rejection
- AC-6: Read-only enforcement (mutations blocked)
- AC-7: Resilience against Telegram API timeouts and outages
- AC-8: Multi-role catalog validation
