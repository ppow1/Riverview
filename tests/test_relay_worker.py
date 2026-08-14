"""Unit seams for the persistent Relay worker. Version: 0.6.0"""

from pathlib import Path

import pytest

from riverview.relay.worker import RelayWorker, WorkerStatistics


def test_statistics_begin_at_zero() -> None:
    statistics = WorkerStatistics()
    assert statistics.cycles == statistics.notifications == statistics.completed == statistics.failed == 0


def test_worker_rejects_nonpositive_poll_interval() -> None:
    with pytest.raises(ValueError, match="RIV-WRK-0005"):
        RelayWorker(Path.cwd(), "test-worker", poll_seconds=0)