"""
Shortlist — LLM Provider Factory

Abstracts LLM access behind a provider-agnostic interface.
Supports: Groq (primary), OpenAI (fallback).
Easily extensible for Ollama, Together, etc.
"""

from typing import Optional
from enum import Enum

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI  # Used for MiniMax OpenAI-compat API
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("llm.provider")


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    NVIDIA = "nvidia"
    MINIMAX = "minimax"


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
    2. Gemini (primary — 2M context)
    3. NVIDIA Nemotron Ultra (fallback — 1M context, free)
    4. MiniMax M3 (fallback — 1M context, free)

    Security:
    - API keys are sourced from environment variables only
    - Never logged, never passed in URLs
    """
    settings = get_settings()
    _temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    _max_tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

    # Select base model based on task
    model_name = _select_model(task, settings)

    # Initialize available models
    available = []
    
    # Priority: Gemini -> NVIDIA Nemotron -> MiniMax M3
    if settings.GEMINI_API_KEY:
        # Primary Gemini model with same-provider fallbacks
        gemini_primary = _create_gemini_llm(model_name, _temperature, _max_tokens, settings)
        gemini_fallbacks = [
            _create_gemini_llm("gemini-1.5-pro", _temperature, _max_tokens, settings),
            _create_gemini_llm("gemini-1.5-flash", _temperature, _max_tokens, settings),
            _create_gemini_llm("gemini-2.0-flash-exp", _temperature, _max_tokens, settings)
        ]
        gemini_with_fallbacks = gemini_primary.with_fallbacks(gemini_fallbacks)
        available.append((LLMProvider.GEMINI, gemini_with_fallbacks))

    if settings.NVIDIA_API_KEY:
        available.append((LLMProvider.NVIDIA, _create_nvidia_llm(model_name, _temperature, _max_tokens, settings)))

    if settings.MINIMAX_API_KEY:
        available.append((LLMProvider.MINIMAX, _create_minimax_llm(model_name, _temperature, _max_tokens, settings)))

    if not available:
        raise RuntimeError(
            "No LLM API key configured. "
            "Set GEMINI_API_KEY, NVIDIA_API_KEY, or MINIMAX_API_KEY in .env"
        )

    # Reorder based on explicit provider request
    if provider:
        for i, (p, llm) in enumerate(available):
            if p == provider:
                available.insert(0, available.pop(i))
                break

    primary_provider, primary_llm = available[0]
    fallbacks = [llm for p, llm in available[1:]]

    logger.info(
        f"Creating LLM: task={task.value}, primary={primary_provider.value}, "
        f"fallbacks={len(fallbacks)}, temperature={_temperature}"
    )

    if fallbacks:
        return primary_llm.with_fallbacks(fallbacks)
    return primary_llm


def _select_model(task: LLMTask, settings) -> str:
    """Select the best model for the given task."""
    model_map = {
        LLMTask.ANALYSIS: settings.LLM_ANALYSIS_MODEL,
        LLMTask.CODE_GEN: settings.LLM_CODE_MODEL,
        LLMTask.TEXT_GEN: settings.LLM_ANALYSIS_MODEL,   # Same as analysis — good at text
        LLMTask.SCORING: settings.LLM_ANALYSIS_MODEL,
    }
    return model_map.get(task, settings.LLM_ANALYSIS_MODEL)


def _create_nvidia_llm(
    model: str, temperature: float, max_tokens: int, settings
) -> BaseChatModel:
    """Create an NVIDIA Nemotron-backed LLM instance (1M context, free tier)."""
    if not settings.NVIDIA_API_KEY:
        raise RuntimeError("NVIDIA_API_KEY not set")

    return ChatNVIDIA(
        model="nvidia/nemotron-ultra-253b-v1",
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.NVIDIA_API_KEY,
        max_retries=3,
    )


def _create_minimax_llm(
    model: str, temperature: float, max_tokens: int, settings
) -> BaseChatModel:
    """Create a MiniMax M3-backed LLM instance (1M context, free tier)."""
    if not settings.MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY not set")

    # MiniMax is OpenAI-compatible — just point base_url at their endpoint
    return ChatOpenAI(
        model="MiniMax-M3",
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.MINIMAX_API_KEY,
        base_url="https://api.minimax.io/v1",
        max_retries=3,
        timeout=60,
    )


def _create_gemini_llm(
    model: str, temperature: float, max_tokens: int, settings
) -> BaseChatModel:
    """Create a Google Gemini-backed LLM instance."""
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
        
    if "gemini" not in model.lower():
        model = "gemini-1.5-flash"

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        max_output_tokens=max_tokens,
        google_api_key=settings.GEMINI_API_KEY,
        max_retries=3,
        timeout=60,
    )
