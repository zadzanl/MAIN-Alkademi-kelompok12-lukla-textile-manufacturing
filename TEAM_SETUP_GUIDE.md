# 🎯 Team Setup Guide - Sampling & Spec R&D Module

## ⚠️ Important - Repository Information

**MAIN Repository (Use This):**
```
https://github.com/zadzanl/MAIN-Alkademi-hackathon-project1-amiga-textile.git
Branch: master
```

**Old Repository (Archived - DO NOT USE):**
```
c:\project 1  (locally archived)
```

All active development happens in the MAIN repository only.

---

## 🚀 Quick Start for Team

### 1. Clone Repository

```bash
git clone https://github.com/zadzanl/MAIN-Alkademi-hackathon-project1-amiga-textile.git
cd MAIN-Alkademi-hackathon-project1-amiga-textile
```

### 2. Backend Setup (Python FastAPI)

```bash
cd backend/sampling-spec-rnd

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn src.main:app --reload --port 8007
```

**Backend will be available at:**
- API: http://127.0.0.1:8007/api/sampling-spec-rnd
- Swagger Docs: http://127.0.0.1:8007/docs
- Health: http://127.0.0.1:8007/api/sampling-spec-rnd/health

### 3. Frontend Setup (React + TypeScript)

**Terminal 2:**
```bash
cd frontend/sampling-spec-rnd

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Frontend will be available at:**
- URL: http://localhost:3007
- Design: Apple Design System
- Optimization: Tablet optimized (60 FPS)

---

## 📁 Project Structure

```
MAIN-Alkademi-hackathon-project1-amiga-textile/
├── backend/sampling-spec-rnd/          # FastAPI backend
│   ├── src/
│   │   ├── main.py                     # FastAPI app entry point
│   │   ├── api/routes.py               # API endpoints
│   │   ├── models/                     # Data models
│   │   ├── services/                   # Business logic
│   │   └── utils/                      # Utilities
│   ├── requirements.txt                # Python dependencies
│   └── run_backend.bat                 # Windows startup script
│
├── frontend/sampling-spec-rnd/         # React frontend
│   ├── src/
│   │   ├── pages/TimeStudyPage.tsx    # Main page (integrated)
│   │   ├── components/                # Apple Design components
│   │   ├── services/api.ts            # API client
│   │   ├── styles/                    # Design system & globals
│   │   └── types/                     # TypeScript types
│   ├── package.json                    # NPM dependencies
│   ├── tsconfig.json                   # TypeScript config
│   ├── vite.config.ts                  # Vite config with API proxy
│   └── run_frontend.bat                # Windows startup script
│
├── DEPLOYMENT_READY.md                 # Deployment checklist
├── INTEGRATION_STATUS.md               # Integration details
├── TEAM_SETUP_GUIDE.md                 # This file
└── [Other documentation]
```

---

## 🔧 Configuration

### Backend Configuration

**File**: `backend/sampling-spec-rnd/.env.example`

```
DATABASE_URL=sqlite:///sampling_spec_rnd.db
API_PORT=8007
DEBUG=true
```

Copy to `.env` and update as needed.

### Frontend Configuration

**File**: `frontend/sampling-spec-rnd/.env.example`

```
VITE_API_URL=/api/sampling-spec-rnd
```

Copy to `.env` and update as needed.

**Vite Proxy** (automatic via `vite.config.ts`):
- Requests to `/api/*` are proxied to `http://127.0.0.1:8007`
- No CORS issues in development

---

## 🧪 Testing

### Backend Health Check

```bash
curl http://127.0.0.1:8007/api/sampling-spec-rnd/health

# Response:
# {"status":"healthy","module":"sampling-spec-rnd"}
```

### Frontend Connection

1. Open http://localhost:3007
2. Look for green checkmark 🟢 "Backend Connected"
3. Try creating a time study
4. Check backend logs for API calls

---

## 📊 API Documentation

Full API documentation available at:
```
http://127.0.0.1:8007/docs
```

### Key Endpoints

**Time Study:**
- `POST /api/sampling-spec-rnd/studies/create` - Create study
- `POST /api/sampling-spec-rnd/studies/{id}/start` - Start study
- `POST /api/sampling-spec-rnd/studies/{id}/add-sample` - Add sample
- `POST /api/sampling-spec-rnd/studies/{id}/complete` - Complete study

**Specification:**
- `POST /api/sampling-spec-rnd/specs/create` - Create spec
- `POST /api/sampling-spec-rnd/specs/{id}/record-change` - Record change
- `POST /api/sampling-spec-rnd/specs/{id}/record-drift` - Record drift

---

## 🎨 Design System

### Apple Design Tokens Implemented

- **Rounded Corners**: 8px, 12px, 16px, 20px, 24px
- **Glasmorphism**: Backdrop blur, semi-transparent backgrounds
- **Colors**: Apple color palette (primary, secondary, error, success)
- **Typography**: SF Pro Display (Apple font stack fallback)
- **Spacing**: 4px, 8px, 12px, 16px, 24px, 32px
- **Shadows**: Subtle elevation effects

### WCAG AA+ Compliance

- ✅ Contrast ratios checked
- ✅ Touch targets 48px minimum
- ✅ Keyboard navigation support
- ✅ Screen reader friendly

### Tablet Optimization

- ✅ 60 FPS target
- ✅ No lag on factory tablets
- ✅ Responsive layout
- ✅ Touch-friendly UI

---

## 🐛 Troubleshooting

### Backend won't start

```
Error: "Address already in use"
Solution: Change port in command or kill process on port 8007
```

```bash
# Find process on port 8007
netstat -ano | findstr :8007

# Kill process
taskkill /PID <PID> /F
```

### Frontend can't connect to backend

1. Check backend is running on http://127.0.0.1:8007
2. Check Vite proxy in `vite.config.ts`
3. Check CORS allowed origins in `src/main.py`
4. Check browser console for errors

### TypeScript errors

If seeing TypeScript errors:

```bash
cd frontend/sampling-spec-rnd

# Clear cache and reinstall
rm -r node_modules
npm install

# Check types
npx tsc --noEmit
```

---

## 📝 Git Workflow

### For team members:

```bash
# Get latest code
git pull origin master

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ...

# Commit changes
git add .
git commit -m "feat: describe your changes"

# Push to remote
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### Keep code clean

```bash
# Before committing
npx tsc --noEmit              # Check TypeScript
npm run lint                  # Lint code (if configured)

# Backend
cd backend/sampling-spec-rnd
python -m pytest              # Run tests (if available)
```

---

## 📞 Support

If team members have issues:

1. Check `INTEGRATION_STATUS.md` - Integration details
2. Check `DEPLOYMENT_READY.md` - Deployment status
3. Check backend logs - `http://127.0.0.1:8007/docs`
4. Check frontend console - Browser DevTools

---

## ✅ Checklist for Team

- [ ] Clone repository
- [ ] Create virtual environment (backend)
- [ ] Install dependencies (both)
- [ ] Start backend on port 8007
- [ ] Start frontend on port 3007
- [ ] Visit http://localhost:3007
- [ ] See green checkmark "Backend Connected"
- [ ] Create a time study
- [ ] Verify backend receives request
- [ ] Read DEPLOYMENT_READY.md for more info

---

**Repository**: https://github.com/zadzanl/MAIN-Alkademi-hackathon-project1-amiga-textile.git  
**Main Branch**: `master`  
**Status**: ✅ Ready for development  
**Last Updated**: October 13, 2026
