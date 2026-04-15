"""
Client-side error sink.

Frontend error boundaries and the shared logger helper POST unhandled
browser errors here so they land in backend/logs/errors.log alongside
server-side tracebacks.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(prefix="/client-errors", tags=["client-errors"])
logger = logging.getLogger("client-error")


class ClientErrorPayload(BaseModel):
    message: str = Field(..., max_length=2000)
    stack: Optional[str] = Field(None, max_length=8000)
    component_stack: Optional[str] = Field(None, max_length=8000, alias="componentStack")
    url: Optional[str] = Field(None, max_length=500)
    user_agent: Optional[str] = Field(None, max_length=500, alias="userAgent")
    user_id: Optional[str] = Field(None, max_length=100, alias="userId")
    context: Optional[dict] = None

    class Config:
        populate_by_name = True


# Simple in-memory rate limit: max 30 reports per IP per 60s window.
_RATE_WINDOW_SECS = 60
_RATE_MAX = 30
_ip_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(ip: str) -> bool:
    now = time.time()
    hits = _ip_hits[ip]
    while hits and now - hits[0] > _RATE_WINDOW_SECS:
        hits.popleft()
    if len(hits) >= _RATE_MAX:
        return True
    hits.append(now)
    return False


@router.post("")
@router.post("/")
async def report_client_error(payload: ClientErrorPayload, request: Request):
    ip = request.client.host if request.client else "-"
    if _rate_limited(ip):
        # Accept quietly; we never want logging to cause errors on the client.
        return {"accepted": False, "reason": "rate_limited"}

    extras = {
        "url": payload.url,
        "stack": payload.stack,
        "componentStack": payload.component_stack,
        "userAgent": payload.user_agent,
        "userId": payload.user_id,
        "context": payload.context,
        "ip": ip,
    }
    # Drop empty fields so the log line stays compact.
    extras = {k: v for k, v in extras.items() if v}
    logger.error("client-error | %s | %s", payload.message, json.dumps(extras, default=str))
    return {"accepted": True}
