#!/usr/bin/env python3
"""
Telegram Webhook Registration and Health Verification Tool.

Usage:
  # Check current webhook info and bot identity:
  python scripts/register_telegram_webhook.py --check

  # Register public HTTPS webhook URL with secret token:
  python scripts/register_telegram_webhook.py --url https://your-domain.com/api/v1/telegram/webhook

  # Delete current webhook (e.g. for teardown or local polling):
  python scripts/register_telegram_webhook.py --delete

Reads credentials from command-line arguments, environment variables, or local .env file:
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_WEBHOOK_SECRET
  - TELEGRAM_PUBLIC_WEBHOOK_URL
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional


def load_env_file() -> None:
    """Best-effort loader for .env file without external dependencies."""
    search_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for p in search_paths:
        if p.exists() and p.is_file():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
            except Exception:
                pass
            break


def redact_token(token: str) -> str:
    """Redact bot token for safe terminal output."""
    if not token:
        return "<EMPTY>"
    if ":" in token:
        bot_id, secret = token.split(":", 1)
        return f"{bot_id}:***{secret[-4:] if len(secret) >= 4 else ''}"
    return f"***{token[-4:] if len(token) >= 4 else ''}"


def call_telegram_api(
    method: str,
    bot_token: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Execute an HTTP POST or GET request to Telegram Bot API using stdlib urllib."""
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    headers = {"User-Agent": "LuklaOperationsEngine/1.0"}
    data_bytes = None

    if payload is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"
        data_bytes = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST" if payload is not None else "GET")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw_body)
        except Exception:
            return {"ok": False, "error_code": exc.code, "description": raw_body}
    except urllib.error.URLError as exc:
        return {"ok": False, "error_code": -1, "description": f"Network connection failed: {exc.reason}"}


def check_webhook_status(token: str) -> int:
    """Query getMe and getWebhookInfo to report bot identity and webhook configuration."""
    print("=" * 65)
    print(" TELEGRAM BOT & WEBHOOK HEALTH CHECK")
    print("=" * 65)

    # 1. Verify Bot Identity
    me_resp = call_telegram_api("getMe", token)
    if not me_resp.get("ok"):
        print(f"[FAIL] Bot token verification failed: {me_resp.get('description', 'Unknown error')}")
        print(f"       Token: {redact_token(token)}")
        return 1

    bot_user = me_resp.get("result", {})
    print(f"[PASS] Bot Identity Confirmed:")
    print(f"       ID       : {bot_user.get('id')}")
    print(f"       Name     : {bot_user.get('first_name')}")
    print(f"       Username : @{bot_user.get('username')}")
    print(f"       Token    : {redact_token(token)}")
    print("-" * 65)

    # 2. Inspect Webhook Status
    info_resp = call_telegram_api("getWebhookInfo", token)
    if not info_resp.get("ok"):
        print(f"[FAIL] getWebhookInfo failed: {info_resp.get('description', 'Unknown error')}")
        return 1

    info = info_resp.get("result", {})
    current_url = info.get("url") or "(None - Webhook is not registered)"
    pending_updates = info.get("pending_update_count", 0)
    last_error_date = info.get("last_error_date")
    last_error_msg = info.get("last_error_message")

    print(f"[INFO] Webhook Configuration:")
    print(f"       URL             : {current_url}")
    print(f"       Has Custom Cert : {info.get('has_custom_certificate', False)}")
    print(f"       Pending Updates : {pending_updates}")
    print(f"       Max Connections : {info.get('max_connections', 40)}")
    print(f"       Allowed Updates : {info.get('allowed_updates', ['message'])}")

    if last_error_msg:
        print(f"       [!] Last Error   : {last_error_msg} (timestamp: {last_error_date})")
    else:
        print(f"       Last Error      : None (Webhook delivery is clean)")

    print("=" * 65)
    return 0


