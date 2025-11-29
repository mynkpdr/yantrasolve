from typing import List, Optional, Any, Union, Dict

from app.config.settings import settings
from app.utils.logging import logger
from app.utils.gemini import gemini_key_manager
from langchain_core.messages import AIMessage


class LLMClient:
    """
    Unified LLM interaction tool.

    Supports multiple providers (OpenAI, Anthropic, Google) with
    chat, vision, audio transcription, and structured extraction.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize LLM tool.

        Args:
            provider: LLM provider ("openai", "anthropic", "google")
            model: Model name
            api_key: API key for the provider
            base_url: Base URL for the client
        """
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.LLM_API_KEY

        if settings.LLM_BASE_URL or base_url:
            self.base_url = base_url or settings.LLM_BASE_URL
        self.client = self._init_client()

    def _init_client(self) -> Any:
        """Initialize the appropriate client based on provider."""
        try:
            if self.provider == "openai":
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(
                    model=self.model,
                    api_key=self.api_key,
                    base_url=getattr(self, "base_url", None),
                    temperature=settings.LLM_TEMPERATURE,
                )
            elif self.provider == "anthropic":
                return (
                    None  # Placeholder for Anthropic client initialization as for now
                )
            elif self.provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=settings.LLM_TEMPERATURE,
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except ImportError as e:
            logger.error(f"Failed to import client for {self.provider}: {e}")
            raise

    async def chat(
        self,
        messages: List[Union[Dict[str, str], Any]],
        tools: Optional[List[Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AIMessage:
        """
        Standard chat completion with optional tool calling.

        Args:
            messages: List of message dictionaries with role and content, or langchain messages
            tools: Optional list of tool definitions for function calling
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            AIMessage dictionary with content, role, and tool calls
        """

        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

        try:
            if self.provider == "openai":
                result = await self._openai_chat(messages, tools, temp, max_tokens)
            elif self.provider == "google":
                result = await self._google_chat(messages, tools, temp, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            return result

        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return AIMessage(content=f"Error: {str(e)}", role="error")

    async def _google_chat(
        self,
        messages: List[Any],
        tools: Optional[List[Any]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> AIMessage:
        """Google-specific chat completion using LangChain with round-robin key rotation."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        # Get next API key from round-robin manager
        api_key = gemini_key_manager.get_next_key()
        # Create a fresh client with the rotated key
        model = ChatGoogleGenerativeAI(
            model=self.model,
            api_key=api_key,
            temperature=temperature,
            max_retries=0,
            timeout=30,
        )

        if tools:
            model = model.bind_tools(tools)

        kwargs = {}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = await model.ainvoke(messages, **kwargs)

        logger.debug(response)

        return response

    async def _openai_chat(
        self,
        messages: List[Any],
        tools: Optional[List[Any]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> AIMessage:
        """OpenAI-specific chat completion using LangChain."""

        model = self.client
        if tools:
            model = model.bind_tools(tools)

        kwargs = {"temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = await model.ainvoke(messages, **kwargs)

        return response
