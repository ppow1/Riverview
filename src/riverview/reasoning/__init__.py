"""Provider-neutral, bounded reasoning contracts."""

from .contracts import ReasoningProvider, ReasoningRequest, ReasoningResponse
from .gpu import GpuEvidence, LocalGpuReasoningAdapter
from .ollama import OllamaReasoningAdapter
from .registry import ReasoningProviderRegistry

__all__ = ["GpuEvidence", "LocalGpuReasoningAdapter", "OllamaReasoningAdapter", "ReasoningProvider", "ReasoningProviderRegistry", "ReasoningRequest", "ReasoningResponse"]
