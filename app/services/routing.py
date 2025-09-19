# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Routing and prioritization heuristics for MissionMind MVP."""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple

from sqlmodel import Session

from ..models import Assignment, OrgUnit, Task

KEYWORD_SECTION_MAP: Dict[str, str] = {
    "readiness": "OPS_G3",
    "training": "OPS_G3",
    "intel": "INTEL_G2",
    "logistics": "LOG_G4",
    "personnel": "PERS_G1",
    "legal": "JA",
    "chaplain": "CHAP",
    "communications": "G6_CIO",
}

ORIGINATOR_WEIGHT: Dict[str, float] = {
    "HQDA": 1.0,
    "ACOM": 0.85,
    "ASCC": 0.8,
    "DRU": 0.75,
}

STATUS_WEIGHT = {
    "draft": 0.4,
    "in_work": 0.6,
    "open": 0.7,
    "overdue": 1.0,
}


def _urgency_score(suspense: date) -> float:
    days = (suspense - date.today()).days
    if days <= 0:
        return 1.0
    if days <= 3:
        return 0.85
    if days <= 7:
        return 0.7
    if days <= 14:
        return 0.5
    return 0.3


def _originator_score(originator: str) -> float:
    for key, weight in ORIGINATOR_WEIGHT.items():
        if key in originator.upper():
            return weight
    return 0.6


def _keyword_boost(tags: List[str], description: str) -> float:
    text = " ".join(tags + [description]).lower()
    matches = [kw for kw in KEYWORD_SECTION_MAP if kw in text]
    if not matches:
        return 0.0
    return min(0.2 + 0.1 * len(matches), 0.4)


def compute_priority(task: Task) -> float:
    base = 0.2
    base += 0.35 * _urgency_score(task.suspense_date)
    base += 0.25 * _originator_score(task.originator)
    base += 0.15 * _keyword_boost(task.tags, task.description)
    base += 0.05 * STATUS_WEIGHT.get(task.status, 0.5)
    return round(min(base, 1.0), 2)


def recommend_org_unit(task: Task, session: Session) -> Tuple[str, str]:
    """Return (org_unit_id, rationale)."""
    text = " ".join(task.tags + [task.title, task.description]).lower()
    for keyword, org_code in KEYWORD_SECTION_MAP.items():
        if keyword in text:
            org = session.get(OrgUnit, org_code)
            if org:
                return org.id, f"Matched keyword '{keyword}' with org {org.name}"
    # fallback to task org
    org = session.get(OrgUnit, task.org_unit_id)
    if org:
        return org.id, "Defaulted to originating org"
    return task.org_unit_id, "No org metadata available; used provided org_unit_id"


def generate_assignment(task: Task, session: Session) -> Assignment:
    org_id, rationale = recommend_org_unit(task, session)
    assignment = Assignment(
        task_id=task.id,
        assignee_type="org",
        assignee_id=org_id,
        role="owner",
        state="pending",
        rationale=rationale,
    )
    assignment.task = task
    # store rationale in details? using comment? For MVP we attach to state field? We'll use due_override_date as None
    return assignment
