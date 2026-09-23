# Production Deployment Guide: Natural Language Incident Analytics & Reporting

This guide details setup, local development, ServiceNow Personal Developer Instance (PDI) connectivity, and production Docker containerization.

---

## 1. Prerequisites

- **Python**: 3.10+ (Tested with 3.13)
- **Node.js**: 18+ or 20+ (with `npm`)
- **ServiceNow PDI**: Free instance from [developer.servicenow.com](https://developer.servicenow.com) (e.g. `https://dev12345.service-now.com`)
- **Docker & Docker Compose**: (Optional, for containerized production setup)

---

## 2. Local Quickstart (Out-of-the-Box)

### Step 1: Start Backend
```powershell
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend starts at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

### Step 2: Start Frontend
In a separate terminal:
```powershell
cd frontend
npm run dev
```
The frontend UI will be live at `http://localhost:5173`.

---

## 3. Configuring ServiceNow Personal Developer Instance (PDI)

### A. Wake up your ServiceNow PDI
1. Go to [https://developer.servicenow.com](https://developer.servicenow.com) and log in.
2. If your instance is hibernating, click **Wake Up Instance** (PDIs automatically hibernate after 2 hours of inactivity).

### B. Configure Credentials in the UI
1. Open the application UI at `http://localhost:5173`.
2. Navigate to **Admin Settings** in the left sidebar.
3. Enter your ServiceNow details:
   - **ServiceNow Instance URL**: `https://devXXXXX.service-now.com`
   - **Username**: `admin`
   - **Password**: Your instance admin password
4. Click **Test Connection**. The system tests connectivity to `/api/now/table/incident` and verifies authentication.
5. Click **Save Configuration**.

### C. ServiceNow Roles Required
Ensure the service account user has read access to the following ServiceNow tables:
- `incident` (ITIL role or `sn_incident_read`)
- `problem`
- `change_request`
- `cmdb_ci`
- `sys_user`

### D. Enabling CORS in ServiceNow (Optional if calling from custom browser domains directly)
By default, the Python FastAPI backend acts as the secure server-side API Gateway, which means browser CORS restrictions against ServiceNow do not apply! If you wish to enable direct browser access in ServiceNow:
1. In ServiceNow Navigator, type `sys_cors_rule.list`.
2. Click **New**.
3. Name: `IncidentAI Web Application`.
4. Domain: `http://localhost:5173` (or your production domain).
5. HTTP methods: `GET, POST, OPTIONS`.

---

## 4. Docker Production Deployment

### Step 1: Configure Environment Variables
Create `.env` in the root folder:
```env
SERVICENOW_INSTANCE_URL=https://dev12345.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your_password
SERVICENOW_USE_MOCK_FALLBACK=false
LLM_PROVIDER=semantic_engine
OPENAI_API_KEY=
NVIDIA_API_KEY=
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.3-70b-instruct
```

### Step 2: Build and Run with Docker Compose
```bash
docker compose up --build -d
```

Containers provisioned:
1. `incident_ai_frontend`: Nginx serving optimized React bundle on Port 80.
2. `incident_ai_backend`: FastAPI running with Uvicorn on Port 8000.
3. `incident_ai_postgres`: PostgreSQL 16 database storing audit logs and cache on Port 5432.
4. `incident_ai_redis`: Redis 7 managing session memory on Port 6379.

---

## 5. Testing & Verification

Run automated test suite:
```powershell
cd backend
python -m pytest tests/ -v
```

All 11 unit & integration tests validate:
- Natural language intent detection
- Date, priority, and team query translations
- ServiceNow MCP Table API retrieval
- KPI calculations (MTTR, MTBF, SLA breach rate)
- Recurring cluster detection (Customer Portal DB timeout 25x)
- PDF, Word (DOCX), and Excel (XLSX) binary generation
