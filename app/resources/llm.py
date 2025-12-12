"""Unified LLM client supporting multiple providers."""

from typing import List, Optional, Any, Union, Dict
from app.config.settings import settings
from app.utils.logging import logger
from app.utils.gemini import gemini_key_manager
from langchain_core.messages import AIMessage


class LLMClient:
    """Multi-provider LLM client for chat, vision, and tool calling."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.LLM_API_KEY
        if settings.LLM_BASE_URL or base_url:
            self.base_url = base_url or settings.LLM_BASE_URL
        self.client = self._init_client()

    def _init_client(self) -> Any:
        """Initialize the appropriate LangChain client."""
        try:
            if self.provider == "openai":
                from langchain_openai import ChatOpenAI

                return ChatOpenAI(
                    model=self.model,
                    api_key=self.api_key,
                    base_url=getattr(self, "base_url", None),
                    temperature=settings.LLM_TEMPERATURE,
                )
            elif self.provider == "google":
                from langchain_google_genai import ChatGoogleGenerativeAI

                return ChatGoogleGenerativeAI(
                    model=self.model,
                    api_key=self.api_key,
                    temperature=settings.LLM_TEMPERATURE,
                )
            elif self.provider == "anthropic":
                return None  # Placeholder
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
        """Chat completion with optional tool calling."""
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        try:
            if self.provider == "openai":
                return await self._openai_chat(messages, tools, temp, max_tokens)
            elif self.provider == "google":
                return await self._google_chat(messages, tools, temp, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
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
        """Google Gemini chat with round-robin key rotation."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = ChatGoogleGenerativeAI(
            model=self.model,
            api_key=gemini_key_manager.get_next_key(),
            temperature=temperature,
            max_retries=0,
            timeout=30,
        )
        if tools:
            model = model.bind_tools(tools)
        response = await model.ainvoke(
            messages, **({"max_tokens": max_tokens} if max_tokens else {})
        )
        logger.debug(response)
        return response

    async def _openai_chat(
        self,
        messages: List[Any],
        tools: Optional[List[Any]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> AIMessage:
        """OpenAI chat completion."""
        model = self.client.bind_tools(tools) if tools else self.client
        kwargs = {"temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        return await model.ainvoke(messages, **kwargs)
