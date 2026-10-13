# SAMPLING & SPEC R&D - Project Structure

Struktur folder yang jelas dan terorganisir untuk Backend & Frontend development.

## 📂 Folder Structure

```
sampling-spec-rnd/
│
├── backend/                          ← Backend Services & Business Logic
│   ├── models/                       ← Data Models & Classes
│   │   ├── time_study_recorder.py   ← TimeStudyRecorder class
│   │   └── spec_version_tracker.py  ← SpecVersionTracker class
│   │
│   ├── services/                     ← Business Logic & Workflows
│   │   └── sampling_rd_workflow.py  ← Complete workflow example
│   │
│   ├── utils/                        ← Utility Functions & Patterns
│   │   ├── time_study_patterns.py   ← Time study functions (8 patterns)
│   │   └── spec_version_patterns.py ← Spec version functions (9 patterns)
│   │
│   └── api/                          ← API Endpoints (Flask/FastAPI/Django)
│       ├── time_study_routes.py     ← Time study API endpoints
│       ├── spec_version_routes.py   ← Spec version API endpoints
│       └── __init__.py
│
├── frontend/                         ← Frontend UI & Client Logic
│   ├── components/                   ← React Components
│   │   ├── TimeStudyRecorder.jsx    ← Time study recording component
│   │   └── SpecVersionTracker.jsx   ← Spec version tracking component
│   │
│   ├── pages/                        ← Page Components
│   │   ├── SamplingPage.jsx         ← Main sampling dashboard
│   │   └── SpecRnDPage.jsx          ← Spec R&D management page
│   │
│   ├── hooks/                        ← Custom React Hooks
│   │   ├── useTimeStudy.js          ← Time study data management
│   │   └── useSpecVersion.js        ← Spec version data management
│   │
│   ├── utils/                        ← Frontend Utilities
│   │   ├── time-study-patterns.js   ← Time study helper functions
│   │   └── api-client.js            ← API communication
│   │
│   └── styles/                       ← CSS/Styling
│       ├── TimeStudy.module.css
│       └── SpecVersion.module.css
│
├── conventions/                      ← Coding Standards
│   └── NAMING_CONVENTIONS.md
│
├── INVENTORY.md                      ← Items Index
├── STRUCTURE.md                      ← This file
├── SAMPLING_SPEC_RND_GUIDE.md       ← Quick start guide
├── README.md                         ← Module documentation
└── opencode.config.json             ← Configuration
```

## 🎯 Ownership Guide

### Backend Team

**Buat/Develop:**
- `backend/models/` - Python data models
- `backend/services/` - Business logic & workflows
- `backend/utils/` - Helper functions & patterns
- `backend/api/` - REST API endpoints

**Focus:**
- Time study recording logic
- Spec version management
- R&D drift detection
- Data validation & persistence
- Database operations

### Frontend Team

**Buat/Develop:**
- `frontend/components/` - React UI components
- `frontend/pages/` - Page-level components
- `frontend/hooks/` - Custom React hooks
- `frontend/utils/` - Client-side utilities
- `frontend/styles/` - CSS/styling

**Focus:**
- User interfaces
- Component state management
- API integration
- Data visualization
- User experience

## 📋 File Organization Rules

### Backend Files

**Models** (`backend/models/`)
- Nama: `snake_case.py`
- Contoh: `time_study_recorder.py`, `spec_version_tracker.py`
- Content: Python classes, data structures

**Services** (`backend/services/`)
- Nama: `snake_case.py`
- Contoh: `sampling_rd_workflow.py`, `analysis_service.py`
- Content: Business logic, workflows, complex operations

**Utils** (`backend/utils/`)
- Nama: `snake_case.py`
- Contoh: `time_study_patterns.py`, `calculations.py`
- Content: Helper functions, algorithms, utilities

**API Routes** (`backend/api/`)
- Nama: `snake_case_routes.py`
- Contoh: `time_study_routes.py`, `spec_version_routes.py`
- Content: API endpoints, request/response handlers

### Frontend Files

**Components** (`frontend/components/`)
- Nama: `PascalCase.jsx`
- Contoh: `TimeStudyRecorder.jsx`, `SpecVersionTracker.jsx`
- Content: Reusable React components

**Pages** (`frontend/pages/`)
- Nama: `PascalCase.jsx`
- Contoh: `SamplingPage.jsx`, `SpecRnDPage.jsx`
- Content: Full page components

**Hooks** (`frontend/hooks/`)
- Nama: `usePascalCase.js`
- Contoh: `useTimeStudy.js`, `useSpecVersion.js`
- Content: Custom React hooks

