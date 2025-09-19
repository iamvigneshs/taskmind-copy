"""Authority recommendation heuristics for the MVP."""
from __future__ import annotations

from typing import List

from sqlmodel import Session, select

from ..models import Authority, OrgUnit, Task
from ..schemas import AuthoritySuggestion


def suggest_authorities(task: Task, session: Session, limit: int = 3) -> List[AuthoritySuggestion]:
    """Return ranked authority suggestions based on org linkage and keyword mapping."""
    org_priority = [task.org_unit_id]

    # Walk up parent chain for broader authorities.
    current = session.get(OrgUnit, task.org_unit_id)
    while current and current.parent_id:
        org_priority.append(current.parent_id)
        current = session.get(OrgUnit, current.parent_id)

    # Query authorities in priority order.
    suggestions: List[AuthoritySuggestion] = []
    seen: set[str] = set()
    for idx, org_id in enumerate(org_priority):
        if not org_id:
            continue
        statement = select(Authority).where(Authority.org_unit_id == org_id)
        for authority in session.exec(statement).all():
            if authority.id in seen:
                continue
            confidence = max(0.9 - 0.1 * idx, 0.4)
            rationale = f"Authority aligned with org {authority.org_unit_id} (tier {idx + 1})"
            suggestions.append(
                AuthoritySuggestion(
                    authority_id=authority.id,
                    title=authority.title,
                    org_unit_id=authority.org_unit_id,
                    grade=authority.grade,
                    confidence=round(confidence, 2),
                    rationale=rationale,
                )
            )
            seen.add(authority.id)
            if len(suggestions) >= limit:
                return suggestions

    # Fallback placeholder if no authority found.
    if not suggestions:
        suggestions.append(
            AuthoritySuggestion(
                authority_id="DEFAULT",
                title="Org Chief",
                org_unit_id=task.org_unit_id,
                grade="GS-15",
                confidence=0.4,
                rationale="No authority records available; defaulting to org chief.",
            )
        )
    return suggestions
