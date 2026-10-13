# OpenCode Inventory - SAMPLING & SPEC R&D Module

Daftar lengkap semua backend & frontend files untuk module SAMPLING & SPEC R&D.

## 📁 Backend

### Models (`backend/models/`)
| Nama | File | Deskripsi | Status |
|------|------|-----------|--------|
| TimeStudyRecorder | `time_study_recorder.py` | Class untuk merekam time study dengan multiple phases | ✅ Ready |
| SpecVersionTracker | `spec_version_tracker.py` | Class untuk track spec versions & prevent R&D drift | ✅ Ready |

### Services (`backend/services/`)
| Nama | File | Deskripsi | Status |
|------|------|-----------|--------|
| SamplingRnDWorkflow | `sampling_rd_workflow.py` | Complete workflow: spec creation → time study → analysis → approval | ✅ Ready |

### Utils (`backend/utils/`)
| Nama | File | Deskripsi | Patterns | Status |
|------|------|-----------|----------|--------|
| time_study_patterns | `time_study_patterns.py` | Time study functions | 8 | ✅ Ready |
| spec_version_patterns | `spec_version_patterns.py` | Spec version functions | 9 | ✅ Ready |

### API Routes (`backend/api/`)
| Nama | File | Deskripsi | Endpoints | Status |
|------|------|-----------|-----------|--------|
| TimeStudy Routes | `time_study_routes.py` | Time study API endpoints | 5 | ✅ Ready |
| SpecVersion Routes | `spec_version_routes.py` | Spec version API endpoints | 5 | ✅ Ready |
| API Init | `__init__.py` | Blueprint registration | - | ✅ Ready |

---

## 📁 Frontend

### Components (`frontend/components/`)
| Nama | File | Deskripsi | Status |
|------|------|-----------|--------|
| TimeStudyRecorder | `TimeStudyRecorder.jsx` | React component untuk recording time study | ✅ Ready |
| SpecVersionTracker | `SpecVersionTracker.jsx` | React component untuk tracking spec versions | ✅ Ready |

### Hooks (`frontend/hooks/`)
| Nama | File | Deskripsi | Status |
|------|------|-----------|--------|
| useTimeStudy | `useTimeStudy.js` | Custom hook untuk time study data management | ✅ Ready |

### Utils (`frontend/utils/`)
| Nama | File | Deskripsi | Status |
|------|------|-----------|--------|
| api-client | `api-client.js` | Centralized API communication utility | ✅ Ready |
| time-study-patterns | `time-study-patterns.js` | JavaScript time study helpers | ✅ Ready |

### Pages (`frontend/pages/`)
| Nama | File | Status |
|------|------|--------|
| SamplingPage | `SamplingPage.jsx` | 📋 TODO |
| SpecRnDPage | `SpecRnDPage.jsx` | 📋 TODO |

### Styles (`frontend/styles/`)
| Nama | File | Status |
|------|------|--------|
| TimeStudy | `TimeStudy.module.css` | 📋 TODO |
| SpecVersion | `SpecVersion.module.css` | 📋 TODO |

---

## 📊 Summary

| Layer | Ready | TODO | Total |
|-------|-------|------|-------|
| Backend Models | 2 | 0 | 2 |
| Backend Services | 1 | 0 | 1 |
| Backend Utils | 2 | 0 | 2 |
| Backend API | 3 | 0 | 3 |
| **Backend Total** | **8** | **0** | **8** |
| Frontend Components | 2 | 0 | 2 |
| Frontend Hooks | 1 | 0 | 1 |
| Frontend Utils | 2 | 0 | 2 |
| Frontend Pages | 0 | 2 | 2 |
| Frontend Styles | 0 | 2 | 2 |
| **Frontend Total** | **5** | **4** | **9** |
| **TOTAL** | **13** | **4** | **17** |

---

## 🎯 API Endpoints

### Time Study Endpoints
```
POST   /api/v1/time-studies              Create time study
GET    /api/v1/time-studies              List time studies
GET    /api/v1/time-studies/:id          Get specific time study
DELETE /api/v1/time-studies/:id          Delete time study
POST   /api/v1/time-studies/:id/analyze  Analyze time study
```

### Spec Version Endpoints
```
POST   /api/v1/spec-versions               Create spec version
GET    /api/v1/spec-versions               List spec versions
GET    /api/v1/spec-versions/:id           Get specific version
PATCH  /api/v1/spec-versions/:id/status    Update version status
POST   /api/v1/spec-versions/:id/compare   Compare versions
POST   /api/v1/spec-versions/:id/drift-check  Check R&D drift
```

---

## 🚀 Quick Links

| Need | Path |
|------|------|
| Python Time Study Class | `backend/models/time_study_recorder.py` |
| Python Spec Version Class | `backend/models/spec_version_tracker.py` |
| Time Study API Implementation | `backend/api/time_study_routes.py` |
| Spec Version API Implementation | `backend/api/spec_version_routes.py` |
| React Time Study Component | `frontend/components/TimeStudyRecorder.jsx` |
| React Spec Version Component | `frontend/components/SpecVersionTracker.jsx` |
| Time Study Hook | `frontend/hooks/useTimeStudy.js` |
| API Communication | `frontend/utils/api-client.js` |
| Full Workflow Example | `backend/services/sampling_rd_workflow.py` |
| Module Structure | `STRUCTURE.md` |
| Quick Guide | `SAMPLING_SPEC_RND_GUIDE.md` |
| Naming Standards | `conventions/NAMING_CONVENTIONS.md` |

---

## 📝 Tips Untuk Tim

### Backend Team
1. Start dengan `backend/models/time_study_recorder.py`
2. Extend dengan database operations
3. Implement API endpoints di `backend/api/`
4. Add validation & error handling

### Frontend Team
1. Start dengan React components di `frontend/components/`
2. Use custom hooks untuk data management (lihat `frontend/hooks/useTimeStudy.js`)
3. Use `api-client.js` untuk API calls
4. Create pages untuk full features

### Collaborate
- Backend defines API contract (SPEC.md)
- Frontend consumes via `api-client.js`
- Share data models di file documentation
- Update INVENTORY.md saat add new files

---

**Last Updated**: 2026-10-13  
**Structure Version**: 2.0 (Backend + Frontend separated)  
**Total Files**: 17 (13 Ready, 4 TODO)
