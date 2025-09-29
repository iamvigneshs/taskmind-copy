from __future__ import annotations

import os
from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

# SAFETY: Tests will use the same database but with careful transaction management
# Tests will use transactions that are rolled back to avoid affecting data
os.environ["TESTING"] = "true"

# Import dotenv to load the DATABASE_URL from .env file
from dotenv import load_dotenv
load_dotenv()

from app.database import engine, get_session, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Authority, OrgUnit  # noqa: E402


def get_session_override():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = get_session_override


def setup_module(_: object) -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.get(OrgUnit, "OPS_G3"):
            session.add(OrgUnit(id="OPS_G3", name="G3 Operations", echelon="Division"))
        if not session.get(OrgUnit, "DIV-3ID-G3"):
            session.add(OrgUnit(id="DIV-3ID-G3", name="3ID G3", echelon="Division", parent_id="OPS_G3"))
        if not session.get(Authority, "AUTH-1"):
            session.add(
                Authority(
                    id="AUTH-1",
                    title="G3 Chief",
                    org_unit_id="DIV-3ID-G3",
                    grade="O6",
                    authority_scope=["operations", "readiness"],
                )
            )
        session.commit()


client = TestClient(app)


def test_create_task_generates_priority_and_assignment():
    payload = {
        "title": "Provide training readiness summary",
        "description": "G3 to consolidate Q3 readiness data across brigades.",
        "classification": "U",
        "suspense_date": (date.today() + timedelta(days=5)).isoformat(),
        "originator": "HQDA DCS G-3/5/7",
        "org_unit_id": "DIV-3ID-G3",
        "tags": ["readiness", "training"],
    }

    response = client.post("/tasks/", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["priority_score"] > 0
    assert body["assignments"], "Assignment should be auto-created"
    assert body["assignments"][0]["assignee_id"] == "DIV-3ID-G3"


def test_summary_endpoint_returns_consistent_structure():
    payload = {
        "title": "Compile logistics readiness report",
        "description": "Detailed supply readiness overview for upcoming rotation.",
        "classification": "U",
        "suspense_date": (date.today() + timedelta(days=10)).isoformat(),
        "originator": "ACOM G-4",
        "org_unit_id": "DIV-3ID-G3",
        "tags": ["logistics"],
    }
    create_resp = client.post("/tasks/", json=payload)
    task_id = create_resp.json()["id"]

    summary_resp = client.get(f"/tasks/{task_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert {"summary", "risk_level", "key_points"} <= summary.keys()


def test_authority_suggestions_use_org_hierarchy():
    payload = {
        "title": "Draft mobilization policy",
        "description": "Develop mobilization policy update.",
        "classification": "U",
        "suspense_date": (date.today() + timedelta(days=15)).isoformat(),
        "originator": "DIV HQ",
        "org_unit_id": "DIV-3ID-G3",
        "tags": ["policy"],
    }
    task_id = client.post("/tasks/", json=payload).json()["id"]

    resp = client.get(f"/tasks/{task_id}/authority-suggestions")
    assert resp.status_code == 200
    suggestions = resp.json()
    assert suggestions, "Should return at least one suggestion"
    assert suggestions[0]["authority_id"] == "AUTH-1"


def test_quality_check_reports_missing_arims():
    payload = {
        "title": "Short description",
        "description": "Brief.",
        "classification": "U",
        "suspense_date": (date.today() + timedelta(days=2)).isoformat(),
        "originator": "HQDA",
        "org_unit_id": "DIV-3ID-G3",
        "tags": [],
    }
    task_id = client.post("/tasks/", json=payload).json()["id"]
    qc_resp = client.get(f"/tasks/{task_id}/quality-check")
    assert qc_resp.status_code == 200
    result = qc_resp.json()
    codes = {issue["code"] for issue in result["issues"]}
    assert "ARIMS_TAG" in codes
