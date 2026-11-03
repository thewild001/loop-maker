import pytest

from loop_maker.capabilities.discovery import (
    CapabilityDiscovery,
    EntryPointAdapterProvider,
    HostInventoryProvider,
)
from loop_maker.capabilities.models import (
    Authorization,
    Availability,
    CapabilityAssessment,
    CapabilityCategory,
    CapabilityDescriptor,
    CapabilityInterface,
    CapabilityOperation,
    CapabilitySource,
    DiscoveryContext,
    InterfaceKind,
    ProviderDiscoveryResult,
    ProviderStatus,
)


def make_capability(capability_id="host.search", provider_id="host.inventory"):
    return CapabilityDescriptor(
        id=capability_id,
        name="Search",
        description="Search through the host.",
        category=CapabilityCategory.TOOL,
        source=CapabilitySource(provider_id, "native", "search"),
        interface=CapabilityInterface(InterfaceKind.NATIVE, "search"),
        operations=(CapabilityOperation("run", "Run search"),),
    )


class RecordingProvider:
    def __init__(self, provider_id, result=None, error=None):
        self.provider_id = provider_id
        self.result = result
        self.error = error
        self.calls = 0

    async def discover(self, context):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


@pytest.mark.asyncio
async def test_host_inventory_is_always_discovered():
    host_capability = make_capability()
    host = HostInventoryProvider(capabilities=(host_capability,))
    supplemental = RecordingProvider("supplemental")

    inventory = await CapabilityDiscovery(
        host_provider=host,
        supplemental_providers=(supplemental,),
    ).discover(DiscoveryContext())

    assert [item.id for item in inventory.capabilities] == ["host.search"]
    assert len(inventory.provider_results) == 1
    assert supplemental.calls == 0


@pytest.mark.asyncio
async def test_only_explicitly_allowed_supplemental_providers_are_queried():
    host = HostInventoryProvider()
    supplemental_capability = make_capability(
        capability_id="extra.search",
        provider_id="supplemental",
    )
    supplemental = RecordingProvider(
        "supplemental",
        ProviderDiscoveryResult(
            provider_id="supplemental",
            capabilities=(supplemental_capability,),
        ),
    )

    inventory = await CapabilityDiscovery(
        host_provider=host,
        supplemental_providers=(supplemental,),
    ).discover(DiscoveryContext(allowed_providers=("supplemental",)))

    assert supplemental.calls == 1
    assert [item.id for item in inventory.capabilities] == ["extra.search"]


@pytest.mark.asyncio
async def test_supplemental_provider_failure_does_not_discard_host_inventory():
    host_capability = make_capability()
    host = HostInventoryProvider(capabilities=(host_capability,))
    supplemental = RecordingProvider("supplemental", error=RuntimeError("sensitive detail"))

    inventory = await CapabilityDiscovery(
        host_provider=host,
        supplemental_providers=(supplemental,),
    ).discover(DiscoveryContext(allowed_providers=("supplemental",)))

    assert [item.id for item in inventory.capabilities] == ["host.search"]
    failed = inventory.provider_results[1]
    assert failed.status is ProviderStatus.FAILED
    assert failed.errors[0].code == "provider_discovery_failed"
    assert "sensitive detail" not in failed.errors[0].message


@pytest.mark.asyncio
async def test_host_assessments_are_preserved_in_inventory():
    capability = make_capability()
    assessment = CapabilityAssessment(
        capability_id=capability.id,
        operation_id="run",
        availability=Availability.AVAILABLE,
        authorization=Authorization.UNKNOWN,
    )
    inventory = await CapabilityDiscovery(
        host_provider=HostInventoryProvider(
            capabilities=(capability,),
            assessments=(assessment,),
        )
    ).discover(DiscoveryContext())

    assert inventory.assessments == (assessment,)
    assert inventory.assessments[0].authorization is Authorization.UNKNOWN


@pytest.mark.asyncio
async def test_entry_point_provider_projects_trusted_adapter_without_loading_plugins():
    class ExistingAdapter:
        agent_id = "existing-agent"

        def capabilities(self):
            return {"streaming": True}

        async def execute(self, task, context):
            raise NotImplementedError

    result = await EntryPointAdapterProvider(
        {"existing.entry": ExistingAdapter()}
    ).discover(DiscoveryContext())

    assert result.status is ProviderStatus.SUCCESS
    capability = result.capabilities[0]
    assert capability.category is CapabilityCategory.AGENT
    assert capability.interface.kind is InterfaceKind.DELEGATED_AGENT
    assert capability.source.native_id == "existing.entry"
    assert capability.metadata["legacy_capabilities"] == {"streaming": True}


@pytest.mark.asyncio
async def test_entry_point_provider_reports_invalid_adapter_without_aborting_other_adapters():
    class ValidAdapter:
        agent_id = "valid"

        def capabilities(self):
            return {}

        async def execute(self, task, context):
            raise NotImplementedError

    class InvalidAdapter:
        agent_id = "invalid"

        def capabilities(self):
            return {"declared": True}

    result = await EntryPointAdapterProvider({
        "a.invalid": InvalidAdapter(),
        "b.valid": ValidAdapter(),
    }).discover(DiscoveryContext())

    assert result.status is ProviderStatus.PARTIAL
    assert len(result.capabilities) == 1
    assert len(result.errors) == 1
    assert result.errors[0].code == "adapter_contract_invalid"
