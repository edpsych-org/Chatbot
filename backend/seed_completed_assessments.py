"""
One-off dev script: fill in synthetic completed assessment data for selected
students so the psychologist workspace's Generate Report button unlocks.

Targets the local Postgres database (DATABASE_URL from .env). For each
target student it:
  1. Marks every non-cancelled AssessmentAssignment as COMPLETED.
  2. Ensures each assignment has a ChatSession with status='completed' and
     a populated context_data shape (user_profile + assessment_data +
     completed_qa_pairs) varied per role (Mother / Father / School).

Run: cd backend && python seed_completed_assessments.py
"""

from __future__ import annotations

import asyncio
import uuid as uuid_lib
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select, and_

from app.core.database import AsyncSessionLocal
from app.models.assignment import AssessmentAssignment, AssignmentStatus
from app.models.chat import ChatSession, ChatSessionStatus
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.models.user import User


TARGET_STUDENTS = [
    "Multitest Pupil",
    "Legacy Kid",
    "saravanan V",
]


def _qas_for_role(role: str, student_first: str) -> list[dict]:
    """Realistic-looking Q&A pairs tailored to the assessor's perspective."""
    base = [
        {
            "question_text": f"Tell us a bit about {student_first}'s strengths.",
            "answer_text": "",
            "category": "general",
            "answer_type": "text",
        },
        {
            "question_text": f"What concerns brought you to seek an assessment for {student_first}?",
            "answer_text": "",
            "category": "general",
            "answer_type": "text",
        },
        {
            "question_text": "How would you describe their attention and focus?",
            "answer_text": "",
            "category": "attention",
            "answer_type": "text",
        },
        {
            "question_text": "How do they manage emotions when frustrated?",
            "answer_text": "",
            "category": "emotional",
            "answer_type": "text",
        },
        {
            "question_text": "How do they get on with peers?",
            "answer_text": "",
            "category": "social",
            "answer_type": "text",
        },
        {
            "question_text": "Any concerns around reading, writing, or maths?",
            "answer_text": "",
            "category": "academic",
            "answer_type": "text",
        },
        {
            "question_text": "Anything else you'd like the psychologist to know?",
            "answer_text": "",
            "category": "general",
            "answer_type": "text",
        },
    ]

    role_norm = (role or "").strip().lower()

    if role_norm in ("mother", "parent"):
        answers = [
            f"{student_first} is a kind and curious child who loves drawing and animals. They notice small details and remember things from years ago.",
            "Reading aloud has been a recent worry. They get embarrassed when they stumble and refuse to try again. Homework time turns into tears about three nights a week.",
            "Concentration is fine for things they enjoy — Lego, drawing — but they wander after about ten minutes on schoolwork.",
            "When frustrated they tend to go quiet and walk away. Once calm they will talk about it but it takes 15-20 minutes.",
            "They have one or two close friends and prefer small groups. Big playground games overwhelm them.",
            "Reading is the main worry. Maths is fine. Spelling is inconsistent — they can spell a word correctly Monday and forget it Wednesday.",
            "Sleep has been broken for the last two months — taking 30-40 minutes to settle. We wonder if some of the school worry is leaking into bedtime.",
        ]
    elif role_norm == "father":
        answers = [
            f"{student_first} is determined and very physical — football, climbing, anything outdoors. Loyal to friends and protective of younger cousins.",
            "We're worried they're falling behind in class but I see them as bright and capable at home. Two different children depending on the setting.",
            "On a football pitch they can focus for an hour. With a worksheet they're up after a couple of minutes.",
            "They get angry quickly and it shows physically — clenched fists, stomping. They've never been violent toward another child but it's intense.",
            "Loves a small group of mates. Doesn't like being in charge of a game.",
            "I think they understand more than they can show on paper. The writing is the problem, not the thinking.",
            "Mornings before school are getting harder. They've started saying their stomach hurts on Mondays.",
        ]
    elif role_norm == "school":
        answers = [
            f"{student_first} is a polite student who is well-liked by adults. Engages well 1:1 and contributes when called on, though rarely volunteers.",
            "Concerns from class teachers around reading fluency and written expression. Tasks frequently incomplete. Significant gap between oral discussion and written output.",
            "Attention varies by task. Consistently good in practical/hands-on lessons; drifts in extended writing tasks. Often last to start.",
            "Generally regulated in school. Has had two incidents this term where they put their head on the desk and refused to engage for the rest of the lesson — both during literacy.",
            "Has a small consistent friendship group. Avoids unstructured free play with the wider class. PE and group projects go well.",
            "Reading age is currently around 18 months below chronological. Spelling errors include letter reversals and phonological gaps. Maths is broadly age-appropriate.",
            "Parents have engaged well with the SENCo. We have started a literacy intervention twice weekly but have not yet seen meaningful progress after six weeks.",
        ]
    else:
        answers = [
            f"{student_first} is a thoughtful child with strong interests and a close circle of friends.",
            "Concerns centre on schoolwork — particularly literacy — and on intermittent emotional regulation difficulties.",
            "Attention is uneven; better for preferred and hands-on activities.",
            "Frustration is shown through withdrawal more than outward outbursts.",
            "Sociable but prefers small groups.",
            "Reading is the biggest gap; maths is age-appropriate.",
            "We would value clarity on next steps and any specific strategies.",
        ]

    for q, a in zip(base, answers):
        q["answer_text"] = a
    return base


