"""
ai-content-autopilot - Python SDK for the Visibly Content Autopilot API.

Provides a Pull API client, HMAC-SHA256 webhook verification,
and a Flask Blueprint for receiving webhooks.
"""

from .client import VisiblyClient
from .security import verify_webhook_signature
from .webhook import (
    configure_visibly,
    contentpilot_webhook_bp,
    default_flask_blog_handler,
)

__version__ = "1.0.2"

__all__ = [
    "VisiblyClient",
    "verify_webhook_signature",
    "configure_visibly",
    "contentpilot_webhook_bp",
    "default_flask_blog_handler",
    "__version__",
]