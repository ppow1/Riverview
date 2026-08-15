"""Provider-neutral, bounded reasoning contracts."""

from .contracts import ReasoningProvider, ReasoningRequest, ReasoningResponse
from .gpu import GpuEvidence, LocalGpuReasoningAdapter
from .llama_cpp import LlamaCppReasoningAdapter
from .ollama import OllamaReasoningAdapter
from .registry import ReasoningProviderRegistry

__all__ = ["GpuEvidence", "LlamaCppReasoningAdapter", "LocalGpuReasoningAdapter", "OllamaReasoningAdapter", "ReasoningProvider", "ReasoningProviderRegistry", "ReasoningRequest", "ReasoningResponse"]
