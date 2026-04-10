"""
Hybrid Chat API - Multi-Agent Architecture
Combines MCQ flows with AI conversational responses using specialized agents:
- InputValidator: checks parent response quality
- EmpathyAgent: generates warm responses
- AssessmentAgent: extracts clinical insights
- BackgroundGenerator: builds comprehensive profiles
- OrchestratorAgent: coordinates all agents
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime, date
import json
import os
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.assignment import AssessmentAssignment, AssignmentStatus
from app.models.chat import ChatSession, ChatMessage, ChatSessionStatus, MessageRole, MessageType
from app.models.report import GeneratedReport, AIGenerationJob
from app.agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/hybrid-chat", tags=["hybrid-chat"])
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class ChatMessageInput(BaseModel):
    """User message input"""
    message_type: str  # "mcq_choice" | "free_text"
    content: str
    question_id: Optional[str] = None
    selected_option: Optional[str] = None
    choice_value: Optional[str] = None

    @property
    def resolved_option(self) -> Optional[str]:
        """Frontend sends choice_value, backend uses selected_option."""
        return self.selected_option or self.choice_value


class QuickReplyOption(BaseModel):
    """Quick reply button"""
    value: str
    label: str
    icon: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Bot message response"""
    id: str
    role: str
    message_type: str
    content: str
    options: Optional[List[QuickReplyOption]] = None
    allow_text: bool = False
    text_prompt: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Chat session with current state"""
    id: str
    status: str
    current_step: int
    total_steps: int
    progress_percentage: float
    student_name: str
    messages: List[ChatMessageResponse]

    class Config:
        from_attributes = True


class CurrentQuestionMeta(BaseModel):
    """Current question metadata for session resume"""
    message_type: str
    content: str
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class SessionMessageRecord(BaseModel):
    """Full message record for session history"""
    id: str
    role: str
    message_type: str
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionResumeResponse(BaseModel):
    """Full session resume response"""
    session_id: str
    status: str
    progress_percentage: float
    current_node_id: Optional[str] = None
    current_question: Optional[CurrentQuestionMeta] = None
    messages: List[SessionMessageRecord] = []

    class Config:
        from_attributes = True


class BotMessagePayload(BaseModel):
    """Bot message payload for frontend"""
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class StartChatResponse(BaseModel):
    """Response when starting a new chat session"""
    session_id: str
    bot_message: BotMessagePayload
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    """Response after sending a message"""
    bot_message: BotMessagePayload
    progress_percentage: float = 0
    status: str = "in_progress"
    is_complete: bool = False
    current_category: Optional[str] = None
    input_feedback: Optional[str] = None  # validation feedback for insufficient input

    class Config:
        from_attributes = True


class StartChatRequest(BaseModel):
    """Request to start a new chat session"""
    assignment_id: UUID


# ============================================================================
# FLOW ENGINE
# ============================================================================

class FlowEngine:
    """Handles flow navigation and MCQ processing"""

    def __init__(self):
        self.flows = {}
        self.load_flows()

    def load_flows(self):
        """Load flow definitions from JSON files"""
        flows_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "flows")
        if os.path.exists(flows_dir):
            for filename in os.listdir(flows_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(flows_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        flow_data = json.load(f)
                        self.flows[flow_data["flow_id"]] = flow_data

    def get_flow(self, flow_id: str):
        return self.flows.get(flow_id)

    def get_node(self, flow_id: str, node_id: str):
        flow = self.get_flow(flow_id)
        if flow:
            return flow["nodes"].get(node_id)
        return None

    def get_next_node_id(self, flow_id: str, current_node_id: str, user_choice: Optional[str] = None):
        """Determine next node based on user choice"""
        node = self.get_node(flow_id, current_node_id)
        if not node:
            return None

        if node["type"] in ["message", "text_only", "completion"]:
            return node.get("next")

        if node["type"] == "mcq" and user_choice:
            for option in node.get("options", []):
                if option["value"] == user_choice:
                    return option.get("next")
            return node.get("next")

        # MCQ without choice - use default next
        if node["type"] == "mcq":
            return node.get("next")

        return None

    def advance_past_messages(self, flow_id: str, node_id: str) -> tuple:
        """
        Auto-advance through non-interactive message nodes.
        Returns (final_node_id, final_node) - stops at interactive or terminal nodes.
        """
        current_id = node_id
        current_node = self.get_node(flow_id, current_id)

        while current_node and current_node.get("type") == "message":
            next_id = current_node.get("next")
            if not next_id:
                break
            next_node = self.get_node(flow_id, next_id)
            if not next_node:
                break
            current_id = next_id
            current_node = next_node

        return current_id, current_node

    def get_answerable_node_ids(self, flow_id: str) -> List[str]:
        flow = self.get_flow(flow_id)
        if not flow:
            return []
        return [
            node_id for node_id, node in flow.get("nodes", {}).items()
            if node.get("type") in ("mcq", "text_only")
        ]

    def count_answerable_nodes(self, flow_id: str) -> int:
        return len(self.get_answerable_node_ids(flow_id))

    def calculate_progress(self, flow_id: str, answered_node_ids: List[str]) -> float:
        answerable = self.get_answerable_node_ids(flow_id)
        if not answerable:
            return 0.0
        completed = len([nid for nid in answered_node_ids if nid in answerable])
        return round((completed / len(answerable)) * 100, 1)

    def format_bot_message(self, node, student_name: str = "your child", node_id: str = None):
        """Format node into chat message dict"""
        content = node.get("content") or node.get("question", "")
        content = content.replace("{student_name}", student_name)

        options = None
        if node["type"] == "mcq":
            options = [
                QuickReplyOption(value=opt["value"], label=opt["label"])
                for opt in node.get("options", [])
            ]

        return {
            "role": "bot",
            "message_type": node["type"],
            "content": content,
            "options": options,
            "allow_text": node.get("allow_text", False),
            "text_prompt": node.get("text_prompt"),
            "metadata": {
                "node_id": node_id,
                "category": node.get("category"),
                "question_id": node_id,
            }
        }


# Global instances
flow_engine = FlowEngine()
orchestrator = OrchestratorAgent()


# ============================================================================
# HELPER: Build response metadata
# ============================================================================

def _build_bot_metadata(bot_response_data: dict) -> dict:
    """Extract frontend-relevant metadata from bot response data."""
    meta = {}
    if bot_response_data.get("options"):
        options = bot_response_data["options"]
        meta["options"] = [
            {"value": o.value, "label": o.label} if hasattr(o, 'value') else o
            for o in options
        ]
    if bot_response_data.get("allow_text"):
        meta["allow_text"] = bot_response_data["allow_text"]
    if bot_response_data.get("text_prompt"):
        meta["text_prompt"] = bot_response_data["text_prompt"]
    return meta



# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/start")
async def start_chat_session(
    request: StartChatRequest,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new hybrid chat session for an assignment, or resume an existing active one."""
    # Verify assignment
    result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.id == request.assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.assigned_to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check for completed session — block re-taking
    completed_result = await db.execute(
        select(ChatSession).where(
            ChatSession.assignment_id == assignment.id,
            ChatSession.status == ChatSessionStatus.COMPLETED.value,
        )
    )
    completed_session = completed_result.scalar_one_or_none()

    if completed_session:
        raise HTTPException(
            status_code=400,
            detail="This assessment has already been completed. You cannot take it again."
        )

    # Check for existing active session (enables resume / "Continue Assessment")
    existing_session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.assignment_id == assignment.id,
            ChatSession.status.in_([
                ChatSessionStatus.ACTIVE.value,
                ChatSessionStatus.PAUSED.value,
            ])
        )
    )
    existing = existing_session_result.scalar_one_or_none()

    if existing:
        # Return existing session data so the frontend can restore state
        messages_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == existing.id)
            .order_by(ChatMessage.timestamp)
        )
        messages = messages_result.scalars().all()

        answered = existing.context_data.get("answered_node_ids", [])
        progress = flow_engine.calculate_progress(existing.flow_type, answered)

        # Build current_question from flow engine so frontend can restore MCQ options
        current_question = None
        if existing.current_node_id and existing.status != ChatSessionStatus.COMPLETED.value:
            current_node = flow_engine.get_node(existing.flow_type, existing.current_node_id)
            if current_node:
                student_name = existing.context_data.get("user_profile", {}).get("student_name", "your child")
                cq_content = (current_node.get("content") or current_node.get("question", "")).replace("{student_name}", student_name)
                cq_metadata: Dict[str, Any] = {
                    "node_id": existing.current_node_id,
                    "category": current_node.get("category"),
                    "allow_text": current_node.get("allow_text", False),
                    "text_prompt": current_node.get("text_prompt"),
                }
                if current_node.get("type") == "mcq":
                    cq_metadata["options"] = [
                        {"value": opt["value"], "label": opt["label"]}
                        for opt in current_node.get("options", [])
                    ]
                current_question = {
                    "message_type": current_node["type"],
                    "content": cq_content,
                    "metadata": cq_metadata,
                }

        response.status_code = status.HTTP_200_OK
        return {
            "session_id": str(existing.id),
            "status": existing.status,
            "progress_percentage": progress,
            "resumed": True,
            "bot_message": None,
            "current_question": current_question,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "message_type": m.message_type,
                    "content": m.content,
                    "metadata": m.message_metadata,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in messages
            ],
        }

    # Get student info
    result = await db.execute(select(Student).where(Student.id == assignment.student_id))
    student = result.scalar_one_or_none()

    flow_type = "parent_assessment_v1" if current_user.role == UserRole.PARENT else "teacher_assessment_v1"

    # Create new session
    session = ChatSession(
        assignment_id=request.assignment_id,
        user_id=current_user.id,
        user_type=current_user.role.value.lower(),
        flow_type=flow_type,
        current_node_id="welcome",
        current_step=0,
        context_data={
            "user_profile": {
                "student_name": f"{student.first_name} {student.last_name}" if student else "your child",
                "student_age": None
            },
            "assessment_data": {},
            "background_profile": {},
            "conversation_summary": "",
            "explored_areas": [],
            "answered_node_ids": [],
            "messages_count": 0,
            "recent_messages": [],
        }
    )
    db.add(session)
    await db.flush()

    flow = flow_engine.get_flow(flow_type)
    if not flow:
        raise HTTPException(status_code=500, detail="Flow definition not found")

    student_name = session.context_data["user_profile"]["student_name"]
    start_node = flow_engine.get_node(flow_type, flow["start_node"])
    bot_message_data = flow_engine.format_bot_message(start_node, student_name, flow["start_node"])

    # Create welcome message
    bot_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.BOT.value,
        message_type=bot_message_data["message_type"],
        content=bot_message_data["content"],
        message_metadata=bot_message_data.get("metadata", {}),
        generation_source="flow_engine"
    )
    db.add(bot_message)

    # Auto-advance through non-interactive message nodes to first question
    final_node_id, final_node = flow_engine.advance_past_messages(flow_type, flow["start_node"])

    if final_node_id != flow["start_node"] and final_node:
        session.current_node_id = final_node_id
        question_data = flow_engine.format_bot_message(final_node, student_name, final_node_id)
        question_msg = ChatMessage(
            session_id=session.id,
            role=MessageRole.BOT.value,
            message_type=question_data["message_type"],
            content=question_data["content"],
            message_metadata=question_data.get("metadata", {}),
            generation_source="flow_engine"
        )
        db.add(question_msg)
        # Combine welcome + question
        bot_message_data = question_data
        bot_message_data["content"] = bot_message.content + "\n\n" + question_data["content"]

    await db.commit()
    await db.refresh(session)

    response.status_code = status.HTTP_201_CREATED
    return StartChatResponse(
        session_id=str(session.id),
        bot_message=BotMessagePayload(
            message_type=bot_message_data.get("message_type", "text"),
            content=bot_message_data.get("content", ""),
            metadata=_build_bot_metadata(bot_message_data) or None
        ),
        metadata={"student_name": student_name}
    )


