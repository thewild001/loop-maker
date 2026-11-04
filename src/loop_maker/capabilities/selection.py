"""Deterministic, policy-bounded capability selection.

Selection is advisory: it never resolves an executable binding or invokes a
capability. The host remains responsible for authorization and invocation-time
revalidation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    Authorization,
    Availability,
    CapabilityAssessment,
    CapabilityCategory,
    CapabilityDescriptor,
    CapabilityInventory,
    InterfaceKind,
)


class RejectionCode(str, Enum):
    OPERATION_NOT_SUPPORTED = "operation_not_supported"
    CATEGORY_NOT_ALLOWED = "category_not_allowed"
    INTERFACE_NOT_ALLOWED = "interface_not_allowed"
    PROVIDER_NOT_ALLOWED = "provider_not_allowed"
    PROVIDER_EXCLUDED = "provider_excluded"
    REQUIRED_TAGS_MISSING = "required_tags_missing"
    UNAVAILABLE = "unavailable"
    DEGRADED_NOT_ALLOWED = "degraded_not_allowed"
    AVAILABILITY_UNKNOWN = "availability_unknown"
    ACCESS_DENIED = "access_denied"
    APPROVAL_REQUIRED = "approval_required"
    AUTHORIZATION_UNKNOWN = "authorization_unknown"
    ASSESSMENT_MISSING = "assessment_missing"


@dataclass(frozen=True, slots=True)
class SelectionRequest:
    """Declarative requirements for one capability operation.

    ``objective`` is retained as request context for future intelligent rankers;
    this deterministic selector does not infer semantic relevance from prose.
    """

    operation_id: str
    objective: str | None = None
    categories: tuple[CapabilityCategory, ...] = ()
    interface_kinds: tuple[InterfaceKind, ...] = ()
    required_tags: tuple[str, ...] = ()
    allowed_providers: tuple[str, ...] = ()
    excluded_providers: tuple[str, ...] = ()
    preferred_providers: tuple[str, ...] = ()
    allow_degraded: bool = False
    max_results: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise ValueError("operation_id must be a non-empty string")
        if self.objective is not None and not self.objective.strip():
            raise ValueError("objective must be non-empty when provided")
        if self.max_results is not None and self.max_results < 1:
            raise ValueError("max_results must be greater than zero")
        for provider_id in (
            *self.allowed_providers, *self.excluded_providers, *self.preferred_providers
        ):
            if not isinstance(provider_id, str) or not provider_id.strip():
                raise ValueError("provider IDs must be non-empty strings")
        for tag in self.required_tags:
            if not isinstance(tag, str) or not tag.strip():
                raise ValueError("required tags must be non-empty strings")


@dataclass(frozen=True, slots=True)
class SelectedCapability:
    capability: CapabilityDescriptor
    operation_id: str
    assessment: CapabilityAssessment
    rank: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RejectedCapability:
    capability_id: str
    code: RejectionCode
    explanation: str


@dataclass(frozen=True, slots=True)
class SelectionResult:
    selected: tuple[SelectedCapability, ...] = ()
    approval_required: tuple[SelectedCapability, ...] = ()
    rejected: tuple[RejectedCapability, ...] = ()

    @property
    def has_eligible_capabilities(self) -> bool:
        return bool(self.selected)


class DeterministicCapabilitySelector:
    """Apply hard constraints, then produce a stable and explainable ordering."""

    def select(
        self,
        inventory: CapabilityInventory,
        request: SelectionRequest,
    ) -> SelectionResult:
        assessments = self._assessment_index(inventory.assessments)
        selected: list[tuple[CapabilityDescriptor, CapabilityAssessment]] = []
        approval: list[tuple[CapabilityDescriptor, CapabilityAssessment]] = []
        rejected: list[RejectedCapability] = []

        for capability in inventory.capabilities:
            reason = self._static_rejection(capability, request)
            if reason is not None:
                rejected.append(RejectedCapability(capability.id, reason[0], reason[1]))
                continue

            # An operation-specific assessment takes precedence over a capability-wide one.
            assessment = assessments.get((capability.id, request.operation_id)) or assessments.get(
                (capability.id, None)
            )
            if assessment is None:
                rejected.append(RejectedCapability(
                    capability.id,
                    RejectionCode.ASSESSMENT_MISSING,
                    "No assessment exists for this capability operation.",
                ))
                continue

            decision = self._assessment_rejection(assessment, request)
            if decision is not None:
                code, explanation = decision
                if code is RejectionCode.APPROVAL_REQUIRED:
                    approval.append((capability, assessment))
                else:
                    rejected.append(RejectedCapability(capability.id, code, explanation))
                continue
            selected.append((capability, assessment))

        selected.sort(key=lambda item: self._sort_key(item[0], request))
        approval.sort(key=lambda item: self._sort_key(item[0], request))
        if request.max_results is not None:
            selected = selected[:request.max_results]

        ranked = tuple(
            SelectedCapability(
                capability=capability,
                operation_id=request.operation_id,
                assessment=assessment,
                rank=index,
                reasons=self._selection_reasons(capability, request, assessment),
            )
            for index, (capability, assessment) in enumerate(selected, start=1)
        )
        approval_ranked = tuple(
            SelectedCapability(
                capability=capability,
                operation_id=request.operation_id,
                assessment=assessment,
                rank=index,
                reasons=("Approval is required; this is not an execution grant.",),
            )
            for index, (capability, assessment) in enumerate(approval, start=1)
        )
        return SelectionResult(
            selected=ranked,
            approval_required=approval_ranked,
            rejected=tuple(sorted(rejected, key=lambda item: item.capability_id)),
        )

    @staticmethod
    def _assessment_index(
        assessments: tuple[CapabilityAssessment, ...],
    ) -> dict[tuple[str, str | None], CapabilityAssessment]:
        """Keep the newest assessment per capability and operation scope."""
        index: dict[tuple[str, str | None], CapabilityAssessment] = {}
        for assessment in assessments:
            key = (assessment.capability_id, assessment.operation_id)
            current = index.get(key)
            if current is None or assessment.assessed_at > current.assessed_at:
                index[key] = assessment
        return index

    @staticmethod
    def _static_rejection(
        capability: CapabilityDescriptor,
        request: SelectionRequest,
    ) -> tuple[RejectionCode, str] | None:
        if not any(op.id == request.operation_id for op in capability.operations):
            return (RejectionCode.OPERATION_NOT_SUPPORTED, "Requested operation is not declared.")
        if request.categories and capability.category not in request.categories:
            return (RejectionCode.CATEGORY_NOT_ALLOWED, "Capability category is outside the request.")
        if request.interface_kinds and capability.interface.kind not in request.interface_kinds:
            return (RejectionCode.INTERFACE_NOT_ALLOWED, "Interface kind is outside the request.")
        provider_id = capability.source.provider_id
        if provider_id in request.excluded_providers:
            return (RejectionCode.PROVIDER_EXCLUDED, "Provider is explicitly excluded.")
        if request.allowed_providers and provider_id not in request.allowed_providers:
            return (RejectionCode.PROVIDER_NOT_ALLOWED, "Provider is not in the request allowlist.")
        missing = set(request.required_tags) - set(capability.constraints.tags)
        if missing:
            return (
                RejectionCode.REQUIRED_TAGS_MISSING,
                f"Required capability tags are missing: {', '.join(sorted(missing))}.",
            )
        return None

    @staticmethod
    def _assessment_rejection(
        assessment: CapabilityAssessment,
        request: SelectionRequest,
    ) -> tuple[RejectionCode, str] | None:
        if assessment.availability is Availability.UNAVAILABLE:
            return (RejectionCode.UNAVAILABLE, "Capability operation is unavailable.")
        if assessment.availability is Availability.UNKNOWN:
            return (RejectionCode.AVAILABILITY_UNKNOWN, "Availability has not been established.")
        if assessment.availability is Availability.DEGRADED and not request.allow_degraded:
            return (RejectionCode.DEGRADED_NOT_ALLOWED, "Degraded operation is not allowed.")
        if assessment.authorization is Authorization.DENIED:
            return (RejectionCode.ACCESS_DENIED, "Host policy denied this operation.")
        if assessment.authorization is Authorization.REQUIRES_APPROVAL:
            return (RejectionCode.APPROVAL_REQUIRED, "Host approval is required before use.")
        if assessment.authorization is Authorization.UNKNOWN:
            return (RejectionCode.AUTHORIZATION_UNKNOWN, "Authorization has not been established.")
        return None

    @staticmethod
    def _sort_key(
        capability: CapabilityDescriptor,
        request: SelectionRequest,
    ) -> tuple[int, str, str]:
        try:
            provider_rank = request.preferred_providers.index(capability.source.provider_id)
        except ValueError:
            provider_rank = len(request.preferred_providers)
        return (provider_rank, capability.name.casefold(), capability.id)

    @staticmethod
    def _selection_reasons(
        capability: CapabilityDescriptor,
        request: SelectionRequest,
        assessment: CapabilityAssessment,
    ) -> tuple[str, ...]:
        reasons = ["Declared operation and request constraints match."]
        if capability.source.provider_id in request.preferred_providers:
            reasons.append("Provider is explicitly preferred.")
        if assessment.availability is Availability.DEGRADED:
            reasons.append("Degraded availability was explicitly permitted.")
        return tuple(reasons)
