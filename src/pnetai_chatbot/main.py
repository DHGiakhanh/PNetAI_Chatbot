"""Root execution entrypoint launching the Uvicorn ASGI server."""

from __future__ import annotations

import uvicorn

from pnetai_chatbot.infrastructure.config.settings import get_settings
from pnetai_chatbot.interface.api.app import create_app

app = create_app()


def main() -> None:
    """Initialize and run the Uvicorn ASGI server based on settings."""
    settings = get_settings()

    reload_mode = settings.is_development

    uvicorn.run(
        "pnetai_chatbot.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=reload_mode,
    )


if __name__ == "__main__":
    main()
