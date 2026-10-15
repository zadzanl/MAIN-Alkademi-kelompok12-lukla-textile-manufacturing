# Backend Status - Sampling & Spec R&D Module

## ✅ Status: RUNNING

### Startup Error Fixed
- **Error**: `Attribute "app" not found in module "src.api.routes"`
- **Root Cause**: `routes.py` only had `create_api_router()` function, no FastAPI instance
- **Solution**: Created `src/main.py` with FastAPI app and CORS middleware

### Current Setup

**Backend Server**
- Running: ✅ YES
- Address: `http://127.0.0.1:8009`
- Port: `8009`
- Status: Uvicorn running with auto-reload

**Frontend Integration**
- Frontend Address: `http://localhost:3009`
- API Proxy: Vite configured to proxy to `http://localhost:8009/api`
- Status: ✅ Connected

### Files Modified
1. **Created**: `src/main.py`
   - FastAPI app instance
   - CORS middleware (allows localhost:3009)
   - Health check endpoint
   - Router inclusion

2. **Updated**: `run_backend.bat`
   - Changed from `uvicorn src.api.routes:app`
   - To: `uvicorn src.main:app --reload --port 8009`

### API Endpoints Available
```
GET  /health                              → Health check
POST /api/sampling-spec-rnd/studies/create  → Create study
POST /api/sampling-spec-rnd/studies/{id}/start → Start study
...
```

### Portal Auth Endpoints (added)
```
GET  /api/auth/health                     → auth module + email mode
POST /api/auth/register                   → ajukan akun (pending)
POST /api/auth/login                      → identifier + password
POST /api/auth/logout | GET /api/auth/me  → sesi (Bearer)
POST /api/auth/change-password            → ganti password (Bearer)
POST /api/auth/forgot-password            → kirim OTP
POST /api/auth/reset-password             → setel ulang dengan OTP
GET  /api/auth/admin/registrations        → antrean verifikasi (admin)
POST /api/auth/admin/registrations/{id}/approve|reject (admin)
```
In-memory store (`src/services/auth_store.py`), stdlib scrypt + SMTP, no new deps.
Seed admin default: `admin@luka.local` / `Admin#12345`. Tests: `pytest tests/test_auth.py -q`.

### Frontend Integration
- **API Service**: `src/services/api.ts`
- **Component**: `TimeStudyPage.tsx` (integrated with backend)
- **Fallback**: Local storage if backend not available
- **Connection Check**: Automatic health check on page load

### How to Run

**Terminal 1 - Backend:**
```powershell
cd backend\sampling-spec-rnd
.\venv\Scripts\activate
uvicorn src.main:app --reload --port 8009
```

**Terminal 2 - Frontend:**
```powershell
cd frontend\sampling-spec-rnd
npm run dev
# Opens http://localhost:3009
```

### Next Steps
1. ✅ Backend startup fixed
2. ✅ Frontend running on port 3009
3. ✅ Integration verified
4. Test API flow: Create study → Add sample → Verify backend receives data
5. Check if any TypeScript errors remain (was 60 errors reported earlier)
6. Deploy to production

### Verification
- Backend import test: ✅ PASS
- Backend server start: ✅ PASS (Uvicorn running)
- Frontend dev server: ✅ PASS (Vite running on 3009)
- CORS configured: ✅ YES (localhost:3009 allowed)
