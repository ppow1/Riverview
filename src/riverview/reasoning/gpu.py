"""Named local GPU provider probes over the provider-neutral reasoning contract."""

from __future__ import annotations

import csv
import io
import subprocess
from dataclasses import dataclass

from .contracts import ReasoningRequest, ReasoningResponse
from .llama_cpp import LlamaCppReasoningAdapter
from .ollama import OllamaReasoningAdapter


@dataclass(frozen=True, slots=True)
class GpuEvidence:
    adapter_id: str
    gpu_name: str
    driver: str
    memory_total_mib: int
    memory_used_before_mib: int
    memory_used_after_mib: int
    model: str
    status: str
    reason: str
    runtime_endpoint: str


def _inventory() -> list[dict[str, str]]:
    output = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,name,driver_version,memory.total,memory.used", "--format=csv,noheader,nounits"],
        text=True,
        timeout=10,
    )
    return list(csv.DictReader(io.StringIO(output), fieldnames=("index", "name", "driver", "total", "used"), skipinitialspace=True))


class LocalGpuReasoningAdapter:
    def __init__(self, adapter_id: str, expected_name: str, *, endpoint: str = "http://127.0.0.1:11434", runtime: str = "ollama") -> None:
        if adapter_id not in {"rtx4090", "p100"}:
            raise ValueError("RIV-REASON-0003: GPU adapter identity is closed.")
        self.adapter_id = adapter_id
        self.expected_name = expected_name
        self.endpoint = endpoint
        if runtime not in {"ollama", "llama-cpp"}:
            raise ValueError("RIV-REASON-0003: GPU runtime identity is closed.")
        self.runtime = runtime

    def complete(self, model: str, request: ReasoningRequest) -> tuple[ReasoningResponse | None, GpuEvidence]:
        devices = _inventory()
        matches = [device for device in devices if self.expected_name.lower() in device["name"].lower()]
        if not matches:
            raise RuntimeError("RIV-REASON-0003: named GPU is unavailable.")
        device = matches[0]
        before = int(device["used"])
        adapter = (LlamaCppReasoningAdapter if self.runtime == "llama-cpp" else OllamaReasoningAdapter)(endpoint=self.endpoint, timeout_seconds=90)
        result = adapter.complete(model, request)
        after_devices = {item["index"]: item for item in _inventory()}
        after = int(after_devices[device["index"]]["used"])
        if after <= before:
            evidence = GpuEvidence(
                self.adapter_id, device["name"], device["driver"], int(device["total"]),
                before, after, model, "rejected",
                f"runtime endpoint {self.endpoint} completed but did not use the named {device['name']} device",
                self.endpoint,
            )
            return None, evidence
        evidence = GpuEvidence(
            self.adapter_id, device["name"], device["driver"], int(device["total"]),
            before, after, model, "succeeded",
            f"bounded Ollama request completed on the measured {device['name']} runtime",
            self.endpoint,
        )
        return result, evidence