**Utils** (`frontend/utils/`)
- Nama: `camelCase.js`
- Contoh: `api-client.js`, `formatters.js`
- Content: Utility functions, API clients, helpers

**Styles** (`frontend/styles/`)
- Nama: `ComponentName.module.css`
- Contoh: `TimeStudy.module.css`, `SpecVersion.module.css`
- Content: Component-scoped CSS

## 🔄 Communication Between Frontend & Backend

### API Contract
```
Frontend → HTTP Request → Backend API
Backend ← HTTP Response → Frontend
```

**Location**: `backend/api/` - Define API endpoints
**Location**: `frontend/utils/api-client.js` - Consume API

### Shared Data Models

**Backend** defines data structure:
```python
# backend/models/time_study_recorder.py
def to_dict(self) -> Dict:
    return {
        'spec_id': ...,
        'phases': [...],
        'total_duration': ...
    }
```

**Frontend** consumes it:
```javascript
// frontend/hooks/useTimeStudy.js
const [timeStudy, setTimeStudy] = useState({
  spec_id: '',
  phases: [],
  total_duration: 0
})
```

## 🚀 Development Workflow

### Backend Development

1. **Create Model** → `backend/models/your_model.py`
   ```python
   class YourModel:
       def __init__(self):
           pass
   ```

2. **Create Service** → `backend/services/your_service.py`
   ```python
   def your_logic():
       model = YourModel()
       return model.process()
   ```

3. **Create API Route** → `backend/api/your_routes.py`
   ```python
   @app.post('/api/your-endpoint')
   def handle_your_request():
       result = your_service()
       return jsonify(result)
   ```

4. **Update Utils** → `backend/utils/` if needed
   - Helper functions
   - Calculation functions
   - Patterns

### Frontend Development

1. **Create Component** → `frontend/components/YourComponent.jsx`
   ```jsx
   function YourComponent() {
       return <div>...</div>
   }
   ```

2. **Create Hook** → `frontend/hooks/useYourData.js` (if needed)
   ```javascript
   function useYourData() {
       const [data, setData] = useState(null)
       return { data, setData }
   }
   ```

3. **Add Styling** → `frontend/styles/YourComponent.module.css`
   ```css
   .container {
       /* styles */
   }
   ```

4. **Create Page** → `frontend/pages/YourPage.jsx`
   ```jsx
   function YourPage() {
       return <YourComponent />
   }
   ```

## 📝 Documentation Location

- **Module Guide**: `SAMPLING_SPEC_RND_GUIDE.md` ← Start here!
- **Code Examples**: `backend/services/sampling_rd_workflow.py`
- **API Reference**: TBD (to be created)
- **Component Library**: TBD (to be created)
- **Naming Standards**: `conventions/NAMING_CONVENTIONS.md`

## 🔍 Finding What You Need

| Need | Location |
|------|----------|
| Python model to extend | `backend/models/` |
| Utility function to use | `backend/utils/` |
| API endpoint reference | `backend/api/` |
| Complete workflow example | `backend/services/sampling_rd_workflow.py` |
| React component to use | `frontend/components/` |
| Custom hook to create | `frontend/hooks/` |
| Helper function (frontend) | `frontend/utils/` |
| Component styling | `frontend/styles/` |

## 💡 Best Practices

### Backend
- ✅ Keep models focused on data structure
- ✅ Put business logic in services
- ✅ Extract common functions to utils
- ✅ Document API endpoints clearly
- ✅ Use type hints in Python

### Frontend
- ✅ Keep components small & reusable
- ✅ Use custom hooks for logic
- ✅ Scope styles to components
- ✅ Centralize API calls in utils
- ✅ Use PascalCase for components

### Both
- ✅ Follow naming conventions
- ✅ Add JSDoc/docstring comments
- ✅ Keep files focused on single responsibility
- ✅ Update INVENTORY.md when adding files
- ✅ Communicate API contract early

## 📊 Current Status

| Layer | Status | Files |
|-------|--------|-------|
| Backend Models | ✅ Ready | 2 |
| Backend Services | ✅ Ready | 1 |
| Backend Utils | ✅ Ready | 2 |
| Backend API | 📋 TODO | 0 |
| Frontend Components | ✅ Ready | 2 |
| Frontend Pages | 📋 TODO | 0 |
| Frontend Hooks | 📋 TODO | 0 |
| Frontend Utils | ✅ Ready | 1 |
| Frontend Styles | 📋 TODO | 0 |

---

**Last Updated**: 2026-10-13  
**Structure Version**: 1.0  
**Team**: Backend + Frontend