@router.post("/sessions/{session_id}/message", response_model=SendMessageResponse)
async def send_message(
    session_id: UUID,
    message_input: ChatMessageInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message (MCQ choice or free text) to the chat session.
    Multi-agent routing:
    - MCQ -> flow engine (instant)
    - Free text -> orchestrator (validator + assessor + empathy in parallel)
    - Quick replies -> flow advance or AI elaboration
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Block messages on completed sessions
    if session.status == ChatSessionStatus.COMPLETED.value or session.completed_at is not None:
        raise HTTPException(status_code=400, detail="This assessment has already been completed. You cannot submit further answers.")

    student_name = session.context_data.get("user_profile", {}).get("student_name", "your child")

    # Store user message
    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER.value,
        message_type=message_input.message_type,
        content=message_input.content,
        message_metadata={
            "question_id": message_input.question_id,
            "selected_option": message_input.resolved_option
        }
    )
    db.add(user_message)

    # Track recent messages for context
    recent = session.context_data.get("recent_messages", [])
    recent.append({"role": "user", "content": message_input.content})
    if len(recent) > 10:
        recent = recent[-10:]
    session.context_data["recent_messages"] = recent
    session.context_data["messages_count"] = session.context_data.get("messages_count", 0) + 1

    # === ROUTING ===
    bot_response_data = None
    input_feedback = None
    is_ai_quick_reply = message_input.resolved_option in ("continue", "more")

    try:
        if message_input.message_type == "mcq_choice" and not is_ai_quick_reply:
            # --- MCQ FLOW: real option selected ---
            bot_response_data = await _handle_mcq_choice(session, message_input, student_name)

        elif message_input.message_type == "mcq_choice" and message_input.resolved_option == "continue":
            # --- "Continue assessment" quick-reply ---
            bot_response_data = await _handle_continue(session, student_name)

        elif message_input.message_type == "mcq_choice" and message_input.resolved_option == "more":
            # --- "Tell me more" quick-reply ---
            bot_response_data = await _handle_more(session, student_name)

        elif message_input.message_type == "free_text":
            # --- FREE TEXT: multi-agent processing ---
            bot_response_data, input_feedback = await _handle_free_text(
                session, message_input, user_message, student_name
            )

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # NEVER show errors to user - always provide a graceful response
        bot_response_data = _graceful_fallback(session, student_name)

    # Final fallback - should never happen but just in case
    if not bot_response_data:
        bot_response_data = _graceful_fallback(session, student_name)

    # Create bot message in DB
    bot_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.BOT.value,
        message_type=bot_response_data["message_type"],
        content=bot_response_data["content"],
        message_metadata=bot_response_data.get("metadata", {}),
        generation_source=bot_response_data.get("generation_source", "unknown")
    )
    db.add(bot_message)

    # Track bot message in recent
    recent.append({"role": "bot", "content": bot_response_data["content"]})
    if len(recent) > 10:
        recent = recent[-10:]
    session.context_data["recent_messages"] = recent

    session.last_interaction_at = datetime.utcnow()
    await db.commit()
    await db.refresh(bot_message)

    # Calculate progress
    answered_nodes = session.context_data.get("answered_node_ids", [])
    progress = flow_engine.calculate_progress(session.flow_type, answered_nodes)

    # Current category
    current_category = None
    if session.current_node_id:
        current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
        if current_node:
            current_category = current_node.get("category")

    # Check completion
    is_complete = bot_response_data.get("message_type") == "completion"
    session_status = "completed" if is_complete else "in_progress"

    if is_complete:
        session.status = ChatSessionStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()
        await db.commit()

    return SendMessageResponse(
        bot_message=BotMessagePayload(
            message_type=bot_message.message_type,
            content=bot_message.content,
            metadata=_build_bot_metadata(bot_response_data) or None
        ),
        progress_percentage=progress,
        status=session_status,
        is_complete=is_complete,
        current_category=current_category,
        input_feedback=input_feedback,
    )


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def _handle_mcq_choice(session: ChatSession, message_input: ChatMessageInput, student_name: str) -> dict:
    """Handle real MCQ option selection - generate AI acknowledgment + advance flow."""
    # Mark current node as answered
    answered_nodes = session.context_data.get("answered_node_ids", [])
    current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
    current_category = current_node.get("category", "general") if current_node else "general"

    if current_node and current_node.get("type") in ("mcq", "text_only"):
        if session.current_node_id not in answered_nodes:
            answered_nodes.append(session.current_node_id)
            session.context_data["answered_node_ids"] = answered_nodes

    # Store MCQ answer in assessment data
    if current_node:
        _store_mcq_answer(session, current_category, session.current_node_id, message_input.resolved_option)

    # Get the selected option label for AI context
    user_choice_label = message_input.content
    if current_node:
        for opt in current_node.get("options", []):
            if opt["value"] == message_input.resolved_option:
                user_choice_label = opt.get("label", message_input.content)
                break

    # Get next node
    next_node_id = flow_engine.get_next_node_id(
        session.flow_type, session.current_node_id, message_input.resolved_option
    )
    if not next_node_id and current_node:
        next_node_id = current_node.get("next")

    if next_node_id:
        # Auto-advance past message nodes to next interactive node
        final_id, final_node = flow_engine.advance_past_messages(session.flow_type, next_node_id)
        session.current_node_id = final_id
        session.current_step += 1

        if final_node:
            next_category = final_node.get("category", "general")

            # Only show acknowledgment every 5th answer to reduce chattiness
            answer_count = len(session.context_data.get("answered_node_ids", []))
            show_feedback = answer_count > 0 and answer_count % 5 == 0

            msg_data = flow_engine.format_bot_message(final_node, student_name, final_id)

            if show_feedback:
                context_summary = orchestrator._summarize_context(session.context_data)
                next_q_text = final_node.get("question", "")
                try:
                    ai_transition = await orchestrator.generate_transition(
                        user_choice=user_choice_label,
                        current_category=current_category,
                        next_category=next_category,
                        student_name=student_name,
                        context_summary=context_summary,
                        next_question=next_q_text,
                    )
                except Exception as e:
                    logger.warning(f"AI transition failed, skipping ack: {e}")
                    ai_transition = ""

                if ai_transition:
                    msg_data["content"] = ai_transition + "\n\n" + msg_data["content"]
                    msg_data["generation_source"] = "ai_transition"
                else:
                    msg_data["generation_source"] = "flow_engine"
            else:
                msg_data["generation_source"] = "flow_engine"

            return msg_data

    # Fallback: re-present current question
    if current_node:
        msg_data = flow_engine.format_bot_message(current_node, student_name, session.current_node_id)
        msg_data["generation_source"] = "flow_engine"
        return msg_data

    return _graceful_fallback(session, student_name)


