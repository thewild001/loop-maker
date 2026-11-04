"""Hybrid capability discovery orchestration.

The host inventory is always queried first. Supplemental providers run only
when explicitly allowed in the discovery context.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import (
    CapabilityAssessment,
    CapabilityCategory,
    CapabilityDescriptor,
    CapabilityInterface,
    CapabilityInventory,
    CapabilityOperation,
    CapabilityProvider,
    CapabilitySource,
    DiscoveryContext,
    DiscoveryError,
    InterfaceKind,
    ProviderDiscoveryResult,
    ProviderStatus,
)


class HostInventoryProvider:
    """Expose descriptors explicitly supplied by the host integration."""

    def __init__(
        self,
        capabilities: Sequence[CapabilityDescriptor] = (),
        assessments: Sequence[CapabilityAssessment] = (),
        provider_id: str = "host.inventory",
    ) -> None:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")
        self._provider_id = provider_id
        self._capabilities = tuple(capabilities)
        self._assessments = tuple(assessments)

    @property
    def provider_id(self) -> str:
        return self._provider_id

    async def discover(self, context: DiscoveryContext) -> ProviderDiscoveryResult:
        del context
        return ProviderDiscoveryResult(
            provider_id=self.provider_id,
            capabilities=self._capabilities,
            assessments=self._assessments,
        )


class EntryPointAdapterProvider:
    """Project already-loaded, trusted AgentAdapters into capability descriptors.

    This provider does not load Python entry points. The caller must pass
    adapters obtained through the existing trusted plugin-loading mechanism.
    """

    def __init__(
        self,
        adapters: Mapping[str, Any],
        provider_id: str = "python.entry_points",
    ) -> None:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")
        self._provider_id = provider_id
        self._adapters = dict(adapters)

    @property
    def provider_id(self) -> str:
        return self._provider_id

    async def discover(self, context: DiscoveryContext) -> ProviderDiscoveryResult:
        del context
        capabilities: list[CapabilityDescriptor] = []
        errors: list[DiscoveryError] = []

        for entry_point_name, adapter in sorted(self._adapters.items()):
            try:
                agent_id = getattr(adapter, "agent_id", None)
                declared = adapter.capabilities()
                if not isinstance(agent_id, str) or not agent_id.strip():
                    raise ValueError("agent_id must be a non-empty string")
                if not callable(getattr(adapter, "execute", None)):
                    raise ValueError("execute(task, context) is required")
                if not callable(getattr(adapter, "capabilities", None)):
                    raise ValueError("capabilities() is required")
                if not isinstance(declared, dict):
                    raise ValueError("capabilities() must return a dictionary")
            except Exception as exc:
                errors.append(DiscoveryError(
                    code="adapter_contract_invalid",
                    message=(
                        f"Adapter '{entry_point_name}' could not be normalized "
                        f"({type(exc).__name__})."
                    ),
                ))
                continue

            capabilities.append(CapabilityDescriptor(
                id=f"agent:{self.provider_id}:{entry_point_name}",
                name=agent_id,
                description=f"Delegated agent adapter '{agent_id}'.",
                category=CapabilityCategory.AGENT,
                source=CapabilitySource(
                    provider_id=self.provider_id,
                    source_type="python_entry_point",
                    native_id=entry_point_name,
                ),
                interface=CapabilityInterface(
                    kind=InterfaceKind.DELEGATED_AGENT,
                    reference=agent_id,
                ),
                operations=(CapabilityOperation(
                    id="execute",
                    description="Execute a bounded task through this trusted adapter.",
                ),),
                metadata={"agent_id": agent_id, "legacy_capabilities": declared},
            ))

        if errors and capabilities:
            status = ProviderStatus.PARTIAL
        elif errors:
            status = ProviderStatus.FAILED
        else:
            status = ProviderStatus.SUCCESS

        return ProviderDiscoveryResult(
            provider_id=self.provider_id,
            capabilities=tuple(capabilities),
            status=status,
            complete=not errors,
            errors=tuple(errors),
        )


class CapabilityDiscovery:
    """Coordinate host-first discovery and explicitly allowed supplements."""

    def __init__(
        self,
        host_provider: CapabilityProvider,
        supplemental_providers: Sequence[CapabilityProvider] = (),
    ) -> None:
        providers = (host_provider, *supplemental_providers)
        provider_ids = [provider.provider_id for provider in providers]
        if len(provider_ids) != len(set(provider_ids)):
            raise ValueError("provider IDs must be unique")
        self._host_provider = host_provider
        self._supplemental_providers = tuple(supplemental_providers)

    async def discover(self, context: DiscoveryContext) -> CapabilityInventory:
        selected_providers = [self._host_provider]
        allowed = set(context.allowed_providers)
        selected_providers.extend(
            provider for provider in self._supplemental_providers
            if provider.provider_id in allowed
        )

        results: list[ProviderDiscoveryResult] = []
        for provider in selected_providers:
            try:
                result = await provider.discover(context)
                if result.provider_id != provider.provider_id:
                    raise ValueError("provider returned a mismatched provider_id")
            except Exception as exc:
                result = ProviderDiscoveryResult(
                    provider_id=provider.provider_id,
                    status=ProviderStatus.FAILED,
                    complete=False,
                    errors=(DiscoveryError(
                        code="provider_discovery_failed",
                        message=f"Provider failed ({type(exc).__name__}).",
                    ),),
                )
            results.append(result)

        capabilities = tuple(
            capability
            for result in results
            for capability in result.capabilities
        )
        assessments = tuple(
            assessment
            for result in results
            for assessment in result.assessments
        )
        return CapabilityInventory(
            capabilities=capabilities,
            assessments=assessments,
            provider_results=tuple(results),
        )
