"""
Seed script to add sample chatbot questions to the database
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.assessment import ChatbotQuestion
from app.core.config import settings


async def seed_questions():
    """Add sample questions to the database"""

    # Create async engine
    database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if questions already exist
        result = await session.execute(select(ChatbotQuestion))
        existing = result.scalars().all()

        if existing:
            print(f"Database already has {len(existing)} questions")
            return

        # Sample questions for educational psychological assessment
        questions = [
            # Behavioral Section
            {
                "question_number": 1,
                "section": "Behavioral",
                "question_text": "How would you describe your child's ability to focus on tasks?",
                "question_type": "SCALE",
                "options": {"min": 1, "max": 5, "labels": {"1": "Very Poor", "5": "Excellent"}},
                "is_required": True,
                "help_text": "Consider how long they can concentrate on homework or activities",
                "order_index": 1
            },
            {
                "question_number": 2,
                "section": "Behavioral",
                "question_text": "Does your child have difficulty following instructions?",
                "question_type": "YES_NO",
                "options": None,
                "is_required": True,
                "help_text": "Think about multi-step instructions at home or school",
                "order_index": 2
            },
            {
                "question_number": 3,
                "section": "Behavioral",
                "question_text": "How often does your child display impulsive behavior?",
                "question_type": "MULTIPLE_CHOICE",
                "options": {
                    "choices": [
                        {"value": "never", "label": "Never"},
                        {"value": "rarely", "label": "Rarely"},
                        {"value": "sometimes", "label": "Sometimes"},
                        {"value": "often", "label": "Often"},
                        {"value": "very_often", "label": "Very Often"}
                    ]
                },
                "is_required": True,
                "help_text": "Impulsive behavior includes acting without thinking about consequences",
                "order_index": 3
            },

            # Academic Section
            {
                "question_number": 4,
                "section": "Academic",
                "question_text": "How is your child performing in reading compared to their peers?",
                "question_type": "SCALE",
                "options": {"min": 1, "max": 5, "labels": {"1": "Far Below", "3": "Average", "5": "Far Above"}},
                "is_required": True,
                "help_text": "Based on teacher feedback or your observations",
                "order_index": 4
            },
            {
                "question_number": 5,
                "section": "Academic",
                "question_text": "Does your child struggle with mathematical concepts?",
                "question_type": "YES_NO",
                "options": None,
                "is_required": True,
                "help_text": "Consider both basic arithmetic and problem-solving",
                "order_index": 5
            },
            {
                "question_number": 6,
                "section": "Academic",
                "question_text": "Please describe any specific learning challenges your child faces:",
                "question_type": "TEXT",
                "options": None,
                "is_required": False,
                "help_text": "Be as detailed as possible - include subjects, specific difficulties, etc.",
                "order_index": 6
            },

            # Social & Emotional Section
            {
                "question_number": 7,
                "section": "Social & Emotional",
                "question_text": "How well does your child interact with peers?",
                "question_type": "SCALE",
                "options": {"min": 1, "max": 5, "labels": {"1": "Very Poorly", "5": "Very Well"}},
                "is_required": True,
                "help_text": "Consider friendships, group activities, and social situations",
                "order_index": 7
            },
            {
                "question_number": 8,
                "section": "Social & Emotional",
                "question_text": "Does your child show signs of anxiety or excessive worry?",
                "question_type": "YES_NO",
                "options": None,
                "is_required": True,
                "help_text": "This could include worry about school, social situations, or separation",
                "order_index": 8
            },
            {
                "question_number": 9,
                "section": "Social & Emotional",
                "question_text": "How often does your child experience emotional outbursts or meltdowns?",
                "question_type": "MULTIPLE_CHOICE",
                "options": {
                    "choices": [
                        {"value": "never", "label": "Never"},
                        {"value": "rarely", "label": "Rarely (less than once a month)"},
                        {"value": "sometimes", "label": "Sometimes (few times a month)"},
                        {"value": "often", "label": "Often (weekly)"},
                        {"value": "daily", "label": "Daily or multiple times a day"}
                    ]
                },
                "is_required": True,
                "help_text": "Meltdowns are intense emotional reactions disproportionate to the situation",
                "order_index": 9
            },

            # Communication Section
            {
                "question_number": 10,
                "section": "Communication",
                "question_text": "How would you rate your child's verbal communication skills?",
                "question_type": "SCALE",
                "options": {"min": 1, "max": 5, "labels": {"1": "Very Limited", "5": "Excellent"}},
                "is_required": True,
                "help_text": "Consider vocabulary, sentence structure, and clarity of expression",
                "order_index": 10
            },
            {
                "question_number": 11,
                "section": "Communication",
                "question_text": "Does your child have difficulty understanding non-verbal cues (facial expressions, tone of voice)?",
                "question_type": "YES_NO",
                "options": None,
                "is_required": True,
                "help_text": "Non-verbal communication includes body language and social signals",
                "order_index": 11
            },
            {
                "question_number": 12,
                "section": "Communication",
                "question_text": "Please share any concerns about your child's communication abilities:",
                "question_type": "TEXT",
                "options": None,
                "is_required": False,
                "help_text": "Include both strengths and challenges",
                "order_index": 12
            }
        ]

        # Add all questions
        for q_data in questions:
            question = ChatbotQuestion(**q_data)
            session.add(question)

        await session.commit()
        print(f"Successfully added {len(questions)} sample questions to the database")

        # Verify
        result = await session.execute(select(ChatbotQuestion))
        all_questions = result.scalars().all()
        print(f"Total questions in database: {len(all_questions)}")


if __name__ == "__main__":
    print("Seeding chatbot questions...")
    try:
        asyncio.run(seed_questions())
        print("Seeding complete!")
    except Exception as e:
        print(f"Error seeding questions: {e}")
        sys.exit(1)
