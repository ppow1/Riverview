"""Persistent bounded Riverview Open WebUI service entrypoint."""

from __future__ import annotations

import os
import time

from riverview.operator.openwebui import OpenWebUIConfig, RiverviewOpenWebUIService
from riverview.reasoning import OllamaReasoningAdapter


def main() -> None:
    token = os.environ.get("RIVERVIEW_OPENWEBUI_TOKEN", "")
    if not token:
        raise RuntimeError("RIV-UI-0009: service token must be supplied through the process environment.")
    adapter = OllamaReasoningAdapter()
    service = RiverviewOpenWebUIService(
        OpenWebUIConfig(port=18082, service_identity="riverview-openwebui", bearer_token=token),
        lambda model, request: adapter.complete(model, request),
    )
    service.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()


if __name__ == "__main__":
    main()