async def _handle_continue(session: ChatSession, student_name: str) -> dict:
    """Handle 'Continue assessment' quick-reply - advance to next flow node."""
    next_node_id = flow_engine.get_next_node_id(
        session.flow_type, session.current_node_id, None
    )

    if next_node_id:
        # Auto-advance past message nodes
        final_id, final_node = flow_engine.advance_past_messages(session.flow_type, next_node_id)
        session.current_node_id = final_id
        session.current_step += 1

        if final_node:
            content_parts = []
            if final_id != next_node_id:
                interim_node = flow_engine.get_node(session.flow_type, next_node_id)
                if interim_node and interim_node.get("type") == "message":
                    interim_content = (interim_node.get("content") or "").replace("{student_name}", student_name)
                    if interim_content:
                        content_parts.append(interim_content)

            msg_data = flow_engine.format_bot_message(final_node, student_name, final_id)
            if content_parts:
                msg_data["content"] = "\n\n".join(content_parts) + "\n\n" + msg_data["content"]
            msg_data["generation_source"] = "flow_engine"
            return msg_data

    # No flow transition - re-present current question
    current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
    if current_node:
        msg_data = flow_engine.format_bot_message(current_node, student_name, session.current_node_id)
        msg_data["generation_source"] = "flow_engine"
        return msg_data

    return _graceful_fallback(session, student_name)


