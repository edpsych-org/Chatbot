# Database Models
from app.models.user import User
from app.models.student import Student
from app.models.assessment import AssessmentSession, ChatbotQuestion, ChatbotAnswer
from app.models.assignment import AssessmentAssignment
from app.models.upload import IQTestUpload, CognitiveProfile
from app.models.report import AIGenerationJob, GeneratedReport, ReportReview, FinalReport
from app.models.magic_link import MagicLinkToken
from app.models.chat import ChatSession, ChatMessage, FlowDefinition, ConversationTemplate
from app.models.verification_token import VerificationToken

__all__ = [
    "User",
    "Student",
    "AssessmentSession",
    "AssessmentAssignment",
    "ChatbotQuestion",
    "ChatbotAnswer",
    "IQTestUpload",
    "CognitiveProfile",
    "AIGenerationJob",
    "GeneratedReport",
    "ReportReview",
    "FinalReport",
    "MagicLinkToken",
    "ChatSession",
    "ChatMessage",
    "FlowDefinition",
    "ConversationTemplate",
    "VerificationToken",
]
