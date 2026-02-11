"""LangGraph orchestrator routing requests through JD and repo analysis pipelines."""

from functools import lru_cache

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.agents.nodes.jd_node import jd_analysis_node
from app.agents.nodes.company_node import company_logic_node
from app.agents.nodes.capstone_node import capstone_generator_node
from app.agents.nodes.repo_node import repo_analysis_node
from app.agents.nodes.scaffold_node import scaffold_generator_node
from app.agents.nodes.portfolio_node import portfolio_optimizer_node
from app.agents.nodes.fitness_node import fitness_scorer_node
from app.logging_config import get_logger

logger = get_logger("agents.orchestrator")

def _route_after_company(state: AgentState) -> str:
    """
    Conditional routing after company logic node.
    If errors occurred, skip to END. Otherwise, continue to capstone.
    """
    errors = state.get("errors", [])
    if errors:
        logger.warning(f"Routing to END due to errors: {errors}")
        return END
    return "capstone_generator"

def _route_after_repo(state: AgentState) -> str:
    """
    Conditional routing after repo analysis node.
    If errors occurred, go to END. Otherwise, END (for now).
    """
    errors = state.get("errors", [])
    if errors:
        logger.warning(f"Routing to END due to repo errors: {errors}")
        return END
    # Future: could route to scaffold_generator here
    return END

def build_jd_pipeline() -> StateGraph:
    """
    Build the JD analysis → Capstone generation pipeline.

    Flow:
        START → jd_analysis → company_logic → capstone_generator → END
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("jd_analysis", jd_analysis_node)
    graph.add_node("company_logic", company_logic_node)
    graph.add_node("capstone_generator", capstone_generator_node)

    # Wire edges
    graph.add_edge(START, "jd_analysis")
    graph.add_edge("jd_analysis", "company_logic")
    graph.add_conditional_edges(
        "company_logic",
        _route_after_company,
        {
            "capstone_generator": "capstone_generator",
            END: END,
        },
    )
    graph.add_edge("capstone_generator", END)

    return graph

def build_repo_pipeline() -> StateGraph:
    """
    Build the Repo Analysis pipeline.

    Flow:
        START → repo_analysis → END
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("repo_analysis", repo_analysis_node)

    # Wire edges
    graph.add_edge(START, "repo_analysis")
    graph.add_conditional_edges(
        "repo_analysis",
        _route_after_repo,
        {
            END: END,
        },
    )

    return graph

@lru_cache(maxsize=2)
def compile_jd_pipeline(with_checkpointer: bool = False):
    """
    Compile the JD pipeline into an executable graph.

    Args:
        with_checkpointer: If True, enables state persistence
            for resumable execution. Requires thread_id in config.
    """
    graph = build_jd_pipeline()

    compile_kwargs = {}
    if with_checkpointer:
        compile_kwargs["checkpointer"] = MemorySaver()

    compiled = graph.compile(**compile_kwargs)

    logger.info("JD pipeline compiled successfully")
    return compiled

@lru_cache(maxsize=2)
def compile_repo_pipeline(with_checkpointer: bool = False):
    """
    Compile the Repo pipeline into an executable graph.

    Args:
        with_checkpointer: If True, enables state persistence
            for resumable execution. Requires thread_id in config.
    """
    graph = build_repo_pipeline()

    compile_kwargs = {}
    if with_checkpointer:
        compile_kwargs["checkpointer"] = MemorySaver()

    compiled = graph.compile(**compile_kwargs)

    logger.info("Repo pipeline compiled successfully")
    return compiled

# Scaffold Pipeline

def _route_after_scaffold(state: AgentState) -> str:
    """Conditional routing after scaffold generation."""
    errors = state.get("errors", [])
    if errors:
        logger.warning(f"Routing to END due to scaffold errors: {errors}")
        return END
    return END

def build_scaffold_pipeline() -> StateGraph:
    """
    Build the Scaffold generation pipeline.

    Flow:
        START → scaffold_generator → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("scaffold_generator", scaffold_generator_node)

    graph.add_edge(START, "scaffold_generator")
    graph.add_conditional_edges(
        "scaffold_generator",
        _route_after_scaffold,
        {END: END},
    )

    return graph

@lru_cache(maxsize=2)
def compile_scaffold_pipeline(with_checkpointer: bool = False):
    """
    Compile the Scaffold pipeline into an executable graph.
    """
    graph = build_scaffold_pipeline()

    compile_kwargs = {}
    if with_checkpointer:
        compile_kwargs["checkpointer"] = MemorySaver()

    compiled = graph.compile(**compile_kwargs)

    logger.info("Scaffold pipeline compiled successfully")
    return compiled

# Portfolio Pipeline

def _route_after_portfolio(state: AgentState) -> str:
    """Conditional routing after portfolio optimization."""
    errors = state.get("errors", [])
    if errors:
        logger.warning(f"Routing to END due to portfolio errors: {errors}")
        return END
    return END

def build_portfolio_pipeline() -> StateGraph:
    """
    Build the Portfolio optimization pipeline.

    Flow:
        START → portfolio_optimizer → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("portfolio_optimizer", portfolio_optimizer_node)

    graph.add_edge(START, "portfolio_optimizer")
    graph.add_conditional_edges(
        "portfolio_optimizer",
        _route_after_portfolio,
        {END: END},
    )

    return graph

@lru_cache(maxsize=2)
def compile_portfolio_pipeline(with_checkpointer: bool = False):
    """
    Compile the Portfolio pipeline into an executable graph.
    """
    graph = build_portfolio_pipeline()

    compile_kwargs = {}
    if with_checkpointer:
        compile_kwargs["checkpointer"] = MemorySaver()

    compiled = graph.compile(**compile_kwargs)

    logger.info("Portfolio pipeline compiled successfully")
    return compiled

# Fitness Pipeline

def _route_after_fitness(state: AgentState) -> str:
    """Conditional routing after fitness evaluation."""
    errors = state.get("errors", [])
    if errors:
        logger.warning(f"Routing to END due to fitness errors: {errors}")
        return END
    return END

def build_fitness_pipeline() -> StateGraph:
    """
    Build the Fitness scoring pipeline.

    Flow:
        START → fitness_scorer → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("fitness_scorer", fitness_scorer_node)

    graph.add_edge(START, "fitness_scorer")
    graph.add_conditional_edges(
        "fitness_scorer",
        _route_after_fitness,
        {END: END},
    )

    return graph

@lru_cache(maxsize=2)
def compile_fitness_pipeline(with_checkpointer: bool = False):
    """
    Compile the Fitness pipeline into an executable graph.
    """
    graph = build_fitness_pipeline()

    compile_kwargs = {}
    if with_checkpointer:
        compile_kwargs["checkpointer"] = MemorySaver()

    compiled = graph.compile(**compile_kwargs)

    logger.info("Fitness pipeline compiled successfully")
    return compiled
