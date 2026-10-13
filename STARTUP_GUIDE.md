# Sampling & Spec R&D - Startup Guide

Quick-start guide to run the Sampling & Spec R&D module locally.

## ⚡ 5-Minute Quick Start

### Backend (Terminal 1)

```bash
# Navigate to backend
cd "c:\project 1\MAIN-Alkademi-hackathon-project1-amiga-textile\backend\sampling-spec-rnd"

# Create virtual environment (first time only)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart

# Run server
uvicorn src.api.routes:app --reload --port 8000
```

✅ Backend ready: http://localhost:8000

### Frontend (Terminal 2)

```bash
# Navigate to frontend
cd "c:\project 1\MAIN-Alkademi-hackathon-project1-amiga-textile\frontend\sampling-spec-rnd"

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

✅ Frontend ready: http://localhost:3000

---

## 📋 Step-by-Step Setup

### Prerequisites

- **Python** 3.8+ (check: `python --version`)
- **Node.js** 16+ (check: `node --version`)
- **npm** 8+ (check: `npm --version`)
- **Git** (check: `git --version`)

### Backend Installation

1. **Navigate to backend folder:**
   ```bash
   cd "c:\project 1\MAIN-Alkademi-hackathon-project1-amiga-textile\backend\sampling-spec-rnd"
   ```

2. **Create Python virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   
   You should see `(venv)` prefix in terminal.

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   If `requirements.txt` doesn't exist:
   ```bash
   pip install fastapi uvicorn python-multipart
   ```

4. **Run development server:**
   ```bash
   uvicorn src.api.routes:app --reload --port 8000
   ```

5. **Verify it's working:**
   - Open: http://localhost:8000/docs
   - You should see the **OpenAPI documentation**
   - Try the `/health` endpoint

### Frontend Installation

1. **Navigate to frontend folder:**
   ```bash
   cd "c:\project 1\MAIN-Alkademi-hackathon-project1-amiga-textile\frontend\sampling-spec-rnd"
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Verify it's working:**
   - Browser automatically opens: http://localhost:3000
   - You should see the **Time Study Recording** interface
   - Design with rounded corners, glassmorphism effect visible

---

## 🧪 Testing the System

### Test Time Study Flow

1. **Go to frontend:** http://localhost:3000
2. **Enter process name:** "Assembly Line A"
3. **Click "Create Study"**
   - Study card should appear
   - Status: "draft"
4. **Click "Start Study"**
   - Status changes to "in_progress"
   - Input field for cycle time appears
5. **Add samples:**
   - Enter "1200" (milliseconds)
   - Click "Add Sample"
   - Progress bar updates
   - Repeat several times
6. **Complete study:**
   - Click "Complete"
   - Status changes to "completed"

### Test Backend API Directly

Using curl or Postman:

```bash
# 1. Create a study
POST http://localhost:8000/api/sampling-spec-rnd/studies/create
Params:
  tenant_id=default
  process_id=proc_001
  process_name=Assembly A
  operator_id=op_001

# 2. Start study
POST http://localhost:8000/api/sampling-spec-rnd/studies/{study_id}/start

# 3. Add sample
POST http://localhost:8000/api/sampling-spec-rnd/studies/{study_id}/add-sample
Params:
  cycle_time_ms=1200
  element_name=assembly

# 4. Get statistics
GET http://localhost:8000/api/sampling-spec-rnd/studies/{study_id}/stats

# 5. Check health
GET http://localhost:8000/api/sampling-spec-rnd/health
```

---

## 🎨 Design System Verification

### Rounded Corners
✅ Check: Card, Button, Input elements have smooth rounded corners (8-24px)

### Clear Contrast
✅ Check: Text is clearly readable (dark text on light background)

### Glassmorphism Effect
✅ Check: Cards have blur effect and semi-transparent appearance
- Inspect element → Look for `backdrop-filter: blur()`

### Tablet Performance
✅ Check: No lag when:
- Typing in inputs
- Clicking buttons
- Adding samples rapidly
- Dev Tools shows 60 FPS

---

## 🔧 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Make sure virtual environment is activated
venv\Scripts\activate

