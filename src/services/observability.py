"""Langfuse tracing: the one place that wires LangChain calls and pipeline steps into traces.

- `@observe` (re-exported from langfuse) wraps plain-Python steps and request entry points.
- `llm_run_config()` builds the config for every LangChain `.ainvoke()`, attaching the
  Langfuse callback handler so the call nests under the surrounding `@observe` span.

Tracing never breaks a request: without keys, or with LANGFUSE_TRACING_ENABLED=false,
the decorators still run the wrapped functions and no callback handler is attached.
"""

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig
from langfuse import Langfuse, get_client, observe, propagate_attributes
from langfuse.langchain import CallbackHandler

from src.config import get_langfuse_config
from src.shared.logging import get_logger

__all__ = [
    "flush_langfuse",
    "init_langfuse",
    "llm_run_config",
    "observe",
    "propagate_attributes",
    "record_input",
]

logger = get_logger(__name__)


def init_langfuse() -> None:
    """Create the Langfuse client from config. Call once at startup."""
    config = get_langfuse_config()
    if not config.is_active:
        reason = "disabled" if not config.tracing_enabled else "LANGFUSE_* keys are not set"
        logger.warning("Langfuse tracing is off (%s); requests run without traces.", reason)
        # Without a public key the SDK logs an authentication warning on every traced
        # call; one warning at startup is enough.
        logging.getLogger("langfuse").setLevel(logging.ERROR)
        Langfuse(tracing_enabled=False)
        return

    # The first client created becomes the one `get_client()` and `@observe` use.
    Langfuse(
        public_key=config.public_key,
        secret_key=config.secret_key.get_secret_value() if config.secret_key else None,
        base_url=config.base_url,
        tracing_enabled=True,
    )
    logger.info("Langfuse tracing is on, sending traces to %s", config.base_url)


def flush_langfuse() -> None:
    """Send any buffered traces. Call before the process exits."""
    if get_langfuse_config().is_active:
        logger.info("Flushing buffered Langfuse traces")
        get_client().flush()


def record_input(**fields: Any) -> None:
    """Set the current span's input by hand.

    For `@observe(capture_input=False)` steps: their arguments include a GitHub client or
    an auth context holding credentials, so only these safe fields are recorded instead.
    """
    get_client().update_current_span(input=fields)


def llm_run_config(
    run_name: str,
    *,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RunnableConfig:
    """Build the config for a LangChain call, with the Langfuse handler when tracing is on.

    `run_name` becomes the observation name in the trace tree.
    """
    config: RunnableConfig = {"run_name": run_name}
    if tags:
        config["tags"] = tags
    if metadata:
        config["metadata"] = metadata
    if get_langfuse_config().is_active:
        config["callbacks"] = [CallbackHandler()]
    return config