async def _handle_more(session: ChatSession, student_name: str) -> dict:
    """Handle 'Tell me more' quick-reply - AI elaboration."""
    current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
    current_category = current_node.get("category", "general") if current_node else "general"

    response_text = await orchestrator.process_elaboration_request(
        context_data=session.context_data,
        current_category=current_category,
    )

    # After elaboration, auto-advance to next question
    next_node_id = flow_engine.get_next_node_id(session.flow_type, session.current_node_id, None)
    if next_node_id:
        final_id, final_node = flow_engine.advance_past_messages(session.flow_type, next_node_id)
        session.current_node_id = final_id
        if final_node:
            msg_data = flow_engine.format_bot_message(final_node, student_name, final_id)
            msg_data["content"] = response_text + "\n\n" + msg_data["content"]
            msg_data["generation_source"] = "ai_empathetic"
            return msg_data

    return {
        "role": "bot",
        "message_type": "text",
        "content": response_text,
        "allow_text": True,
        "text_prompt": "Type your response...",
        "generation_source": "ai_empathetic",
        "metadata": {"category": current_category}
    }


async def _handle_free_text(
    session: ChatSession,
    message_input: ChatMessageInput,
    user_message: ChatMessage,
    student_name: str,
) -> tuple:
    """
    Handle free text input through multi-agent pipeline.
    Returns (bot_response_data, input_feedback).
    """
    current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
    current_category = current_node.get("category", "general") if current_node else "general"

    # Special handling: age question accepts short numeric answers (e.g. "7", "14", "he is 12")
    if session.current_node_id == "student_age" and current_node:
        import re as _re
        age_match = _re.search(r'\b(\d{1,2})\b', message_input.content)
        if age_match:
            age_val = int(age_match.group(1))
            if 3 <= age_val <= 18:
                # Map typed age to the right MCQ option bucket
                if age_val <= 7:
                    bucket = "5-7"
                elif age_val <= 10:
                    bucket = "8-10"
                elif age_val <= 13:
                    bucket = "11-13"
                else:
                    bucket = "14+"
                # Store age in context
                session.context_data["user_profile"]["student_age"] = str(age_val)
                # Mark as answered
                answered = session.context_data.get("answered_node_ids", [])
                if session.current_node_id not in answered:
                    answered.append(session.current_node_id)
                    session.context_data["answered_node_ids"] = answered
                # Advance to next node (same as MCQ)
                options = current_node.get("options", [])
                next_id = None
                for opt in options:
                    if opt.get("value") == bucket:
                        next_id = opt.get("next")
                        break
                if not next_id and options:
                    next_id = options[0].get("next")
                if next_id:
                    final_id, final_node = flow_engine.advance_past_messages(session.flow_type, next_id)
                    session.current_node_id = final_id
                    if final_node:
                        question_data = flow_engine.format_bot_message(final_node, student_name, final_id)
                        return {
                            "role": "bot",
                            "message_type": question_data["message_type"],
                            "content": f"Got it, {student_name} is {age_val} years old.\n\n{question_data['content']}",
                            "metadata": question_data.get("metadata", {}),
                            "generation_source": "flow_engine",
                        }, None

    # Peek at the next question so empathy agent can create a natural transition
    next_question_text = ""
    if current_node:
        peek_next_id = current_node.get("next")
        if not peek_next_id and current_node.get("type") == "mcq":
            options = current_node.get("options", [])
            if options:
                peek_next_id = options[0].get("next")
        if peek_next_id:
            _, peek_node = flow_engine.advance_past_messages(session.flow_type, peek_next_id)
            if peek_node:
                next_question_text = peek_node.get("question", "")

    # Get the current question text for relevance validation
    current_question_text = ""
    if current_node:
        current_question_text = current_node.get("question", "") or current_node.get("text_prompt", "")

    # Run multi-agent pipeline (validates input first)
    result = await orchestrator.process_free_text(
        user_input=message_input.content,
        context_data=session.context_data,
        current_category=current_category,
        next_question=next_question_text,
        current_question=current_question_text,
    )

    # Handle validation feedback (input too short/vague/gibberish) - do NOT advance
    if result["response_type"] == "validation_feedback":
        return {
            "role": "bot",
            "message_type": "text",
            "content": result["content"],
            "allow_text": True,
            "text_prompt": "Share more details...",
            "generation_source": "ai_validator",
            "metadata": {"validation": True}
        }, result["content"]

    # Mark current node as answered only AFTER validation passes
    answered_nodes = session.context_data.get("answered_node_ids", [])
    if current_node and current_node.get("type") in ("text_only", "mcq"):
        if session.current_node_id not in answered_nodes:
            answered_nodes.append(session.current_node_id)
            session.context_data["answered_node_ids"] = answered_nodes

    # Store classification
    if result.get("classification"):
        user_message.intent_classification = result["classification"]

        # Update assessment data
        classification = result["classification"]
        cat = classification.get("category", current_category)
        _update_assessment_data(session, cat, classification, message_input.content)

    # Background profile generation removed — psychologist generates reports later

    # Auto-advance to next flow question (AI response + next question combined)
    if current_node:
        # For MCQ nodes with text input, use default next or first option's next
        next_node_id = current_node.get("next")
        if not next_node_id and current_node.get("type") == "mcq":
            options = current_node.get("options", [])
            if options:
                next_node_id = options[0].get("next")
        if next_node_id:
            final_id, final_node = flow_engine.advance_past_messages(session.flow_type, next_node_id)
            session.current_node_id = final_id

            if final_node:
                # Only show empathetic acknowledgment every 5th answer
                answer_count = len(session.context_data.get("answered_node_ids", []))
                show_feedback = answer_count > 0 and answer_count % 5 == 0

                msg_data = flow_engine.format_bot_message(final_node, student_name, final_id)
                if show_feedback and result.get("content"):
                    msg_data["content"] = result["content"] + "\n\n" + msg_data["content"]
                    msg_data["generation_source"] = "ai_empathetic"
                else:
                    msg_data["generation_source"] = "flow_engine"
                return msg_data, None

    # No next node (end of flow or standalone text) - just return AI response
    return {
        "role": "bot",
        "message_type": "text",
        "content": result["content"],
        "allow_text": True,
        "text_prompt": "Type your response...",
        "generation_source": "ai_empathetic",
        "metadata": {
            "classification": result.get("classification"),
            "category": current_category,
        }
    }, None


