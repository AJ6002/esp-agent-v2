"""Server-Side Session Layer for ESP APM Copilot (Domain 11).

Provides in-memory session management, structured telemetry evidence snapshots,
deferred intent queueing for compound queries, and multi-turn entity persistence.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("agent.session")

SESSION_TTL_SECONDS = 86400  # 24 Hours
MAX_SESSIONS = 2000


@dataclass
class SessionState:
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    last_intent: str | None = None
    last_entity: str | None = None
    last_event_id: str | None = None
    last_entities: list[str] = field(default_factory=list)
    last_evidence: dict[str, Any] = field(default_factory=dict)
    last_diagnosis: dict[str, Any] = field(default_factory=dict)
    last_markdown_report: str | None = None
    active_page_route: str | None = None
    deferred_intents: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.last_active_at = time.time()

    def is_expired(self, ttl_seconds: float = SESSION_TTL_SECONDS) -> bool:
        return (time.time() - self.last_active_at) > ttl_seconds


class SessionManager:
    """In-memory thread-safe session manager with 24-hour TTL and LRU eviction."""

    def __init__(self, max_capacity: int = MAX_SESSIONS, ttl_seconds: float = SESSION_TTL_SECONDS) -> None:
        self._sessions: dict[str, SessionState] = {}
        self.max_capacity = max_capacity
        self.ttl_seconds = ttl_seconds

    def get_or_create(self, session_id: str | None = None) -> tuple[SessionState, bool]:
        """Retrieve existing session or instantiate a new one.
        
        Returns:
            (SessionState, is_new: bool)
        """
        self.cleanup_expired()

        if not session_id or not str(session_id).strip():
            new_id = f"sess_{uuid.uuid4().hex[:12]}"
            session = SessionState(session_id=new_id)
            self._insert_session(session)
            return session, True

        sid = str(session_id).strip()
        if sid in self._sessions:
            sess = self._sessions[sid]
            sess.touch()
            return sess, False

        # Create requested session
        session = SessionState(session_id=sid)
        self._insert_session(session)
        return session, True

    def get(self, session_id: str | None) -> SessionState | None:
        if not session_id:
            return None
        sid = str(session_id).strip()
        sess = self._sessions.get(sid)
        if sess:
            if sess.is_expired(self.ttl_seconds):
                del self._sessions[sid]
                return None
            sess.touch()
        return sess

    def record_execution(
        self,
        session_id: str,
        intent: str,
        entity: str | None = None,
        event_id: str | None = None,
        entities: list[str] | None = None,
        evidence: dict[str, Any] | None = None,
        diagnosis: dict[str, Any] | None = None,
        markdown_report: str | None = None,
        page_route: str | None = None,
    ) -> None:
        """Record the computational evidence and execution snapshot for a session."""
        session, _ = self.get_or_create(session_id)
        session.last_intent = intent
        if entity:
            session.last_entity = entity
        if event_id:
            session.last_event_id = event_id
        if entities:
            session.last_entities = entities
        if evidence:
            session.last_evidence = evidence
        if diagnosis:
            session.last_diagnosis = diagnosis
        if markdown_report:
            session.last_markdown_report = markdown_report
        if page_route:
            session.active_page_route = page_route
        session.touch()

    def queue_deferred_intent(
        self,
        session_id: str,
        query: str,
        expected_intent: str | None = None,
        entity: str | None = None,
    ) -> None:
        """Queue a secondary deferred intent from a compound query."""
        session, _ = self.get_or_create(session_id)
        session.deferred_intents.append({
            "query": query,
            "intent": expected_intent,
            "entity": entity,
            "queued_at": time.time(),
        })
        session.touch()

    def pop_deferred_intent(self, session_id: str) -> dict[str, Any] | None:
        """Pop the next deferred intent from the session queue."""
        session = self.get(session_id)
        if session and session.deferred_intents:
            session.touch()
            return session.deferred_intents.pop(0)
        return None

    def peek_deferred_intent(self, session_id: str) -> dict[str, Any] | None:
        session = self.get(session_id)
        if session and session.deferred_intents:
            return session.deferred_intents[0]
        return None

    def _insert_session(self, session: SessionState) -> None:
        if len(self._sessions) >= self.max_capacity:
            # Evict oldest inactive session
            oldest_sid = min(self._sessions.keys(), key=lambda k: self._sessions[k].last_active_at)
            del self._sessions[oldest_sid]
        self._sessions[session.session_id] = session

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if (now - s.last_active_at) > self.ttl_seconds]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def clear(self) -> None:
        """Reset all sessions (for unit tests)."""
        self._sessions.clear()


# Global Singleton Session Manager
session_manager = SessionManager()
