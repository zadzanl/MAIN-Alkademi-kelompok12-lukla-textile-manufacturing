# Lukla Operations Engine — Garment Manufacturing ERP Platform

Enterprise operations platform for garment and textile contract manufacturing (maklon / konveksi), integrating sample R&D, warehouse inventory, cutting batching, line sewing piece-rate production, multi-tier quality inspection, and tiered piece-rate payroll with financial controls.

---

## 📌 Architecture & Design Baseline

The repository is organized following an OpenSpec contract-first, specification-driven approach:

- **Core Technical Blueprint:** Complete Phase A, B, and C planning baseline located in [`openspec/changes/lukla-ops-engine-planning/`](./openspec/changes/lukla-ops-engine-planning/).
- **OpenAPI 3.1 Contract:** Full API catalog with 69 HTTP operations and 111 component schemas at [`contracts/openapi.yaml`](./openspec/changes/lukla-ops-engine-planning/contracts/openapi.yaml).
- **Core Requirements:** Canonical BRD v2.3.0 and PRD v2.0 defining 20 core Functional Requirements (`FR-1.1`..`FR-10.4`), 8 RBAC roles, and operational closing scenarios.
- **Enterprise Modules Architecture:** Architectural reference for all 6 future core modules documented in [`docs/MODULES_ARCHITECTURE.md`](./docs/MODULES_ARCHITECTURE.md).
- **User Operations Guide:** Complete role-based operational manual for factory staff, supervisors, and clients in [`USER_GUIDE.md`](./USER_GUIDE.md).

---

## 🗂️ Repository Structure

```text
.
├── openspec/                                # OpenSpec governance & specifications
│   ├── changes/
│   │   ├── lukla-ops-engine-planning/       # Approved planning change baseline
│   │   │   ├── contracts/openapi.yaml       # OpenAPI 3.1 contract (69 operations)
│   │   │   ├── specs/                       # 6 domain capability specifications
│   │   │   ├── reviews/                     # Formal review approvals (Phase A, B, C)
│   │   │   ├── research/                    # Architectural research & decisions
│   │   │   ├── 00-deconstruction.md         # Pitch deck transcription register
│   │   │   ├── 04-rbac-matrix.md            # 8 roles with IZIN / PEMBATASAN rules
│   │   │   ├── 06-acceptance-tests.md       # Acceptance tests (AT-01..AT-10, AT-R01..AT-R08)
│   │   │   ├── 10-technology-stack-and-decisions.md # Architecture Decision Records
│   │   │   ├── 11-database-schema-spec.md   # PostgreSQL schema, DDL, and RLS policies
│   │   │   ├── 16-test-harness-and-agent-verification.md # Test harness specification
│   │   │   ├── validate-blueprint.py        # Planning contract validator
│   │   │   └── verify-traceability.ps1      # Automated requirements traceability script
│   │   └── archive/                         # Archived proposals & superseded drafts
│   └── config.yaml                          # OpenSpec CLI configuration
│
├── prototypes/                              # Working prototypes & spikes
│   └── sampling-spec-rnd/                   # Standalone Sampling & Spec R&D prototype
│       ├── backend/                         # FastAPI backend (Port 8009)
│       └── frontend/                        # React 18 + Vite + Tailwind (Port 3009)
│
├── docs/                                    # System & module documentation
│   ├── MODULES_ARCHITECTURE.md              # 6-module system architecture specification
│   └── sampling-spec-rnd/                   # Prototype setup & architecture guides
│       ├── SETUP_GUIDE.md                   # Quickstart & team onboarding instructions
│       ├── ARCHITECTURE.md                  # Prototype layout & integration analysis
│       └── APPLE_DESIGN.md                  # Apple design system tokens & guidelines
│
├── USER_GUIDE.md                            # Panduan Pengguna Operasional Pabrik (8 Roles & 6 Views)
└── AGENTS.md                                # AI Agent pairing guidelines & engineering mode
```

---

## 🧪 Planning Verification Commands

To verify traceability and contract integrity of the Lukla Operations Engine blueprint:

```powershell
# 1. Verify complete requirements traceability (FRs, RBAC roles, closing scenarios)
pwsh -File openspec/changes/lukla-ops-engine-planning/verify-traceability.ps1

# 2. Validate OpenAPI 3.1 contract references, paths, and examples
python openspec/changes/lukla-ops-engine-planning/validate-blueprint.py

# 3. Validate OpenSpec change integrity
openspec validate lukla-ops-engine-planning
```

---

## 🚀 Running the Sampling & Spec R&D Prototype

A working reference prototype for the Sampling & Spec R&D workflow is available in `prototypes/sampling-spec-rnd/`:

1. **Backend (FastAPI on Port 8009):**
   ```bash
   cd prototypes/sampling-spec-rnd/backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn src.main:app --reload --port 8009
   ```

2. **Frontend (React + Vite on Port 3009):**
   ```bash
   cd prototypes/sampling-spec-rnd/frontend
   npm install
   npm run dev
   ```

For detailed setup, troubleshooting, and batch startup scripts, see the [Team Setup Guide](./docs/sampling-spec-rnd/SETUP_GUIDE.md).

---

## 🔒 Governance & Operational Principles

1. **Zero Silent Changes:** Business decisions subject to client clarification remain flagged as `PRODUCTION_BLOCKED` until authorized.
2. **Multi-Tenant Isolation:** Enforced via PostgreSQL Row-Level Security (`FORCE ROW LEVEL SECURITY`) with `tenant_id` session variables.
3. **Immutability & Audit Trails:** Financial ledgers and inventory transactions are append-only; reversals are recorded as explicit counter-entries.
