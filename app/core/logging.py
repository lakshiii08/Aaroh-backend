import logging
import sys
import uuid
from contextvars import ContextVar

# Context variable for tracing request IDs across async calls
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "system"
        return True

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("aaroh_backend")
    if logger.handlers:
        return logger

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [req_id:%(request_id)s] %(name)s - %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    logger.addHandler(handler)
    return logger

logger = setup_logging()