# Then install dependencies
pip install fastapi uvicorn python-multipart
```

### Issue: "Cannot find module '@components'"

**Solution:**
```bash
# Clear node_modules and reinstall
rm -r node_modules
npm install

# Rebuild
npm run dev
```

### Issue: "Port 8000/3000 already in use"

**Solution:**
```bash
# Change port in vite.config.ts (frontend)
# Or in uvicorn command (backend)
uvicorn src.api.routes:app --port 8001
```

### Issue: "Backend returns 404 for API calls"

**Solution:**
1. Check backend is running: http://localhost:8000/health
2. Check frontend proxy in `vite.config.ts`:
   ```tsx
   proxy: {
     '/api': {
       target: 'http://localhost:8000',
       changeOrigin: true,
     }
   }
   ```

### Issue: "Glassmorphism not visible on mobile"

**Solution:**
- Glassmorphism requires backdrop-filter support
- Check browser compatibility:
  - Chrome 76+
  - Safari 9+
  - Firefox 103+
- Fallback to solid colors for older browsers

---

## 📁 Project Files Reference

### Backend Key Files
```
backend/sampling-spec-rnd/
├── src/models/
│   ├── time_study_recorder.py      (Time study data model)
│   └── spec_version_tracker.py     (Spec version model)
├── src/services/
│   └── sampling_rnd_workflow.py    (Business logic)
├── src/utils/
│   ├── time_study_patterns.py      (Analysis utilities)
│   └── spec_version_patterns.py    (Drift analysis)
└── src/api/
    └── routes.py                    (REST endpoints)
```

### Frontend Key Files
```
frontend/sampling-spec-rnd/
├── src/components/
│   ├── Button.tsx                  (Touch-friendly button)
│   ├── Card.tsx                    (Glassmorphic card)
│   ├── Input.tsx                   (Form input)
│   └── SamplingCard.tsx            (Study display)
├── src/hooks/
│   ├── usePerformance.ts           (FPS/lag monitoring)
│   └── useLocalStorage.ts          (Offline caching)
├── src/pages/
│   └── TimeStudyPage.tsx           (Main page)
└── src/styles/
    ├── globals.css                 (Apple Design)
    └── design-system.ts            (Design tokens)
```

---

## 🚀 Next Steps

### After Startup

1. **Backend Integration:**
   - Connect to real database (PostgreSQL/MongoDB)
   - Add authentication
   - Set up logging

2. **Frontend Enhancements:**
   - Add Spec Version page
   - Add drift tracking UI
   - Add analytics dashboard

3. **Testing:**
   - Add unit tests
   - Add integration tests
   - Load testing

4. **Deployment:**
   - Docker containerization
   - CI/CD pipeline setup
   - Production deployment

---

## 📚 Documentation

- `backend/README.md` - Backend API reference
- `backend/MODULES_REFERENCE.md` - Module specifications
- `frontend/README.md` - Frontend component guide
- `PROJECT_STRUCTURE.md` - Complete project overview
- `INTEGRATION_ANALYSIS.md` - System integration patterns

---

## 📞 Troubleshooting

### Check System Status

```bash
# Backend health
curl http://localhost:8000/api/sampling-spec-rnd/health

# Frontend is running
# Open http://localhost:3000 in browser
```

### View Logs

**Backend (in terminal):**
- Watch output from `uvicorn src.api.routes:app`
- Look for errors, warnings

**Frontend (in terminal):**
- Watch output from `npm run dev`
- Check browser console (F12 → Console tab)

### Debug Mode

**Backend:**
```bash
# Enable more verbose logging
uvicorn src.api.routes:app --reload --log-level debug
```

**Frontend:**
```bash
# Dev tools already open (F12)
# Performance tab shows FPS
```

---

## ✅ Startup Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] Virtual environment created and activated
- [ ] Backend dependencies installed
- [ ] Backend server running on :8000
- [ ] Frontend dependencies installed
- [ ] Frontend server running on :3000
- [ ] Can access http://localhost:3000
- [ ] Can create time study
- [ ] Can add samples
- [ ] Backend API responds to health check
- [ ] Design elements visible (rounded, glassmorphism)
- [ ] No console errors

---

**Status**: 🟢 Ready to develop!

For production deployment, see `PROJECT_STRUCTURE.md`.
