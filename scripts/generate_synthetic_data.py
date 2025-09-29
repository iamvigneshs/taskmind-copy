# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Seed synthetic MissionMind data into the configured database."""
from __future__ import annotations

import random
from datetime import date, timedelta

from sqlmodel import Session

from app.database import session_scope
from app.models import Authority, OrgUnit, Task
from app.services.routing import compute_priority
from sqlmodel import select

ORG_UNITS = [
    ("OPS_G3", "G3 Operations", "HQDA", None),
    ("DIV-3ID-G3", "3ID G3", "Division", "OPS_G3"),
    ("LOG_G4", "G4 Logistics", "HQDA", None),
    ("ACOM-G4", "ACOM G4", "ACOM", "LOG_G4"),
]

AUTHORITIES = [
    ("AUTH-1", "G3 Chief", "OPS_G3", "O6", ["operations", "training"]),
    ("AUTH-2", "3ID G3", "DIV-3ID-G3", "O6", ["readiness", "operations"]),
    ("AUTH-3", "ACOM G4", "ACOM-G4", "SES", ["logistics", "sustainment"]),
]

TAGS = [["readiness", "training"], ["logistics"], ["intel"], ["policy"], ["budget"]]
DESCRIPTIONS = [
    "Compile quarterly readiness statistics and highlight gaps.",
    "Prepare logistics sustainment plan for rotation.",
    "Draft intelligence summary for upcoming exercise.",
    "Update mobilization policy for reserve components.",
    "Assemble budget variance analysis for leadership review.",
]


def seed_reference(session: Session) -> None:
    for org_id, name, echelon, parent_id in ORG_UNITS:
        if not session.get(OrgUnit, org_id):
            session.add(OrgUnit(id=org_id, name=name, echelon=echelon, parent_id=parent_id))
    for auth_id, title, org_unit_id, grade, scope in AUTHORITIES:
        if not session.get(Authority, auth_id):
            session.add(
                Authority(
                    id=auth_id,
                    title=title,
                    org_unit_id=org_unit_id,
                    grade=grade,
                    authority_scope=scope,
                )
            )
    session.commit()


def seed_tasks(session: Session, count: int = 10) -> None:
    existing = len(session.exec(select(Task)).all())
    for idx in range(count):
        title_idx = (existing + idx) % len(DESCRIPTIONS)
        tags = random.choice(TAGS)
        org = "DIV-3ID-G3" if "readiness" in tags else "ACOM-G4"
        task = Task(
            id=f"T-25-{existing + idx + 1:06d}",
            title=DESCRIPTIONS[title_idx].split(" ")[0].capitalize() + " task",
            description=DESCRIPTIONS[title_idx],
            classification="U",
            suspense_date=date.today() + timedelta(days=random.randint(2, 21)),
            originator="HQDA DCS G-3/5/7" if "readiness" in tags else "ACOM G-4",
            org_unit_id=org,
            status="open",
            tags=tags,
        )
        task.priority_score = compute_priority(task)
        session.add(task)
    session.commit()


def check_data_exists(session: Session) -> bool:
    """Check if data already exists in the database."""
    tasks = session.exec(select(Task).limit(1)).all()
    return len(tasks) > 0


def main() -> None:
    print("🌱 MissionMind Synthetic Data Generator")
    print("=" * 40)
    
    # Safety check
    with session_scope() as session:
        if check_data_exists(session):
            print("\n⚠️  WARNING: Database already contains tasks!")
            print("Adding more synthetic data may create duplicates.")
            
            choice = input("\nDo you want to continue? (y/N): ").strip().lower()
            if choice != 'y':
                print("✅ Exiting safely. No data added.")
                return
    
    print("\n🔄 Seeding reference data...")
    with session_scope() as session:
        seed_reference(session)
        
    print("🔄 Generating synthetic tasks...")
    with session_scope() as session:
        seed_tasks(session)
        
    print("\n✅ Synthetic data seeding complete!")


if __name__ == "__main__":
    main()
