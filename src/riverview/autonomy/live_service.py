"""Persistent Riverview Continuous Motion Engine service entrypoint."""

from __future__ import annotations

import signal
import threading

from riverview.autonomy.runtime import ContinuousMomentumRuntime


def main() -> None:
    stop = threading.Event()
    runtime = ContinuousMomentumRuntime()

    def shutdown(_signum: int, _frame: object) -> None:
        stop.set()
        runtime.stop()

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)
    runtime.serve()
    stop.set()


if __name__ == "__main__":
    main()
