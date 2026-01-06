"""Conversation service for chat interactions with notebooks."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..api_client import NotebookLMClient


class ChatMode(Enum):
    """Predefined chat modes for common use cases."""

    DEFAULT = "default"  # General purpose
    LEARNING_GUIDE = "learning_guide"  # Educational focus
    CONCISE = "concise"  # Brief responses
    DETAILED = "detailed"  # Verbose responses


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""

    query: str
    answer: str
    turn_number: int


@dataclass
class AskResult:
    """Result of asking the notebook a question."""

    answer: str
    conversation_id: str
    turn_number: int
    is_follow_up: bool
    raw_response: str = ""


class ConversationService:
    """Service for conversational interactions with notebooks."""

    def __init__(self, client: "NotebookLMClient"):
        self._client = client

    async def configure(
        self,
        notebook_id: str,
        goal: Optional["ChatGoal"] = None,
        response_length: Optional["ChatResponseLength"] = None,
        custom_prompt: Optional[str] = None,
    ) -> None:
        """Configure chat persona and response settings.

        Args:
            notebook_id: The notebook to configure.
            goal: Chat persona (DEFAULT, CUSTOM, LEARNING_GUIDE).
            response_length: Response verbosity (DEFAULT, LONGER, SHORTER).
            custom_prompt: Custom instructions (required if goal is CUSTOM).

        Example:
            from notebooklm.rpc import ChatGoal, ChatResponseLength

            await conversation.configure(
                notebook_id,
                goal=ChatGoal.LEARNING_GUIDE,
                response_length=ChatResponseLength.LONGER,
            )
        """
        await self._client.configure_chat(
            notebook_id, goal, response_length, custom_prompt
        )

    async def set_mode(self, notebook_id: str, mode: ChatMode) -> None:
        """Set chat mode using predefined configurations.

        Args:
            notebook_id: The notebook to configure.
            mode: Predefined chat mode.

        Example:
            await conversation.set_mode(notebook_id, ChatMode.LEARNING_GUIDE)
        """
        from ..rpc import ChatGoal, ChatResponseLength

        mode_configs = {
            ChatMode.DEFAULT: (ChatGoal.DEFAULT, ChatResponseLength.DEFAULT, None),
            ChatMode.LEARNING_GUIDE: (ChatGoal.LEARNING_GUIDE, ChatResponseLength.LONGER, None),
            ChatMode.CONCISE: (ChatGoal.DEFAULT, ChatResponseLength.SHORTER, None),
            ChatMode.DETAILED: (ChatGoal.DEFAULT, ChatResponseLength.LONGER, None),
        }

        goal, length, prompt = mode_configs[mode]
        await self._client.configure_chat(notebook_id, goal, length, prompt)

    async def ask(
        self,
        notebook_id: str,
        question: str,
        source_ids: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
    ) -> AskResult:
        """Ask the notebook a question.

        Args:
            notebook_id: The notebook to query
            question: The question to ask
            source_ids: Limit to specific sources (None = all sources)
            conversation_id: Continue existing conversation (None = new)

        Returns:
            AskResult with answer and conversation metadata
        """
        result = await self._client.ask(
            notebook_id, question, source_ids, conversation_id
        )
        return AskResult(
            answer=result["answer"],
            conversation_id=result["conversation_id"],
            turn_number=result["turn_number"],
            is_follow_up=result["is_follow_up"],
            raw_response=result.get("raw_response", ""),
        )

    async def get_history(self, notebook_id: str, limit: int = 20) -> Any:
        """Get conversation history from server.

        Args:
            notebook_id: The notebook to get history for
            limit: Maximum number of turns to retrieve

        Returns:
            List of conversation IDs (not full content)
        """
        return await self._client.get_conversation_history(notebook_id, limit)

    def get_cached_turns(self, conversation_id: str) -> List[ConversationTurn]:
        """Get locally cached conversation turns.

        Args:
            conversation_id: The conversation to retrieve

        Returns:
            List of ConversationTurn from the client's local cache (this session only)
        """
        turns_data = self._client._conversation_cache.get(conversation_id, [])
        return [
            ConversationTurn(
                query=turn["query"],
                answer=turn["answer"],
                turn_number=turn["turn_number"],
            )
            for turn in turns_data
        ]

    def clear_cache(self, conversation_id: Optional[str] = None) -> bool:
        """Clear local conversation cache.

        Args:
            conversation_id: Clear specific conversation (None = clear all)

        Returns:
            True if cleared successfully
        """
        if conversation_id:
            if conversation_id in self._client._conversation_cache:
                del self._client._conversation_cache[conversation_id]
                return True
            return False
        else:
            self._client._conversation_cache.clear()
            return True

    async def delete_history(self, notebook_id: str) -> bool:
        """Delete conversation history from server.

        Args:
            notebook_id: The notebook whose history to delete

        Returns:
            True if deleted successfully

        Raises:
            NotImplementedError: Server-side deletion RPC not yet discovered
        """
        raise NotImplementedError("Server-side history deletion not yet implemented")
