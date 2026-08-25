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
from .escalation_policy import (
    POLICY_EVENT_TYPE,
    POLICY_VERSION,
    CapacitySnapshot,
    ConsequenceClass,
    EscalationPolicy,
    PolicyDecisionRecorder,
    PolicyInputError,
)
from .gpu import GpuEvidence, LocalGpuReasoningAdapter
from .llama_cpp import LlamaCppReasoningAdapter
from .ollama import OllamaReasoningAdapter
from .registry import ReasoningProviderRegistry
from .binding import (
    BindingConfiguration,
    BindingConfigurationLoader,
    CapabilityBindingDecision,
    CapabilityBindingError,
    CognitionBindingAdapter,
    ProviderResourceCandidate,
    TierBinding,
)
from .reservation import (
    CapacitySnapshot,
    ReservationError,
    ReservationState,
    ResidentCognitionReservation,
    ResidentCognitionReservationAdapter,
)

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
    "BindingConfiguration",
    "BindingConfigurationLoader",
    "CapabilityBindingDecision",
    "CapabilityBindingError",
    "CognitionBindingAdapter",
    "ProviderResourceCandidate",
    "TierBinding",
    "CapacitySnapshot",
    "ReservationError",
    "ReservationState",
    "ResidentCognitionReservation",
    "ResidentCognitionReservationAdapter",
    "ReasoningRequest",
    "ReasoningResponse",
    "ReasoningResult",
    "ResidentReasoningPacket",
    "ResidentReasoningPacketAssembler",
    "CapacitySnapshot",
    "ConsequenceClass",
    "EscalationPolicy",
    "POLICY_EVENT_TYPE",
    "POLICY_VERSION",
    "PolicyDecisionRecorder",
    "PolicyInputError",
]
