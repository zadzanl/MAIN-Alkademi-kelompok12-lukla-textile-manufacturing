# BACKEND STATUS — UHUY B2B External Portal API

**Module:** `uhuy-b2b-portal` (external client portal, port 8010)
**Stack:** FastAPI 0.104.1, Pydantic, stdlib only (no new dependencies)
**Storage:** in-memory, client-scoped, resets on restart

## What exists

| Area | Endpoint | Notes |
|---|---|---|
| Health | `GET /health`, `GET /api/portal/health`, `GET /api/portal/auth/health` | module + scope + email mode |
| Client auth | `POST /api/portal/auth/register` | creates `pending` client |
| | `POST /api/portal/auth/login` | email/phone + password → opaque token |
| | `POST /api/portal/auth/logout`, `GET /api/portal/auth/me` | |
| | `POST /api/portal/auth/change-password` | revokes sessions |
| | `POST /api/portal/auth/forgot-password`, `/reset-password` | OTP to email (dev-log fallback) |
| Internal approval | `GET /api/portal/auth/admin/clients` | admin only |
| | `POST /api/portal/auth/admin/clients/{id}/approve\|reject` | admin only |
| Client data | `GET /api/portal/summary` | client-scoped KPI |
| | `GET /api/portal/orders`, `GET /api/portal/orders/{id}` | own orders only |
| | `GET /api/portal/stock` | own consigned material only |
| | `GET /api/portal/requests`, `GET /api/portal/requests/{id}` | own requests only |
| Request submit | `POST /api/portal/requests/order`, `POST /api/portal/requests/sample` | status `submitted` |

## Isolation boundary

Every client-data method takes `client_id` and filters on it. The route layer resolves
`client_id` **only** from the authenticated session (never from body/query). Reading another
client's id returns `404`. This is covered by `tests/test_portal_scope.py` (RBAC role #8 / AT-R08).

## Security

- Passwords: salted `hashlib.scrypt` (`scrypt$n$r$p$salt$hash`).
- Sessions: opaque `secrets.token_urlsafe` tokens, stored hashed, expiring; revoked on password change.
- OTPs: hashed, single-use, attempt-capped, cooldown; `forgot-password` always answers generically.
- Admin endpoints reject non-admin actors with `403`.

## Config (`.env`)

See `.env.example`. Key vars: `SEED_ADMIN_EMAIL/PASSWORD`, `PORTAL_TOKEN_TTL_MINUTES`,
`PORTAL_OTP_*`, `SMTP_*` (empty `SMTP_HOST` = dev-log OTP).

## Verification (all green)

```text
pytest -q     -> 23 passed
ruff check .  -> All checks passed!
mypy src      -> Success: no issues found in 9 source files
```

Live smoke: boot + `/health` + login (client A) + scoped summary/orders/stock + cross-client
`404` + order-request creation.

## Known ceiling

Single-process, in-memory only; requests are not persisted; no rate limiting. Upgrade by
swapping `portal_store` for production PostgreSQL tables with RLS (same method API).
