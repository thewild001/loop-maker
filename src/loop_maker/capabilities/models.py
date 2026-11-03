"""Typed, host-agnostic contracts for capability discovery.

These models describe capabilities and discovery assessments. They do not
authorize or execute capabilities; the host remains authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Protocol


class CapabilityCategory(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    SKILL = "skill"
    EVALUATOR = "evaluator"


class InterfaceKind(str, Enum):
    NATIVE = "native"
    MCP_TOOL = "mcp_tool"
    MCP_RESOURCE = "mcp_resource"
    MCP_PROMPT = "mcp_prompt"
    PYTHON_ENTRY_POINT = "python_entry_point"
    SKILL_ACTIVATION = "skill_activation"
    API = "api"
    DELEGATED_AGENT = "delegated_agent"


class Availability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class Authorization(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    REQUIRES_APPROVAL = "requires_approval"
    UNKNOWN = "unknown"


class ProviderStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_mapping(value: Mapping[str, Any] | None, field_name: str) -> None:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping or None")


@dataclass(frozen=True, slots=True)
class CapabilitySource:
    """Concrete origin of a descriptor; native IDs are provider-scoped."""

    provider_id: str
    source_type: str
    native_id: str
    provenance: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.provider_id, "provider_id")
        _require_text(self.source_type, "source_type")
        _require_text(self.native_id, "native_id")


@dataclass(frozen=True, slots=True)
class CapabilityInterface:
    """How the host can consume a capability; this is not an executor."""

    kind: InterfaceKind
    reference: str
    input_schema: Mapping[str, Any] | None = None
    output_schema: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, InterfaceKind):
            raise TypeError("kind must be an InterfaceKind")
        _require_text(self.reference, "reference")
        _require_mapping(self.input_schema, "input_schema")
        _require_mapping(self.output_schema, "output_schema")


@dataclass(frozen=True, slots=True)
class CapabilityOperation:
    id: str
    description: str
    input_schema: Mapping[str, Any] | None = None
    output_schema: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_text(self.id, "operation id")
        _require_text(self.description, "operation description")
        _require_mapping(self.input_schema, "input_schema")
        _require_mapping(self.output_schema, "output_schema")


@dataclass(frozen=True, slots=True)
class CapabilityConstraints:
    """Declarative constraints; enforcement remains with host/policy."""

    requirements: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for item in (*self.requirements, *self.tags):
            _require_text(item, "constraint item")


@dataclass(frozen=True, slots=True)
class CapabilityDescriptor:
    """Stable normalized descriptor, independent of runtime assessments."""

    id: str
    name: str
    description: str
    category: CapabilityCategory
    source: CapabilitySource
    interface: CapabilityInterface
    operations: tuple[CapabilityOperation, ...]
    constraints: CapabilityConstraints = field(default_factory=CapabilityConstraints)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.id, "capability id")
        _require_text(self.name, "capability name")
        _require_text(self.description, "capability description")
        if not isinstance(self.category, CapabilityCategory):
            raise TypeError("category must be a CapabilityCategory")
        if not isinstance(self.source, CapabilitySource):
            raise TypeError("source must be a CapabilitySource")
        if not isinstance(self.interface, CapabilityInterface):
            raise TypeError("interface must be a CapabilityInterface")
        if not isinstance(self.constraints, CapabilityConstraints):
            raise TypeError("constraints must be CapabilityConstraints")
        _require_mapping(self.metadata, "metadata")
        if not isinstance(self.operations, tuple) or not all(
            isinstance(operation, CapabilityOperation) for operation in self.operations
        ):
            raise TypeError("operations must be a tuple of CapabilityOperation")
        operation_ids = [operation.id for operation in self.operations]
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("operation IDs must be unique within a capability")


@dataclass(frozen=True, slots=True)
class CapabilityAssessment:
    """Time- and context-bound state; never treat UNKNOWN as permission."""

    capability_id: str
    availability: Availability
    authorization: Authorization
    operation_id: str | None = None
    assessed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context_ref: str | None = None
    evidence: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.capability_id, "capability_id")
        if not isinstance(self.availability, Availability):
            raise TypeError("availability must be an Availability")
        if not isinstance(self.authorization, Authorization):
            raise TypeError("authorization must be an Authorization")
        if self.operation_id is not None:
            _require_text(self.operation_id, "operation_id")
        if self.assessed_at.tzinfo is None or self.assessed_at.utcoffset() is None:
            raise ValueError("assessed_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class DiscoveryContext:
    """Explicit scope and allowlist for a discovery request."""

    objective: str | None = None
    requested_categories: tuple[CapabilityCategory, ...] = ()
    allowed_providers: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.objective is not None:
            _require_text(self.objective, "objective")
        if not all(isinstance(item, CapabilityCategory) for item in self.requested_categories):
            raise TypeError("requested_categories must contain CapabilityCategory values")
        for provider_id in self.allowed_providers:
            _require_text(provider_id, "allowed provider")
        _require_mapping(self.metadata, "metadata")


@dataclass(frozen=True, slots=True)
class DiscoveryError:
    code: str
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        _require_text(self.code, "error code")
        _require_text(self.message, "error message")


@dataclass(frozen=True, slots=True)
class ProviderDiscoveryResult:
    provider_id: str
    capabilities: tuple[CapabilityDescriptor, ...] = ()
    assessments: tuple[CapabilityAssessment, ...] = ()
    status: ProviderStatus = ProviderStatus.SUCCESS
    complete: bool = True
    errors: tuple[DiscoveryError, ...] = ()
    source_version: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.provider_id, "provider_id")
        if not isinstance(self.status, ProviderStatus):
            raise TypeError("status must be a ProviderStatus")
        if self.status is ProviderStatus.FAILED:
            if self.capabilities:
                raise ValueError("a failed provider result cannot contain capabilities")
            if not self.errors or self.complete:
                raise ValueError("a failed provider result must be incomplete and explain its errors")
        if self.status is ProviderStatus.PARTIAL and (not self.errors or self.complete):
            raise ValueError("a partial provider result must be incomplete and explain its errors")
        if self.status is ProviderStatus.SUCCESS and (self.errors or not self.complete):
            raise ValueError("a successful provider result must be complete and contain no errors")
        if any(item.source.provider_id != self.provider_id for item in self.capabilities):
            raise ValueError("all capabilities must identify the result provider as their source")
        capability_map = {item.id: item for item in self.capabilities}
        for assessment in self.assessments:
            capability = capability_map.get(assessment.capability_id)
            if capability is None:
                raise ValueError("provider assessment references an unknown capability")
            if (assessment.operation_id is not None
                    and assessment.operation_id not in {op.id for op in capability.operations}):
                raise ValueError("provider assessment references an unknown operation")


@dataclass(frozen=True, slots=True)
class CapabilityInventory:
    """Request-scoped snapshot; persistence and caching are deliberately absent."""

    capabilities: tuple[CapabilityDescriptor, ...] = ()
    assessments: tuple[CapabilityAssessment, ...] = ()
    provider_results: tuple[ProviderDiscoveryResult, ...] = ()

    def __post_init__(self) -> None:
        if not all(isinstance(item, CapabilityDescriptor) for item in self.capabilities):
            raise TypeError("capabilities must contain CapabilityDescriptor values")
        if not all(isinstance(item, CapabilityAssessment) for item in self.assessments):
            raise TypeError("assessments must contain CapabilityAssessment values")
        if not all(isinstance(item, ProviderDiscoveryResult) for item in self.provider_results):
            raise TypeError("provider_results must contain ProviderDiscoveryResult values")
        capability_ids = [item.id for item in self.capabilities]
        if len(capability_ids) != len(set(capability_ids)):
            raise ValueError("capability IDs must be unique within an inventory")
        provider_ids = [item.provider_id for item in self.provider_results]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("provider IDs must be unique within an inventory")
        known_ids = set(capability_ids)
        operations_by_capability = {
            item.id: {operation.id for operation in item.operations}
            for item in self.capabilities
        }
        for assessment in self.assessments:
            if assessment.capability_id not in known_ids:
                raise ValueError("assessment references an unknown capability")
            if (assessment.operation_id is not None
                    and assessment.operation_id not in operations_by_capability[assessment.capability_id]):
                raise ValueError("assessment references an unknown operation")


class CapabilityProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    async def discover(
        self, context: DiscoveryContext
    ) -> ProviderDiscoveryResult: ...