def _store_mcq_answer(session: ChatSession, category: str, node_id: str, value: str):
    """Store MCQ answer in assessment data."""
    assessment = session.context_data.get("assessment_data", {})
    if category not in assessment:
        assessment[category] = {"mcq_answers": {}, "text_inputs": [], "indicators": []}
    elif not isinstance(assessment[category], dict):
        assessment[category] = {"mcq_answers": {}, "text_inputs": [], "severity": assessment[category]}

    assessment[category].setdefault("mcq_answers", {})[node_id] = value

    # Extract severity from the option metadata in the flow
    current_node = flow_engine.get_node(session.flow_type, node_id)
    if current_node:
        for option in current_node.get("options", []):
            if option["value"] == value:
                meta = option.get("metadata", {})
                if "severity" in meta:
                    assessment[category]["severity"] = meta["severity"]
                elif "level" in meta:
                    assessment[category]["severity"] = meta["level"]
                break

    session.context_data["assessment_data"] = assessment

    # Track explored areas
    explored = session.context_data.get("explored_areas", [])
    if category not in explored and category not in ("intro", "background", "transition", "general"):
        explored.append(category)
        session.context_data["explored_areas"] = explored


def _update_assessment_data(session: ChatSession, category: str, classification: dict, text: str):
    """Update assessment data from AI classification."""
    assessment = session.context_data.get("assessment_data", {})
    if category not in assessment:
        assessment[category] = {"mcq_answers": {}, "text_inputs": [], "indicators": []}
    elif not isinstance(assessment[category], dict):
        assessment[category] = {"mcq_answers": {}, "text_inputs": [], "severity": assessment[category]}

    # Update severity (AI classification may override)
    if classification.get("severity"):
        assessment[category]["severity"] = classification["severity"]

    # Add text input — store full answer, no truncation
    if text and len(text) > 3:
        text_inputs = assessment[category].get("text_inputs", [])
        text_inputs.append(text)
        assessment[category]["text_inputs"] = text_inputs

    # Add indicators
    if classification.get("indicators"):
        existing = assessment[category].get("indicators", [])
        new_indicators = list(set(existing + classification["indicators"]))[:10]
        assessment[category]["indicators"] = new_indicators

    session.context_data["assessment_data"] = assessment

    explored = session.context_data.get("explored_areas", [])
    if category not in explored and category not in ("intro", "background", "transition", "general"):
        explored.append(category)
        session.context_data["explored_areas"] = explored


