# Lukla - Textile Manufacturing Operations Platform

Lukla is a textile manufacturing operations platform that brings production, warehouse, quality control, sampling, and payroll together in a single application. Teams no longer need to switch between tools.

**Language:** [Bahasa Indonesia](./README.md) · English

## Key Features

- Operational dashboard and factory activity summary.
- AI Copilot that answers operational questions in everyday language.
- Warehouse, stock, and inventory transaction management.
- Production monitoring and line sewing work logging.
- Sampling, time study, specification, and quality control analysis.
- Piece-rate payroll and its related financial controls.
- Login portal for internal users.

## Repository Structure

| Folder/File | Description |
| --- | --- |
| `backend/` | Main Lukla Operations Engine API (port 8000) |
| `prototypes/sampling-spec-rnd/backend/` | Sampling and operations prototype API (port 8009) |
| `prototypes/sampling-spec-rnd/frontend/` | React + Vite web application (port 3009) |
| `prototypes/uhuy-b2b-portal/` | Companion B2B portal prototype |
| `USER_GUIDE.md` | Application usage guide |

## Running the Application

### Prerequisites

- Python 3.11 or a Python version compatible with `requirements.txt`.
- Node.js 20 or newer, plus npm.
- Git.

Run each service in a separate terminal. All commands below are run from the repository root, unless a working directory is stated otherwise.

### 1. Main backend - port 8000

Install the backend dependencies once:

```powershell
python -m pip install -r prototypes/sampling-spec-rnd/backend/requirements.txt
```

Start the main API:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

If it works, the API docs open at `http://localhost:8000/docs`.

### 2. Prototype backend - port 8009

```powershell
Set-Location prototypes/sampling-spec-rnd/backend
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8009
```

If it works, the health check returns a healthy status:

```powershell
Invoke-RestMethod http://localhost:8009/health
```

### 3. Frontend - port 3009

Open a new terminal, then run:

```powershell
Set-Location prototypes/sampling-spec-rnd/frontend
npm install
npm run dev
```

If it works, the login page opens at `http://localhost:3009`.

The frontend uses a Vite proxy. Requests to `/api/v1` are forwarded to the backend on port 8000, while `/api` and the AI Copilot are forwarded to the backend on port 8009. That is why all three services must run for the application to work fully.

## Demo Credentials

- **Identifier:** `ADMIN-IT`
- **Password:** `Admin#12345`

Enter `ADMIN-IT` in the **identifier** login field at `http://localhost:3009`.

## User Guide

See [USER_GUIDE.md](./USER_GUIDE.md) for the full guide to every application feature.

## Project Notes

The `frontend/` folder at the root is not the main frontend application; it is a Playwright test harness for the design mock. The demo application runs from `prototypes/sampling-spec-rnd/`.
