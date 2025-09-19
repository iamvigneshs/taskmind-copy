# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""LLM summary placeholder for MVP."""
from __future__ import annotations

from typing import List

from ..models import Task
from ..schemas import TaskSummary


def summarize_task(task: Task, comments: List[str]) -> TaskSummary:
    """Generate a lightweight heuristic summary.

    In the MVP we avoid external LLM calls and build a template-based response
    that highlights urgency, originator, and notable comment themes.
    """
    key_points: List[str] = []
    if task.priority_score >= 0.8:
        key_points.append("High priority task")
    if task.suspense_date:
        key_points.append(f"Due {task.suspense_date.isoformat()}")
    if task.tags:
        key_points.append("Tags: " + ", ".join(task.tags[:3]))
    if comments:
        key_points.append(f"Recent feedback snippets: {comments[0][:80]}...")

    summary_text = (
        f"Task {task.id} from {task.originator} focuses on {task.title}. "
        f"Classification {task.classification}. Priority score {task.priority_score}."
    )
    risk_level = "red" if task.priority_score >= 0.8 else "amber" if task.priority_score >= 0.5 else "green"
    return TaskSummary(summary=summary_text, risk_level=risk_level, key_points=key_points)