def _context_for(student: Student, role: str, qa_pairs: list[dict]) -> dict:
    age = None
    if student.date_of_birth:
        age = (datetime.now().date() - student.date_of_birth).days // 365
    student_first = student.first_name
    return {
        "user_profile": {
            "student_name": f"{student.first_name} {student.last_name}".strip(),
            "student_age": age,
            "school_name": student.school_name,
            "year_group": student.year_group,
        },
        "assessment_data": {
            qa["category"]: {
                "indicator": qa["question_text"],
                "free_text": qa["answer_text"],
            }
            for qa in qa_pairs
        },
        "completed_qa_pairs": qa_pairs,
        "explored_areas": list({qa["category"] for qa in qa_pairs}),
        "answered_node_ids": [f"node_{i}" for i in range(len(qa_pairs))],
        "perspective_role": role,
    }


async def main():
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        for label in TARGET_STUDENTS:
            first, *rest = label.split(" ", 1)
            last = rest[0] if rest else ""
            stmt = select(Student).where(
                and_(Student.first_name == first, Student.last_name == last)
            )
            student = (await db.execute(stmt)).scalar_one_or_none()
            if not student:
                print(f"  - {label}: NOT FOUND, skipping")
                continue

            assignments = (
                await db.execute(
                    select(AssessmentAssignment).where(
                        and_(
                            AssessmentAssignment.student_id == student.id,
                            AssessmentAssignment.status != AssignmentStatus.CANCELLED,
                        )
                    )
                )
            ).scalars().all()

            if not assignments:
                print(f"  - {label}: no active assignments, skipping")
                continue

            print(f"\n* {label} — {len(assignments)} assignment(s)")

            for a in assignments:
                # Look up the guardian's role
                sg = (
                    await db.execute(
                        select(StudentGuardian).where(
                            and_(
                                StudentGuardian.student_id == student.id,
                                StudentGuardian.guardian_user_id == a.assigned_to_user_id,
                            )
                        )
                    )
                ).scalar_one_or_none()
                user = (
                    await db.execute(select(User).where(User.id == a.assigned_to_user_id))
                ).scalar_one_or_none()
                role = (sg.relationship_type if sg else None) or (
                    user.role.value.title() if user else "Guardian"
                )

                qa_pairs = _qas_for_role(role, student.first_name)
                context = _context_for(student, role, qa_pairs)

                # Find any existing chat session for this assignment, else create one
                session = (
                    await db.execute(
                        select(ChatSession).where(ChatSession.assignment_id == a.id)
                    )
                ).scalars().first()

                if session is None:
                    session = ChatSession(
                        id=uuid_lib.uuid4(),
                        assignment_id=a.id,
                        user_id=a.assigned_to_user_id,
                        user_type="parent" if role.lower() != "school" else "school",
                        flow_type="parent_assessment_v1",
                        status=ChatSessionStatus.COMPLETED.value,
                        current_step=len(qa_pairs),
                        current_node_id=f"node_{len(qa_pairs) - 1}",
                        context_data=context,
                        started_at=now,
                        last_interaction_at=now,
                        completed_at=now,
                        duration_minutes=24,
                    )
                    db.add(session)
                    print(f"    + new ChatSession for {role} ({user.email if user else '?'})")
                else:
                    session.status = ChatSessionStatus.COMPLETED.value
                    session.context_data = context
                    session.completed_at = now
                    session.last_interaction_at = now
                    session.duration_minutes = session.duration_minutes or 24
                    print(f"    ~ updated ChatSession {str(session.id)[:8]} for {role}")

                a.status = AssignmentStatus.COMPLETED
                a.completed_at = now
                if not a.started_at:
                    a.started_at = now
                print(f"    ~ assignment {str(a.id)[:8]} → COMPLETED ({role})")

        await db.commit()

    print("\nDone. Refresh /psychologist/dashboard or the student's workspace.")


if __name__ == "__main__":
    asyncio.run(main())
