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
    ASSESSMENT_CONTEXT_MISMATCH = "assessment_context_mismatch"


@dataclass(frozen=True, slots=True)
class SelectionRequest:
    """Declarative requirements for one capability operation.

    ``objective`` is retained as request context for future intelligent rankers;
    this deterministic selector does not infer semantic relevance from prose.
    """

    operation_id: str
    objective: str | None = None
    context_ref: str | None = None
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
        if self.objective is not None and (
            not isinstance(self.objective, str) or not self.objective.strip()
        ):
            raise ValueError("objective must be a non-empty string when provided")
        if self.context_ref is not None and (
            not isinstance(self.context_ref, str) or not self.context_ref.strip()
        ):
            raise ValueError("context_ref must be a non-empty string when provided")
        if type(self.allow_degraded) is not bool:
            raise TypeError("allow_degraded must be a bool")
        if self.max_results is not None and (
            type(self.max_results) is not int or self.max_results < 1
        ):
            raise ValueError("max_results must be a positive integer")
        if not isinstance(self.categories, tuple) or not all(
            isinstance(item, CapabilityCategory) for item in self.categories
        ):
            raise TypeError("categories must be a tuple of CapabilityCategory values")
        if not isinstance(self.interface_kinds, tuple) or not all(
            isinstance(item, InterfaceKind) for item in self.interface_kinds
        ):
            raise TypeError("interface_kinds must be a tuple of InterfaceKind values")
        for field_name, values in (
            ("required_tags", self.required_tags),
            ("allowed_providers", self.allowed_providers),
            ("excluded_providers", self.excluded_providers),
            ("preferred_providers", self.preferred_providers),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"{field_name} must be a tuple of non-empty strings")
            if not all(isinstance(value, str) and value.strip() for value in values):
                raise ValueError(f"{field_name} must contain non-empty strings")


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
        selected: list[tuple[CapabilityDescriptor, CapabilityAssessment]] = []
        approval: list[tuple[CapabilityDescriptor, CapabilityAssessment]] = []
        rejected: list[RejectedCapability] = []

        for capability in inventory.capabilities:
            reason = self._static_rejection(capability, request)
            if reason is not None:
                rejected.append(RejectedCapability(capability.id, reason[0], reason[1]))
                continue

            assessment, context_mismatch = self._assessment_for(
                inventory.assessments, capability.id, request
            )
            if assessment is None:
                code = (
                    RejectionCode.ASSESSMENT_CONTEXT_MISMATCH
                    if context_mismatch
                    else RejectionCode.ASSESSMENT_MISSING
                )
                explanation = (
                    "Assessments exist, but none match the requested context."
                    if context_mismatch
                    else "No assessment exists for this capability operation."
                )
                rejected.append(RejectedCapability(capability.id, code, explanation))
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

    @classmethod
    def _assessment_for(
        cls,
        assessments: tuple[CapabilityAssessment, ...],
        capability_id: str,
        request: SelectionRequest,
    ) -> tuple[CapabilityAssessment | None, bool]:
        """Choose the newest assessment in the requested context.

        Context-free assessments are reusable defaults. Context-bound
        assessments are considered only for an exact context match; they are
        never borrowed by another session. Operation-specific assessments
        take precedence over capability-wide assessments within that scope.
        """
        candidates = [
            item for item in assessments
            if item.capability_id == capability_id
        ]
        if not candidates:
            return None, False

        # An assessment for another operation is never evidence for this one.
        applicable = [
            item for item in candidates
            if item.operation_id is None or item.operation_id == request.operation_id
        ]
        if not applicable:
            return None, False

        scoped = [
            item for item in applicable
            if item.context_ref is None or item.context_ref == request.context_ref
        ]
        if not scoped:
            return None, True

        # Specificity is ordered deliberately: operation-specific first, then
        # context-specific. Within an equal scope, newest wins; equal timestamps
        # resolve conservatively using the safety key.
        scoped.sort(
            key=lambda item: (
                item.operation_id == request.operation_id,
                item.context_ref is not None,
                item.assessed_at,
                cls._assessment_safety_key(item),
            ),
            reverse=True,
        )
        return scoped[0], False

    @staticmethod
    def _assessment_safety_key(
        assessment: CapabilityAssessment,
    ) -> tuple[int, int, str, str]:
        availability_risk = {
            Availability.AVAILABLE: 0,
            Availability.DEGRADED: 1,
            Availability.UNKNOWN: 2,
            Availability.UNAVAILABLE: 3,
        }[assessment.availability]
        authorization_risk = {
            Authorization.ALLOWED: 0,
            Authorization.UNKNOWN: 1,
            Authorization.REQUIRES_APPROVAL: 2,
            Authorization.DENIED: 3,
        }[assessment.authorization]
        return (
            availability_risk,
            authorization_risk,
            assessment.evidence or "",
            assessment.context_ref or "",
        )

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
