# Spend Analytics Savings Finder

A procurement spend analytics application that identifies savings opportunities, supplier consolidation candidates, contract leakage, and maverick purchasing patterns. Powered by Kindo AI for intelligent analysis and recommendations.

## Features

- **Dashboard** — real-time overview of total spend, supplier count, contracts, and maverick transactions with visual charts
- **Spend Records** — full CRUD for procurement transactions with category/supplier filtering, CSV import, and maverick flagging
- **Supplier Management** — track your vendor base with categories and status
- **Contract Tracking** — manage supplier contracts with dates, values, and compliance linking
- **AI-Powered Analysis** — send spend data to a Kindo AI agent for savings identification, data validation, and enrichment
- **Multi-Tenancy** — organization-isolated data with tenant-scoped queries
- **Role-Based Access Control** — Admin, Analyst (edit), and Viewer (read-only) roles
- **Light/Dark Theme** — user-persisted theme preference
- **Getting Started Guide** — step-by-step onboarding for new users
- **Per-Page Help Panels** — contextual help drawers on every page

## Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and configure
3. Build and run:
   ```bash
   docker build -t savings-finder .
   docker run -p 8080:8080 --env-file .env savings-finder
   ```
4. Open http://localhost:8080
5. Log in with `admin` / `admin` (change the password immediately)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session secret key |
| `DATABASE_URL` | No | Database URI (default: SQLite) |
| `KINDO_API_TOKEN` | For AI | Kindo API bearer token |
| `KINDO_AGENT_ID` | For AI | Kindo agent identifier |
| `PORT` | No | Server port (default: 8080) |
| `SESSION_COOKIE_PATH` | No | Cookie path (default: /) |

## CSV Import Format

Upload via `POST /api/spend/import` with a CSV file containing:

```
supplier,description,amount,category,date,po_number,department,is_maverick
Acme Corp,Office supplies,1500.00,Office,2024-01-15,PO-001,Operations,false
```

## Default Credentials

- Username: `admin`
- Password: `admin`

Change immediately after first login via Admin → User Management.

## Technology Stack

- Python 3.11 / Flask
- SQLAlchemy + SQLite (configurable)
- Gunicorn
- Kindo AI Agent API
