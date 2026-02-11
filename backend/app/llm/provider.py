"""
Shortlist — LLM Provider Factory

Abstracts LLM access behind a provider-agnostic interface.
Supports: Groq (primary), OpenAI (fallback).
Easily extensible for Ollama, Together, etc.
"""

from typing import Optional
from enum import Enum

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("llm.provider")


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"


class LLMTask(str, Enum):
    """
    Task categories that map to different model selections.
    Different tasks may benefit from different models.
    """
    ANALYSIS = "analysis"       # JD parsing, skill extraction
    CODE_GEN = "code_gen"       # Scaffold generation, code writing
    TEXT_GEN = "text_gen"       # README, resume bullets, demo scripts
    SCORING = "scoring"         # Repo analysis scoring


def get_llm(
    task: LLMTask = LLMTask.ANALYSIS,
    provider: Optional[LLMProvider] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    Factory function — returns the appropriate LLM for the task.

    Priority:
    1. Explicit provider override
    2. Groq (primary — free, fast)
    3. OpenAI (fallback — if Groq key is missing)

    Security:
    - API keys are sourced from environment variables only
    - Never logged, never passed in URLs
    """
    settings = get_settings()
    _temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    _max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

    # Select model based on task
    model_name = _select_model(task, settings)

    # Determine provider
    if provider is None:
        if settings.GROQ_API_KEY:
            provider = LLMProvider.GROQ
        elif settings.OPENAI_API_KEY:
            provider = LLMProvider.OPENAI
        else:
            raise RuntimeError(
                "No LLM API key configured. "
                "Set GROQ_API_KEY or OPENAI_API_KEY in .env"
            )

    logger.info(
        f"Creating LLM: provider={provider.value}, "
        f"model={model_name}, task={task.value}, "
        f"temperature={_temperature}"
    )

    if provider == LLMProvider.GROQ:
        return _create_groq_llm(model_name, _temperature, _max_tokens, settings)
    elif provider == LLMProvider.OPENAI:
        return _create_openai_llm(model_name, _temperature, _max_tokens, settings)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _select_model(task: LLMTask, settings) -> str:
    """Select the best model for the given task."""
    model_map = {
        LLMTask.ANALYSIS: settings.LLM_ANALYSIS_MODEL,
        LLMTask.CODE_GEN: settings.LLM_CODE_MODEL,
        LLMTask.TEXT_GEN: settings.LLM_ANALYSIS_MODEL,   # Same as analysis — good at text
        LLMTask.SCORING: settings.LLM_ANALYSIS_MODEL,
    }
    return model_map.get(task, settings.LLM_ANALYSIS_MODEL)


def _create_groq_llm(
    model: str, temperature: float, max_tokens: int, settings
) -> ChatGroq:
    """Create a Groq-backed LLM instance."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    return ChatGroq(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.GROQ_API_KEY,
        max_retries=3,
        timeout=60,
    )


def _create_openai_llm(
    model: str, temperature: float, max_tokens: int, settings
) -> BaseChatModel:
    """Create an OpenAI-backed LLM instance."""
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    # Lazy import — only needed if OpenAI is used
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise RuntimeError(
            "langchain-openai is not installed. "
            "Run: pip install langchain-openai"
        )

    return ChatOpenAI(
        model=model if "gpt" in model.lower() else "gpt-4o",
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.OPENAI_API_KEY,
        max_retries=3,
        timeout=60,
    )
