# MissionMind MCP MVP API

This repository contains a FastAPI-based microservice that exposes the MissionMind task orchestration APIs, scoped for a demo MVP. It includes automatic routing, authority recommendation heuristics, quality checks, and synthetic data generation aligned with the MCP tool surface defined in `docs/missionmind-functional-spec.md`.

## 1. Prerequisites
- Python 3.11+
- `pip` for dependency installation
- Optional: Docker (for containerized demo)
- Optional: AWS account with permissions to create an RDS PostgreSQL instance

## 2. Local Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To run the API locally with SQLite:
```bash
uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for the interactive OpenAPI UI.

## 3. AWS RDS (PostgreSQL) Configuration Instructions
1. **Create the database instance**
   - Engine: PostgreSQL 15 (RDS or Aurora Postgres Serverless works for the MVP).
   - Instance size: `db.t3.micro` is sufficient for demo loads.
   - Storage: 20 GB (gp3 is fine).
   - Credentials: define master username/password, ensure it complies with DoD policy.
   - VPC & security group: allow inbound traffic on the chosen Postgres port (default `5432`) from your development IP or VPC subnets.
2. **Create the database**
   - After the instance is available, connect using `psql` or AWS Query Editor and create a database named `missionmind`.
   ```sql
   CREATE DATABASE missionmind;
   ```
3. **Configure environment variables for the API**
   ```bash
   export DATABASE_URL="postgresql+psycopg2://<username>:<password>@<rds-endpoint>:5432/missionmind"
   ```
   Replace `<username>`, `<password>`, and `<rds-endpoint>` with your values. Add `?sslmode=require` if your organization mandates SSL.
4. **Install the PostgreSQL driver**
   ```bash
   pip install "psycopg2-binary>=2.9"
   ```
5. **Initialize schema & seed data**
   ```bash
   python -m app.main  # triggers startup init when importing
   python scripts/generate_synthetic_data.py
   ```

## 4. Synthetic Data Generation
Run the seeding script once the database is reachable:
```bash
python scripts/generate_synthetic_data.py
```
The script inserts reference org units, authorities, and 10 demo tasks with heuristic priority scores.

## 5. Running Unit Tests
```bash
pytest
```
Tests cover task creation (including auto-routing), summary generation, authority suggestions, and quality checks.

## 6. Example Workflow
1. **Create a Task**
   ```bash
   http POST :8000/tasks/ \
     title="Provide training readiness summary" \
     description="G3 to consolidate Q3 readiness data." \
     classification=U \
     suspense_date=2025-09-19 \
     originator="HQDA DCS G-3/5/7" \
     org_unit_id="DIV-3ID-G3" \
     tags:='["readiness","training"]'
   ```
2. **Review assignments and authority suggestions**
   ```bash
   http GET :8000/tasks/T-25-000001
   http GET :8000/tasks/T-25-000001/authority-suggestions
   ```
3. **Invoke MCP-aligned tools** (via REST in the MVP)
   ```bash
   http GET :8000/tasks/T-25-000001/summary
   http GET :8000/tasks/T-25-000001/quality-check
   http GET :8000/tasks/T-25-000001/risk
   ```

## 7. Next Steps Toward Production
- Replace SQLite with managed PostgreSQL (RDS) by default and enable migrations (Alembic).
- Integrate real MCP transport and authentication with Army 365.
- Swap heuristic summaries with approved LLM endpoints.
- Expand testing with contract tests and load tests before rolling demos.