def delete_webhook(token: str, drop_pending: bool = False) -> int:
    """Delete current webhook from Telegram Bot API."""
    print("--> Deleting Telegram webhook...")
    payload = {"drop_pending_updates": drop_pending}
    resp = call_telegram_api("deleteWebhook", token, payload=payload)
    if resp.get("ok"):
        print("[PASS] Webhook successfully deleted.")
        if drop_pending:
            print("       Dropped all pending updates.")
        return 0
    else:
        print(f"[FAIL] deleteWebhook failed: {resp.get('description')}")
        return 1


def register_webhook(
    token: str,
    url: str,
    secret: Optional[str] = None,
    drop_pending: bool = False,
    max_connections: int = 40,
) -> int:
    """Register HTTPS webhook with Telegram Bot API."""
    print("=" * 65)
    print(" REGISTERING TELEGRAM WEBHOOK")
    print("=" * 65)
    print(f" Target URL : {url}")
    print(f" Bot Token  : {redact_token(token)}")
    print(f" Secret Set : {'Yes (Protected)' if secret else 'No (Warning: unverified)'}")

    # Enforce Telegram Bot API HTTPS requirement
    if not url.startswith("https://"):
        print("-" * 65)
        print("[ERROR] Telegram Bot API strictly requires an HTTPS webhook URL.")
        print(f"        Supplied URL starts with: '{url[:7]}'")
        print("        Telegram will reject plain HTTP requests.")
        print("        To fix this, supply an HTTPS endpoint via:")
        print("          1. Domain with SSL reverse proxy (e.g. Caddy, Nginx + Let's Encrypt)")
        print("          2. Cloudflare Tunnel: cloudflared tunnel --url http://localhost:80")
        print("          3. Ngrok tunnel: ngrok http 80")
        print("=" * 65)
        return 1

    payload: Dict[str, Any] = {
        "url": url,
        "allowed_updates": ["message"],
        "max_connections": max_connections,
        "drop_pending_updates": drop_pending,
    }
    if secret:
        payload["secret_token"] = secret

    resp = call_telegram_api("setWebhook", token, payload=payload)

    print("-" * 65)
    if resp.get("ok"):
        print(f"[PASS] setWebhook Success: {resp.get('description', 'Webhook was set')}")
        print("=" * 65)
        # Verify immediately
        check_webhook_status(token)
        return 0
    else:
        print(f"[FAIL] setWebhook Failed: {resp.get('description')}")
        print(f"       Error Code: {resp.get('error_code')}")
        print("=" * 65)
        return 1


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Telegram Webhook Registration and Health Check Tool for Lukla Operations Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default=os.getenv("TELEGRAM_PUBLIC_WEBHOOK_URL"),
        help="Public HTTPS URL for the webhook (e.g. https://domain.com/api/v1/telegram/webhook)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("TELEGRAM_BOT_TOKEN"),
        help="Telegram Bot Token from @BotFather (or env TELEGRAM_BOT_TOKEN)",
    )
    parser.add_argument(
        "--secret",
        default=os.getenv("TELEGRAM_WEBHOOK_SECRET"),
        help="Secret token sent in X-Telegram-Bot-Api-Secret-Token header (or env TELEGRAM_WEBHOOK_SECRET)",
    )
    parser.add_argument(
        "--check",
        "--info",
        action="store_true",
        help="Inspect current bot identity and webhook status without modifying it",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete the currently registered webhook",
    )
    parser.add_argument(
        "--drop-pending-updates",
        action="store_true",
        help="Drop all pending updates currently queued by Telegram",
    )

    args = parser.parse_args()

    token = (args.token or "").strip()
    if not token:
        print("[ERROR] Missing Telegram Bot Token.")
        print("        Provide via --token, TELEGRAM_BOT_TOKEN environment variable, or .env file.")
        sys.exit(1)

    if args.delete:
        sys.exit(delete_webhook(token, drop_pending=args.drop_pending_updates))

    if args.check or not args.url:
        if not args.url and not args.check:
            print("[INFO] No --url provided. Defaulting to webhook status check...")
        sys.exit(check_webhook_status(token))

    url = args.url.strip()
    secret = (args.secret or "").strip() or None
    sys.exit(register_webhook(token, url, secret=secret, drop_pending=args.drop_pending_updates))


if __name__ == "__main__":
    main()
