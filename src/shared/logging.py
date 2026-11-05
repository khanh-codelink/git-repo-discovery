import logging

from opentelemetry import trace

_LOG_FORMAT = (
    "%(asctime)s - %(levelname)s [%(name)s]"
    " - trace_id=%(trace_id)s span_id=%(span_id)s span_name=%(span_name)s"
    " - %(message)s"
)


class SpanIdFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            record.span_id = format(ctx.span_id, "016x")[:6]
            record.trace_id = format(ctx.trace_id, "032x")[:6]
            record.span_name = getattr(span, "name", "")
        else:
            record.span_id = "NA"
            record.trace_id = "NA"
            record.span_name = "NA"
        return True


def _get_default_loglevel() -> int:
    try:
        from src.config import get_settings

        settings = get_settings()

        return getattr(logging, settings.loglevel.upper())
    except Exception:
        return logging.DEBUG


def _make_handler(handler: logging.Handler, log_level: int) -> logging.Handler:
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt="%H:%M:%S"))
    handler.addFilter(SpanIdFilter())
    return handler


def setup_logging() -> None:
    """Install the formatted handler on the root logger. Call once, before other imports.

    Some libraries (e.g. mrkdwn_analysis) call logging.basicConfig() at import time; once the
    root logger has a handler, their call is a no-op and every log line uses _LOG_FORMAT.
    """
    loglevel = _get_default_loglevel()
    logging.basicConfig(
        level=loglevel,
        handlers=[_make_handler(logging.StreamHandler(), loglevel)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    # Only add a local handler when setup_logging() hasn't run yet (e.g., unit tests).
    # If the root logger already has handlers, rely on propagation to avoid double output.
    if not logger.handlers and not logging.root.handlers:
        loglevel = _get_default_loglevel()
        logger.addHandler(_make_handler(logging.StreamHandler(), loglevel))
    if logger.level == logging.NOTSET:
        logger.setLevel(_get_default_loglevel())
    logger.propagate = True
    if SpanIdFilter not in [type(f) for f in logger.filters]:
        logger.addFilter(SpanIdFilter())
    return logger
