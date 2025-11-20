#!/usr/bin/env python3
"""Backend launcher without noisy reload side effects."""

import os
from pathlib import Path
import uvicorn
from app.config import settings


def _is_reload_enabled() -> bool:
    flag = os.getenv("BACKEND_RELOAD", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    reload_enabled = _is_reload_enabled()

    # Limit the reloader to application code and ignore storage writes that would spawn new workers.
    app_dir = Path(__file__).parent / "app"
    storage_dir = Path(settings.storage_path).resolve()

    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=reload_enabled,
        reload_dirs=[str(app_dir)],
        reload_excludes=[str(storage_dir)],
    )