def _graceful_fallback(session: ChatSession, student_name: str) -> dict:
    """
    Never show an error to the user. Always return a meaningful response.
    Re-presents the current question or provides a gentle continuation.
    """
    current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
    if current_node:
        msg_data = flow_engine.format_bot_message(current_node, student_name, session.current_node_id)
        msg_data["content"] = f"Let's continue. {msg_data['content']}"
        msg_data["generation_source"] = "flow_engine"
        return msg_data

    return {
        "role": "bot",
        "message_type": "text",
        "content": f"Thank you for sharing that about {student_name}. Let's continue with the assessment.",
        "allow_text": True,
        "text_prompt": "Type your response...",
        "generation_source": "fallback",
        "metadata": {}
    }


# ============================================================================
# SESSION RESUME
# ============================================================================

@router.get("/sessions/{session_id}", response_model=SessionResumeResponse)
async def get_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat session with full message history for resume."""
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    )
    messages = result.scalars().all()

    message_records = []
    for msg in messages:
        metadata = {}
        if msg.message_metadata:
            metadata.update(msg.message_metadata)
        if msg.intent_classification:
            metadata["intent_classification"] = msg.intent_classification

        message_records.append(
            SessionMessageRecord(
                id=str(msg.id),
                role=msg.role,
                message_type=msg.message_type,
                content=msg.content,
                metadata=metadata,
                timestamp=msg.timestamp
            )
        )

    answered_nodes = session.context_data.get("answered_node_ids", [])
    progress = flow_engine.calculate_progress(session.flow_type, answered_nodes)

    current_question = None
    if session.current_node_id and session.status != ChatSessionStatus.COMPLETED.value:
        current_node = flow_engine.get_node(session.flow_type, session.current_node_id)
        if current_node:
            student_name = session.context_data.get("user_profile", {}).get("student_name", "your child")
            content = (current_node.get("content") or current_node.get("question", "")).replace("{student_name}", student_name)

            q_metadata: Dict[str, Any] = {
                "node_id": session.current_node_id,
                "category": current_node.get("category"),
                "allow_text": current_node.get("allow_text", False),
                "text_prompt": current_node.get("text_prompt"),
            }
            if current_node.get("type") == "mcq":
                q_metadata["options"] = [
                    {"value": opt["value"], "label": opt["label"]}
                    for opt in current_node.get("options", [])
                ]
            current_question = CurrentQuestionMeta(
                message_type=current_node["type"],
                content=content,
                metadata=q_metadata
            )

    return SessionResumeResponse(
        session_id=str(session.id),
        status=session.status,
        progress_percentage=progress,
        current_node_id=session.current_node_id,
        current_question=current_question,
        messages=message_records
    )


# ============================================================================
# VIEW ASSESSMENT DATA (for psychologist / admin)
# ============================================================================

@router.get("/all-sessions")
async def list_all_sessions(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all assessment sessions (completed, in-progress, paused).
    Use ?status_filter=active or ?status_filter=completed to filter.
    Parents see their own; psychologists/admins see all.
    """
    query = select(ChatSession).order_by(ChatSession.last_interaction_at.desc())

    # Optional status filter
    if status_filter:
        query = query.where(ChatSession.status == status_filter)

    # Parents can only see their own
    if current_user.role == UserRole.PARENT:
        query = query.where(ChatSession.user_id == current_user.id)

    result = await db.execute(query)
    sessions = result.scalars().all()

    output = []
    for s in sessions:
        student_name = s.context_data.get("user_profile", {}).get("student_name", "Unknown")
        answered = s.context_data.get("answered_node_ids", [])
        progress = flow_engine.calculate_progress(s.flow_type, answered)

        output.append({
            "session_id": str(s.id),
            "assignment_id": str(s.assignment_id),
            "status": s.status,
            "student_name": student_name,
            "student_age": s.context_data.get("user_profile", {}).get("student_age"),
            "progress_percentage": progress,
            "questions_answered": len(answered),
            "categories_covered": s.context_data.get("explored_areas", []),
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "last_interaction": s.last_interaction_at.isoformat() if s.last_interaction_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "duration_minutes": s.duration_minutes,
        })

    return {"total": len(output), "sessions": output}


