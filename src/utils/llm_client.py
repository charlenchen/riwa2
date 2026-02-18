import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from src.utils.logger import logger


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass

    @abstractmethod
    def generate_with_history(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate text with conversation history."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self._client = None

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Gemini provider will not be functional.")

    def _get_client(self):
        """Lazy load the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                logger.error("google-generativeai package not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                return None
        return self._client

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini."""
        client = self._get_client()
        if not client:
            return self._fallback_response(prompt)

        try:
            response = client.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return self._fallback_response(prompt)

    def generate_with_history(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate text with conversation history using Gemini."""
        client = self._get_client()
        if not client:
            return self._fallback_response(prompt)

        try:
            # Start chat with history
            chat = client.start_chat(history=[])
            for msg in conversation_history:
                role = "user" if msg.get("role") == "user" else "model"
                chat.send_message(msg.get("content", ""))

            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Return a fallback response when API is unavailable."""
        return f"[Gemini unavailable] Received prompt: {prompt[:100]}..."


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo"
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self._client = None

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. OpenAI provider will not be functional.")

    def _get_client(self):
        """Lazy load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("openai package not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                return None
        return self._client

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI."""
        client = self._get_client()
        if not client:
            return self._fallback_response(prompt)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return self._fallback_response(prompt)

    def generate_with_history(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate text with conversation history using OpenAI."""
        client = self._get_client()
        if not client:
            return self._fallback_response(prompt)

        try:
            messages = conversation_history + [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        """Return a fallback response when API is unavailable."""
        return f"[OpenAI unavailable] Received prompt: {prompt[:100]}..."


class MockProvider(LLMProvider):
    """Mock provider for testing without API access."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.call_history: List[Dict[str, Any]] = []

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response."""
        self.call_history.append({
            "type": "generate",
            "prompt": prompt,
            "kwargs": kwargs
        })

        # Check for exact match
        if prompt in self.responses:
            return self.responses[prompt]

        # Check for pattern match
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                return response

        # Default mock response
        return f"[Mock] Generated response for: {prompt[:50]}..."

    def generate_with_history(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate mock response with history."""
        self.call_history.append({
            "type": "generate_with_history",
            "prompt": prompt,
            "history": conversation_history,
            "kwargs": kwargs
        })

        return self.generate(prompt, **kwargs)


class LLMClient:
    """
    Unified LLM client that supports multiple providers.
    Provides a consistent interface for all LLM operations.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or self._auto_detect_provider()
        logger.info(f"Using LLM provider: {type(self.provider).__name__}")

    @staticmethod
    def _auto_detect_provider() -> LLMProvider:
        """Auto-detect and initialize the best available provider."""
        # Try Gemini first (as per project docs)
        if os.environ.get("GEMINI_API_KEY"):
            return GeminiProvider()

        # Try OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            return OpenAIProvider()

        # Fall back to mock
        logger.info("No API keys found. Using MockProvider for testing.")
        return MockProvider()

    def generate(
        self,
        prompt: str,
        style: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt
            style: Optional writing style to apply
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated text
        """
        if style:
            prompt = self._apply_style(prompt, style)

        return self.provider.generate(prompt, **kwargs)

    def generate_with_history(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]],
        style: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text with conversation history.

        Args:
            prompt: Current prompt
            conversation_history: List of previous messages
            style: Optional writing style to apply
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated text
        """
        if style:
            prompt = self._apply_style(prompt, style)

        return self.provider.generate_with_history(
            prompt, conversation_history, **kwargs
        )

    def _apply_style(self, prompt: str, style: str) -> str:
        """Apply a writing style to the prompt."""
        style_instructions = {
            'default': "Write in a clear, engaging style.",
            'narrative': "Write as a compelling story with vivid descriptions.",
            'dramatic': "Write with dramatic tension and emotional intensity.",
            'humorous': "Write with wit and humor.",
            'formal': "Write in a formal, professional tone.",
            'casual': "Write in a casual, conversational tone.",
            'poetic': "Write with poetic language and imagery.",
            'technical': "Write with precise, technical language."
        }

        instruction = style_instructions.get(
            style,
            style_instructions['default']
        )

        return f"{prompt}\n\n{instruction}"

    def summarize(self, text: str, max_length: int = 100) -> str:
        """Summarize a piece of text."""
        prompt = f"Summarize the following text in a concise manner:\n\n{text}"
        return self.generate(prompt)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text."""
        prompt = f"""Extract all named entities from the following text.
Return them as a JSON object with categories (characters, locations, items, events):

{text}"""
        # Note: In production, you'd want to parse the JSON response
        return self.generate(prompt)

    def continue_story(
        self,
        story_so_far: str,
        continuation_length: int = 200
    ) -> str:
        """Continue a story from where it left off."""
        prompt = f"""Continue the following story naturally:

{story_so_far}

Continue the narrative:"""
        return self.generate(prompt, style='narrative')


# Convenience function for quick initialization
def create_llm_client(provider_type: Optional[str] = None) -> LLMClient:
    """
    Create an LLM client with the specified provider.

    Args:
        provider_type: 'gemini', 'openai', 'mock', or None for auto-detect

    Returns:
        Configured LLMClient instance
    """
    if provider_type == 'gemini':
        provider = GeminiProvider()
    elif provider_type == 'openai':
        provider = OpenAIProvider()
    elif provider_type == 'mock':
        provider = MockProvider()
    else:
        return LLMClient()  # Auto-detect

    return LLMClient(provider)
