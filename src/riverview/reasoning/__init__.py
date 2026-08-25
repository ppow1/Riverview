"""Provider-neutral, bounded reasoning and resident cognition contracts."""

from .contracts import ReasoningProvider, ReasoningRequest, ReasoningResponse
from .cognition_contracts import (
    CapabilityResourceRequest,
    CognitionActorClass,
    CognitionFailureCode,
    CognitionResult,
    CognitionResultStatus,
    CognitionTier,
    EscalationAssessment,
    EscalationDecision,
    ReasoningResult,
    ResidentReasoningPacket,
)
from .gpu import GpuEvidence, LocalGpuReasoningAdapter
from .llama_cpp import LlamaCppReasoningAdapter
from .ollama import OllamaReasoningAdapter
from .registry import ReasoningProviderRegistry

__all__ = [
    "CapabilityResourceRequest",
    "CognitionActorClass",
    "CognitionFailureCode",
    "CognitionResult",
    "CognitionResultStatus",
    "CognitionTier",
    "EscalationAssessment",
    "EscalationDecision",
    "GpuEvidence",
    "LlamaCppReasoningAdapter",
    "LocalGpuReasoningAdapter",
    "OllamaReasoningAdapter",
    "ReasoningProvider",
    "ReasoningProviderRegistry",
    "ReasoningRequest",
    "ReasoningResponse",
    "ReasoningResult",
    "ResidentReasoningPacket",
]
