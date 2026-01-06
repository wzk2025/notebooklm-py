"""Domain services for NotebookLM operations."""

from .notebooks import NotebookService, Notebook, NotebookDescription, SuggestedTopic
from .sources import SourceService, Source
from .artifacts import ArtifactService, Artifact, ArtifactStatus, ReportSuggestion
from .conversation import ConversationService, AskResult, ConversationTurn, ChatMode

__all__ = [
    # Notebook
    "NotebookService",
    "Notebook",
    "NotebookDescription",
    "SuggestedTopic",
    # Source
    "SourceService",
    "Source",
    # Artifact
    "ArtifactService",
    "Artifact",
    "ArtifactStatus",
    "ReportSuggestion",
    # Conversation
    "ConversationService",
    "AskResult",
    "ConversationTurn",
    "ChatMode",
]