@router.get("/sessions/{session_id}/data")
async def get_session_data(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the full stored assessment data for a completed session.
    Returns all Q&A pairs, assessment_data, and completion_summary as JSON.
    Parents see their own; psychologists/admins can see any.
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Access control: parents can only see their own
    if current_user.role == UserRole.PARENT and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get student info
    assignment_result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.id == session.assignment_id)
    )
    assignment = assignment_result.scalar_one_or_none()

    student = None
    if assignment:
        student_result = await db.execute(select(Student).where(Student.id == assignment.student_id))
        student = student_result.scalar_one_or_none()

    # Get all messages
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    )
    all_messages = msg_result.scalars().all()

    # Auto-build Q&A pairs from messages if not already stored (for old sessions)
    qa_pairs = session.context_data.get("completed_qa_pairs", [])
    if not qa_pairs and all_messages:
        bot_question_buffer = None
        for msg in all_messages:
            if msg.role == "bot":
                bot_question_buffer = {
                    "node_id": (msg.message_metadata or {}).get("node_id"),
                    "category": (msg.message_metadata or {}).get("category"),
                    "question": msg.content,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                }
            elif msg.role == "user" and bot_question_buffer:
                qa_pairs.append({
                    "question_node_id": bot_question_buffer.get("node_id"),
                    "category": bot_question_buffer.get("category"),
                    "question_text": bot_question_buffer["question"],
                    "question_type": bot_question_buffer["message_type"],
                    "answer_text": msg.content,
                    "answer_type": msg.message_type,
                    "selected_option": (msg.message_metadata or {}).get("selected_option"),
                    "timestamp": msg.timestamp.isoformat(),
                })
                bot_question_buffer = None
            elif msg.role == "user":
                qa_pairs.append({
                    "question_node_id": None,
                    "category": None,
                    "question_text": None,
                    "question_type": None,
                    "answer_text": msg.content,
                    "answer_type": msg.message_type,
                    "selected_option": (msg.message_metadata or {}).get("selected_option"),
                    "timestamp": msg.timestamp.isoformat(),
                })

        # Save the rebuilt pairs back to the session so next time it's instant
        session.context_data["completed_qa_pairs"] = qa_pairs
        await db.commit()

    return {
        "session_id": str(session.id),
        "status": session.status,
        "student": {
            "name": f"{student.first_name} {student.last_name}" if student else "Unknown",
            "age": session.context_data.get("user_profile", {}).get("student_age"),
            "school": student.school_name if student else None,
            "year_group": student.year_group if student else None,
            "date_of_birth": student.date_of_birth.isoformat() if student and student.date_of_birth else None,
            "gender": student.gender if student else None,
        } if student else None,
        "timing": {
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "duration_minutes": session.duration_minutes,
        },
        "qa_pairs": qa_pairs,
        "assessment_data": session.context_data.get("assessment_data", {}),
        "completion_summary": session.context_data.get("completion_summary", {}),
        "full_conversation": [
            {
                "role": msg.role,
                "type": msg.message_type,
                "content": msg.content,
                "metadata": msg.message_metadata,
                "classification": msg.intent_classification,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in all_messages
        ],
        "total_messages": len(all_messages),
    }


# ============================================================================
# SESSION RESET ("Start Over")
# ============================================================================

@router.post("/sessions/{session_id}/reset")
async def reset_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset a session so the user can start over from scratch.
    Deletes all messages, resets context_data and current_node_id,
    then returns a fresh welcome response identical to /start.
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == ChatSessionStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot reset a completed session")

    # Delete all existing messages for this session
    await db.execute(
        sa_delete(ChatMessage).where(ChatMessage.session_id == session.id)
    )

    # Reset session state
    student_name = session.context_data.get("user_profile", {}).get("student_name", "your child")
    session.current_node_id = "welcome"
    session.current_step = 0
    session.status = ChatSessionStatus.ACTIVE.value
    session.completed_at = None
    session.context_data = {
        "user_profile": session.context_data.get("user_profile", {"student_name": student_name}),
        "assessment_data": {},
        "background_profile": {},
        "conversation_summary": "",
        "explored_areas": [],
        "answered_node_ids": [],
        "messages_count": 0,
        "recent_messages": [],
    }

    # Re-create welcome message (same logic as /start)
    flow = flow_engine.get_flow(session.flow_type)
    if not flow:
        raise HTTPException(status_code=500, detail="Flow definition not found")

    start_node = flow_engine.get_node(session.flow_type, flow["start_node"])
    bot_message_data = flow_engine.format_bot_message(start_node, student_name, flow["start_node"])

    bot_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.BOT.value,
        message_type=bot_message_data["message_type"],
        content=bot_message_data["content"],
        message_metadata=bot_message_data.get("metadata", {}),
        generation_source="flow_engine",
    )
    db.add(bot_message)

    # Auto-advance through non-interactive message nodes to first question
    final_node_id, final_node = flow_engine.advance_past_messages(session.flow_type, flow["start_node"])

    if final_node_id != flow["start_node"] and final_node:
        session.current_node_id = final_node_id
        question_data = flow_engine.format_bot_message(final_node, student_name, final_node_id)
        question_msg = ChatMessage(
            session_id=session.id,
            role=MessageRole.BOT.value,
            message_type=question_data["message_type"],
            content=question_data["content"],
            message_metadata=question_data.get("metadata", {}),
            generation_source="flow_engine",
        )
        db.add(question_msg)
        bot_message_data = question_data
        bot_message_data["content"] = bot_message.content + "\n\n" + question_data["content"]

    await db.commit()
    await db.refresh(session)

    return StartChatResponse(
        session_id=str(session.id),
        bot_message=BotMessagePayload(
            message_type=bot_message_data.get("message_type", "text"),
            content=bot_message_data.get("content", ""),
            metadata=_build_bot_metadata(bot_message_data) or None,
        ),
        metadata={"student_name": student_name, "reset": True},
    )


# ============================================================================
# SESSION COMPLETION + BACKGROUND GENERATION
# ============================================================================

