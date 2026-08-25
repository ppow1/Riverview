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
from .context_assembler import (
    ASSEMBLER_VERSION,
    ReasoningAssemblyRequest,
    ReasoningContextAssemblyError,
    ResidentReasoningPacketAssembler,
)
from .provenance import (
    CognitionProvenance,
    CognitionProvenanceEventType,
    CognitionProvenanceWriter,
    ProvenanceLineageError,
)
from .session import (
    CognitionSession,
    CognitionSessionBoundary,
    CognitionSessionError,
    CognitionSessionTurn,
)
from .gpu import GpuEvidence, LocalGpuReasoningAdapter
from .llama_cpp import LlamaCppReasoningAdapter
from .ollama import OllamaReasoningAdapter
from .registry import ReasoningProviderRegistry

__all__ = [
    "CapabilityResourceRequest",
    "ASSEMBLER_VERSION",
    "CognitionActorClass",
    "CognitionFailureCode",
    "CognitionProvenance",
    "CognitionProvenanceEventType",
    "CognitionProvenanceWriter",
    "CognitionSession",
    "CognitionSessionBoundary",
    "CognitionSessionError",
    "CognitionSessionTurn",
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
    "ReasoningAssemblyRequest",
    "ReasoningContextAssemblyError",
    "ProvenanceLineageError",
    "ReasoningProviderRegistry",
    "ReasoningRequest",
    "ReasoningResponse",
    "ReasoningResult",
    "ResidentReasoningPacket",
    "ResidentReasoningPacketAssembler",
]
