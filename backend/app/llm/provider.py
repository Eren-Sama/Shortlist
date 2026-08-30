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
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("llm.provider")


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    GEMINI = "gemini"


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

    # Select base model based on task
    model_name = _select_model(task, settings)

    # Initialize available models
    available = []
    
    # Priority: Groq -> OpenAI -> Gemini
    if settings.GROQ_API_KEY:
        available.append((LLMProvider.GROQ, _create_groq_llm(model_name, _temperature, _max_tokens, settings)))
    if settings.OPENAI_API_KEY:
        available.append((LLMProvider.OPENAI, _create_openai_llm(model_name, _temperature, _max_tokens, settings)))
    if settings.GEMINI_API_KEY:
        # Try the primary Gemini model
        gemini_primary = _create_gemini_llm(model_name, _temperature, _max_tokens, settings)
        
        # Add other massive-context Gemini models as fallbacks to avoid 503s
        gemini_fallbacks = [
            _create_gemini_llm("gemini-1.5-pro", _temperature, _max_tokens, settings),
            _create_gemini_llm("gemini-1.5-flash", _temperature, _max_tokens, settings),
            _create_gemini_llm("gemini-2.0-flash-exp", _temperature, _max_tokens, settings)
        ]
        
        # Chain the Gemini fallbacks together
        gemini_with_fallbacks = gemini_primary.with_fallbacks(gemini_fallbacks)
        available.append((LLMProvider.GEMINI, gemini_with_fallbacks))

    if not available:
        raise RuntimeError(
            "No LLM API key configured. "
            "Set GROQ_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY in .env"
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


def _create_groq_llm(
    model: str, temperature: float, max_tokens: int, settings
) -> ChatGroq:
    """Create a Groq-backed LLM instance."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
        
    # Map foreign models to sensible Groq defaults
    if "gemini" in model.lower() or "gpt" in model.lower():
        model = "llama-3.1-70b-versatile"

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
        
    if "gpt" not in model.lower():
        model = "gpt-4o-mini"

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=settings.OPENAI_API_KEY,
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
