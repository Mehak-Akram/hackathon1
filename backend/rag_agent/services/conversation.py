"""
Conversation service for managing session state and conversation history
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID

from ..api.models.request import ConversationSession
from ..api.models.response import ChatResponse
from ..utils.logger import get_logger
from ..utils.helpers import is_valid_uuid
from ..config.settings import settings


logger = get_logger(__name__)


class ConversationService:
    """
    Service for managing conversation sessions and history
    """
    def __init__(self):
        # In-memory storage for active sessions (in production, use Redis or database)
        self.sessions: Dict[str, ConversationSession] = {}
        self.cleanup_task = None

    async def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> ConversationSession:
        """
        Create a new conversation session
        """
        session_id = str(UUID(int=0)) if user_id is None else str(UUID(int=int(time.time() * 1000000)))
        # Generate a proper UUID
        import uuid
        session_id = str(uuid.uuid4())

        session = ConversationSession(
            id=session_id,
            user_id=user_id,
            metadata=metadata or {},
            conversation_history=[]
        )

        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")

        return session

    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get an existing conversation session
        """
        if not is_valid_uuid(session_id):
            logger.warning(f"Invalid session ID format: {session_id}")
            return None

        session = self.sessions.get(session_id)
        if session:
            # Update last activity time
            session.last_activity = datetime.now().isoformat()
        return session

    async def update_session(self, session_id: str, new_data: Dict[str, Any]) -> bool:
        """
        Update an existing conversation session
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        # Update allowed fields
        if 'metadata' in new_data:
            session.metadata.update(new_data['metadata'])
        if 'conversation_history' in new_data:
            session.conversation_history = new_data['conversation_history']
        if 'active' in new_data:
            session.active = new_data['active']

        # Update last activity
        session.last_activity = datetime.now().isoformat()
        return True

    async def add_conversation_turn(self, session_id: str, question: str, response: str) -> bool:
        """
        Add a question-response pair to the conversation history
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        turn = {
            "question": question,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

        session.conversation_history.append(turn)

        # Limit history to prevent memory issues
        if len(session.conversation_history) > 50:  # As per model validation
            session.conversation_history = session.conversation_history[-50:]

        logger.debug(f"Added conversation turn to session {session_id}, history now has {len(session.conversation_history)} items")
        return True

    async def get_conversation_context(self, session_id: str, max_turns: int = 5) -> List[Dict[str, str]]:
        """
        Get the recent conversation context for follow-up questions
        """
        session = await self.get_session(session_id)
        if not session:
            return []

        # Get the most recent turns
        recent_turns = session.conversation_history[-max_turns:]
        context = []

        for turn in recent_turns:
            context.append({
                "question": turn.get("question", ""),
                "response": turn.get("response", ""),
                "timestamp": turn.get("timestamp", "")
            })

        return context

    async def end_session(self, session_id: str) -> bool:
        """
        End and remove a conversation session
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Ended session: {session_id}")
            return True
        return False

    async def cleanup_expired_sessions(self):
        """
        Remove sessions that have exceeded the timeout
        """
        current_time = datetime.now()
        expired_session_ids = []

        for session_id, session in self.sessions.items():
            try:
                last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
                time_since_activity = current_time - last_activity

                if time_since_activity > timedelta(minutes=settings.session_timeout_minutes):
                    expired_session_ids.append(session_id)
            except ValueError:
                # If we can't parse the timestamp, remove the session
                expired_session_ids.append(session_id)

        for session_id in expired_session_ids:
            await self.end_session(session_id)
            logger.info(f"Cleaned up expired session: {session_id}")

    async def get_all_active_sessions(self) -> List[ConversationSession]:
        """
        Get all currently active sessions
        """
        active_sessions = []
        current_time = datetime.now()

        for session in self.sessions.values():
            try:
                last_activity = datetime.fromisoformat(session.last_activity.replace('Z', '+00:00'))
                time_since_activity = current_time - last_activity

                if time_since_activity <= timedelta(minutes=settings.session_timeout_minutes):
                    active_sessions.append(session)
            except ValueError:
                # If timestamp is invalid, consider the session as active for now
                # but it will be cleaned up in the next cleanup cycle
                active_sessions.append(session)

        return active_sessions

    async def validate_conversation_history(self, session_id: str) -> Dict[str, Any]:
        """
        Validate that conversation history is properly maintained for a session
        """
        session = await self.get_session(session_id)
        if not session:
            return {
                "valid": False,
                "error": "Session not found",
                "details": {}
            }

        validation_result = {
            "valid": True,
            "session_id": session_id,
            "history_count": len(session.conversation_history),
            "history_limit_respected": len(session.conversation_history) <= 50,  # As per model validation
            "timestamps_valid": True,
            "details": {
                "max_history_allowed": 50,
                "current_history_count": len(session.conversation_history)
            }
        }

        # Check timestamps in conversation history
        for turn in session.conversation_history:
            timestamp_str = turn.get("timestamp")
            if timestamp_str:
                try:
                    datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    validation_result["timestamps_valid"] = False
                    validation_result["valid"] = False

        return validation_result


# Global instance of the conversation service
conversation_service = ConversationService()