@router.post("/sessions/{session_id}/complete")
async def complete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark session as complete and store all parent inputs as structured JSON.
    The psychologist can generate background reports later from this data.
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Idempotent finalization: the automatic completion path in the message handler
    # may already have marked the chat session as COMPLETED. We still need to update
    # the assignment status and store the QA summary, so don't reject here.
    already_finalized = (
        session.status == ChatSessionStatus.COMPLETED.value
        and session.context_data
        and "completed_qa_pairs" in session.context_data
    )
    if already_finalized:
        return {
            "message": "Chat session already finalized",
            "session_id": str(session.id),
            "duration_minutes": session.duration_minutes,
            "total_questions_answered": len(session.context_data.get("completed_qa_pairs", [])),
            "categories_covered": list(session.context_data.get("explored_areas", [])),
        }

    if session.status != ChatSessionStatus.COMPLETED.value:
        session.status = ChatSessionStatus.COMPLETED.value
    if not session.completed_at:
        session.completed_at = datetime.utcnow()
    if not session.duration_minutes:
        duration = (session.completed_at - session.started_at).total_seconds() / 60
        session.duration_minutes = int(duration)

    # Update assignment status
    result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.id == session.assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if assignment:
        assignment.status = AssignmentStatus.COMPLETED
        assignment.completed_at = datetime.utcnow()

    # Get student info
    result = await db.execute(
        select(Student).where(Student.id == assignment.student_id) if assignment else select(Student).where(False)
    )
    student = result.scalar_one_or_none() if assignment else None

    # ── Store all raw data as JSON (no AI generation) ──────────────────────
    # Gather every message from the session
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    )
    all_messages = result.scalars().all()

    # Build a clean JSON summary: every question asked + every answer given
    qa_pairs = []
    bot_question_buffer = None  # track the last bot question

    for msg in all_messages:
        if msg.role == "bot":
            # Store the question text + metadata for pairing
            bot_question_buffer = {
                "node_id": (msg.message_metadata or {}).get("node_id"),
                "category": (msg.message_metadata or {}).get("category"),
                "question": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
            }
        elif msg.role == "user" and bot_question_buffer:
            # Pair this user answer with the preceding bot question
            qa_pairs.append({
                "question_node_id": bot_question_buffer.get("node_id"),
                "category": bot_question_buffer.get("category"),
                "question_text": bot_question_buffer["question"],
                "question_type": bot_question_buffer["message_type"],
                "answer_text": msg.content,
                "answer_type": msg.message_type,
                "selected_option": (msg.message_metadata or {}).get("selected_option"),
                "timestamp": msg.timestamp.isoformat(),
            })
            bot_question_buffer = None
        elif msg.role == "user":
            # User message without a preceding question (shouldn't happen, but store it)
            qa_pairs.append({
                "question_node_id": None,
                "category": None,
                "question_text": None,
                "question_type": None,
                "answer_text": msg.content,
                "answer_type": msg.message_type,
                "selected_option": (msg.message_metadata or {}).get("selected_option"),
                "timestamp": msg.timestamp.isoformat(),
            })

    # Store the clean Q&A summary + full assessment data in the session
    session.context_data["completed_qa_pairs"] = qa_pairs
    session.context_data["completion_summary"] = {
        "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
        "student_age": session.context_data.get("user_profile", {}).get("student_age"),
        "school": student.school_name if student else None,
        "year_group": student.year_group if student else None,
        "total_questions": len(qa_pairs),
        "categories_covered": list(session.context_data.get("explored_areas", [])),
        "assessment_data": session.context_data.get("assessment_data", {}),
        "duration_minutes": session.duration_minutes,
        "completed_at": session.completed_at.isoformat(),
    }

    await db.commit()

    logger.info(f"Session {session_id} completed with {len(qa_pairs)} Q&A pairs stored as JSON")

    return {
        "message": "Chat session completed successfully",
        "session_id": str(session.id),
        "duration_minutes": session.duration_minutes,
        "total_questions_answered": len(qa_pairs),
        "categories_covered": list(session.context_data.get("explored_areas", [])),
    }


async def _run_report_generation_job(job_id: UUID, job_type: str, chatbot_data: dict):
    """Background task for report generation. Handles Ollama being down gracefully."""
    from app.core.database import AsyncSessionLocal
    from app.services.local_llm import llm_service

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AIGenerationJob).where(AIGenerationJob.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                logger.error(f"Report generation job {job_id} not found")
                return

            job.status = 'running'
            await db.commit()

            start_time = datetime.utcnow()
            try:
                if job_type == 'profile':
                    llm_result = llm_service.generate_profile_section(chatbot_data)
                elif job_type == 'impact':
                    llm_result = llm_service.generate_impact_section(chatbot_data)
                elif job_type == 'recommendations':
                    llm_result = llm_service.generate_recommendations_section(chatbot_data)
                else:
                    raise ValueError(f"Unknown job type: {job_type}")
            except Exception as llm_err:
                logger.error(f"LLM call failed for job {job_id} ({job_type}): {llm_err}")
                job.status = 'failed'
                job.error_message = f"LLM service error: {str(llm_err)}"
                job.completed_at = datetime.utcnow()
                await db.commit()
                return

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            if llm_result.get("success"):
                job.status = 'completed'
                job.output_text = llm_result.get("text", "")
                job.model_used = llm_result.get("model", settings.OLLAMA_MODEL)
                job.tokens_used = llm_result.get("tokens", 0)
                job.generation_time_seconds = duration
                job.completed_at = end_time
            else:
                job.status = 'failed'
                job.error_message = llm_result.get("error", "LLM returned unsuccessful result")
                job.completed_at = end_time

            await db.commit()
            logger.info(f"Report job {job_id} ({job_type}) finished: {job.status}")

    except Exception as e:
        logger.error(f"Unexpected error in report job {job_id}: {e}", exc_info=True)
        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(AIGenerationJob).where(AIGenerationJob.id == job_id))
                job = result.scalar_one_or_none()
                if job and job.status != 'failed':
                    job.status = 'failed'
                    job.error_message = f"Unexpected error: {str(e)}"
                    job.completed_at = datetime.utcnow()
                    await db.commit()
        except Exception:
            logger.error(f"Failed to mark job {job_id} as failed")
