"""Core infrastructure for NotebookLM API client."""

import httpx
from typing import Any, Optional
from urllib.parse import urlencode

from .auth import AuthTokens
from .rpc import (
    RPCMethod,
    BATCHEXECUTE_URL,
    encode_rpc_request,
    build_request_body,
    decode_response,
)


class ClientCore:
    """Core client infrastructure for HTTP and RPC operations.

    Handles:
    - HTTP client lifecycle (open/close)
    - RPC call encoding/decoding
    - Authentication headers
    - Conversation cache

    This class is used internally by the sub-client APIs (NotebooksAPI,
    ArtifactsAPI, etc.) and should not be used directly.
    """

    def __init__(self, auth: AuthTokens):
        """Initialize the core client.

        Args:
            auth: Authentication tokens from browser login.
        """
        self.auth = auth
        self._http_client: Optional[httpx.AsyncClient] = None
        self._conversation_cache: dict[str, list[dict[str, Any]]] = {}

    async def open(self) -> None:
        """Open the HTTP client connection.

        Called automatically by NotebookLMClient.__aenter__.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                headers={
                    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                    "Cookie": self.auth.cookie_header,
                },
                timeout=30.0,
            )

    async def close(self) -> None:
        """Close the HTTP client connection.

        Called automatically by NotebookLMClient.__aexit__.
        """
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    @property
    def is_open(self) -> bool:
        """Check if the HTTP client is open."""
        return self._http_client is not None

    def update_auth_headers(self) -> None:
        """Update HTTP client headers with current auth tokens.

        Call this after modifying auth tokens (e.g., after refresh_auth())
        to ensure the HTTP client uses the updated credentials.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if not self._http_client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        self._http_client.headers["Cookie"] = self.auth.cookie_header

    def _build_url(self, rpc_method: RPCMethod, source_path: str = "/") -> str:
        """Build the batchexecute URL for an RPC call.

        Args:
            rpc_method: The RPC method to call.
            source_path: The source path parameter (usually notebook path).

        Returns:
            Full URL with query parameters.
        """
        params = {
            "rpcids": rpc_method.value,
            "source-path": source_path,
            "f.sid": self.auth.session_id,
            "rt": "c",
        }
        return f"{BATCHEXECUTE_URL}?{urlencode(params)}"

    async def rpc_call(
        self,
        method: RPCMethod,
        params: list[Any],
        source_path: str = "/",
        allow_null: bool = False,
    ) -> Any:
        """Make an RPC call to the NotebookLM API.

        Args:
            method: The RPC method to call.
            params: Parameters for the RPC call (nested list structure).
            source_path: The source path parameter (usually /notebook/{id}).
            allow_null: If True, don't raise error when response is null.

        Returns:
            Decoded response data.

        Raises:
            RuntimeError: If client is not initialized (not in context manager).
            httpx.HTTPStatusError: If HTTP request fails.
            RPCError: If RPC call fails or returns unexpected data.
        """
        if not self._http_client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")

        url = self._build_url(method, source_path)
        rpc_request = encode_rpc_request(method, params)
        body = build_request_body(rpc_request, self.auth.csrf_token)

        response = await self._http_client.post(url, content=body)
        response.raise_for_status()

        return decode_response(response.text, method.value, allow_null=allow_null)

    def get_http_client(self) -> httpx.AsyncClient:
        """Get the underlying HTTP client for direct requests.

        Used by download operations that need direct HTTP access.

        Returns:
            The httpx.AsyncClient instance.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if not self._http_client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        return self._http_client

    def cache_conversation_turn(
        self, conversation_id: str, query: str, answer: str, turn_number: int
    ) -> None:
        """Cache a conversation turn locally.

        Args:
            conversation_id: The conversation ID.
            query: The user's question.
            answer: The AI's response.
            turn_number: The turn number in the conversation.
        """
        if conversation_id not in self._conversation_cache:
            self._conversation_cache[conversation_id] = []
        self._conversation_cache[conversation_id].append({
            "query": query,
            "answer": answer,
            "turn_number": turn_number,
        })

    def get_cached_conversation(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get cached conversation turns.

        Args:
            conversation_id: The conversation ID.

        Returns:
            List of cached turns, or empty list if not found.
        """
        return self._conversation_cache.get(conversation_id, [])

    def clear_conversation_cache(self, conversation_id: Optional[str] = None) -> bool:
        """Clear conversation cache.

        Args:
            conversation_id: Clear specific conversation, or all if None.

        Returns:
            True if cache was cleared.
        """
        if conversation_id:
            if conversation_id in self._conversation_cache:
                del self._conversation_cache[conversation_id]
                return True
            return False
        else:
            self._conversation_cache.clear()
            return True
