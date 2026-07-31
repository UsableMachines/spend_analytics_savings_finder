This repository is managed by the KinHelm Studio agent.

## Application: Spend Analytics Savings Finder

**Type:** Aggregation / Procurement Analytics

Analyzes procurement spend to identify savings, supplier consolidation,
contract leakage, and maverick purchasing opportunities.

### Architecture

- **Framework:** Flask 3.1 + SQLAlchemy + Gunicorn
- **Database:** SQLite (configurable via DATABASE_URL)
- **Auth:** Flask-Login with RBAC (admin, analyst, viewer)
- **Multi-tenancy:** Tenant-scoped queries on all data models
- **AI Integration:** Kindo Agent API for spend analysis

### Key Files

| File | Purpose |
|---|---|
| `wsgi.py` | Gunicorn entry point |
| `app/__init__.py` | Flask app factory with blueprint registration |
| `app/models.py` | SQLAlchemy models (Tenant, User, Role, Supplier, Contract, SpendRecord, AnalysisRun, Finding) |
| `app/services/kindo_service.py` | Kindo AI agent integration |
| `app/routes/auth.py` | Login, register, logout, role_required decorator |
| `app/routes/main.py` | Dashboard |
| `app/routes/spend.py` | Spend record CRUD |
| `app/routes/suppliers.py` | Supplier CRUD |
| `app/routes/contracts.py` | Contract CRUD |
| `app/routes/analysis.py` | AI analysis runs |
| `app/routes/admin.py` | User/tenant management |
| `app/routes/api.py` | CSV import, theme API |
| `app/routes/getting_started.py` | Getting Started page |
| `agent/agent-config.yaml` | Kindo agent system prompt |
| `Dockerfile` | Container build |
| `gunicorn.conf.py` | Gunicorn configuration |

### Blueprints

| Blueprint | Prefix | File |
|---|---|---|
| auth_bp | (none) | auth.py |
| main_bp | (none) | main.py |
| spend_bp | (none) | spend.py |
| suppliers_bp | (none) | suppliers.py |
| contracts_bp | (none) | contracts.py |
| analysis_bp | (none) | analysis.py |
| admin_bp | /admin | admin.py |
| api_bp | /api | api.py |
| gs_bp | (none) | getting_started.py |

### Default Credentials

- Username: `admin` / Password: `admin`
- Change immediately after first login.
