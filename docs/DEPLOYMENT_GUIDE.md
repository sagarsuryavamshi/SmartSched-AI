# SmartSched AI — Cloud Deployment & Operations Guide

This guide describes how to deploy the production architecture:
- **Frontend:** Next.js 14+ on **Vercel**
- **Backend:** FastAPI on **Render**
- **Database:** Managed **PostgreSQL** on Render / Neon / AWS RDS

---

## 1. Managed PostgreSQL Deployment

1. On **Render** (or Neon / Supabase), provision a new **PostgreSQL 16+** database:
   - Database Name: `smartsched_db`
   - User: `smartsched_user`
2. Obtain the connection string:
   `postgresql://smartsched_user:<password>@<host>:5432/smartsched_db`
3. Execute the schema migration and data transfer from your local terminal:
   ```bash
   DATABASE_URL="<your_postgres_connection_string>" python backend/scripts/migrate_sqlite_to_postgres.py
   ```
   *Verification:* The script will assert that all table counts match 100% of the baseline records.

---

## 2. Backend Deployment on Render

1. Create a **New Web Service** connected to your GitHub repository.
2. Configure settings:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables:
   - `DATABASE_URL`: Your managed PostgreSQL connection URL.
   - `JWT_SECRET_KEY`: A cryptographically secure random string (`openssl rand -hex 32`).
   - `CORS_ORIGINS`: `https://smartsched-ai.vercel.app` (your Vercel frontend URL).
   - `ENVIRONMENT`: `production`
   - `DEBUG`: `false`
4. Health check endpoint: `/api/v1/health`
5. Once deployed, verify:
   ```bash
   curl -s https://<your-render-backend-url>/api/v1/health
   ```

---

## 3. Frontend Deployment on Vercel

1. Import your GitHub repository in the **Vercel Dashboard**.
2. Set Root Directory to: `frontend`
3. Framework Preset: `Next.js`
4. Configure Environment Variables:
   - `NEXT_PUBLIC_API_URL`: `https://<your-render-backend-url>/api/v1`
5. Deploy.
6. Once deployed, the frontend communicates with the Render FastAPI backend via HTTPS with JWT tokens and HttpOnly cookies.

---

## 4. Disaster Recovery & Automated Backups

- Run the automated backup shell script:
  ```bash
  PGDATABASE=smartsched_db PGHOST=<host> PGUSER=<user> PGPASSWORD=<pass> ./backend/scripts/backup_postgres.sh
  ```
- Restore an archive:
  ```bash
  gunzip -c ./data/backups/smartsched_pg_backup_<timestamp>.sql.gz | psql -h <host> -U <user> -d smartsched_db
  ```
