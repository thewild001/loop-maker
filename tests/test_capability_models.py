import pytest

from loop_maker.capabilities.models import (
    Authorization,
    Availability,
    CapabilityAssessment,
    CapabilityCategory,
    CapabilityDescriptor,
    CapabilityInterface,
    CapabilityInventory,
    CapabilityOperation,
    CapabilitySource,
    InterfaceKind,
    ProviderDiscoveryResult,
    ProviderStatus,
)


def make_capability(capability_id="github.search", provider_id="host.native"):
    return CapabilityDescriptor(
        id=capability_id,
        name="Search repositories",
        description="Search repositories using the host integration.",
        category=CapabilityCategory.TOOL,
        source=CapabilitySource(provider_id, "host", "search_repositories"),
        interface=CapabilityInterface(InterfaceKind.NATIVE, "github.search"),
        operations=(CapabilityOperation("search", "Search repositories"),),
    )


def test_descriptor_keeps_category_separate_from_interface():
    capability = make_capability()
    assert capability.category is CapabilityCategory.TOOL
    assert capability.interface.kind is InterfaceKind.NATIVE


def test_source_identity_is_provider_scoped():
    first = make_capability(provider_id="host.one")
    second = make_capability(provider_id="host.two")
    assert first.id == second.id
    assert first.source != second.source


def test_duplicate_operation_ids_are_rejected():
    with pytest.raises(ValueError, match="operation IDs"):
        CapabilityDescriptor(
            id="tool.one",
            name="Tool",
            description="A tool",
            category=CapabilityCategory.TOOL,
            source=CapabilitySource("host", "native", "tool.one"),
            interface=CapabilityInterface(InterfaceKind.NATIVE, "tool.one"),
            operations=(
                CapabilityOperation("run", "Run"),
                CapabilityOperation("run", "Run again"),
            ),
        )


def test_assessment_requires_timezone_aware_timestamp():
    from datetime import datetime

    with pytest.raises(ValueError, match="timezone-aware"):
        CapabilityAssessment(
            capability_id="github.search",
            availability=Availability.AVAILABLE,
            authorization=Authorization.ALLOWED,
            assessed_at=datetime(2026, 1, 1),
        )


def test_unknown_authorization_is_explicit_not_allowed():
    assessment = CapabilityAssessment(
        capability_id="github.search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.UNKNOWN,
    )
    assert assessment.authorization is Authorization.UNKNOWN


def test_partial_provider_result_requires_error_details():
    with pytest.raises(ValueError, match="explain its errors"):
        ProviderDiscoveryResult(
            provider_id="host.native",
            status=ProviderStatus.PARTIAL,
            complete=False,
        )


def test_provider_result_rejects_foreign_source():
    with pytest.raises(ValueError, match="result provider as their source"):
        ProviderDiscoveryResult(
            provider_id="host.native",
            capabilities=(make_capability(provider_id="other.provider"),),
        )


def test_inventory_rejects_duplicate_normalized_ids():
    with pytest.raises(ValueError, match="unique"):
        CapabilityInventory(capabilities=(
            make_capability(provider_id="host.one"),
            make_capability(provider_id="host.two"),
        ))


def test_inventory_rejects_assessment_for_unknown_operation():
    with pytest.raises(ValueError, match="unknown operation"):
        CapabilityInventory(
            capabilities=(make_capability(),),
            assessments=(CapabilityAssessment(
                capability_id="github.search",
                operation_id="delete",
                availability=Availability.AVAILABLE,
                authorization=Authorization.ALLOWED,
            ),),
        )


def test_inventory_accepts_valid_descriptor_and_assessment():
    capability = make_capability()
    assessment = CapabilityAssessment(
        capability_id=capability.id,
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
    )
    inventory = CapabilityInventory(
        capabilities=(capability,),
        assessments=(assessment,),
    )
    assert inventory.capabilities == (capability,)
    assert inventory.assessments == (assessment,)


def test_failed_provider_cannot_return_capabilities():
    with pytest.raises(ValueError, match="cannot contain capabilities"):
        ProviderDiscoveryResult(
            provider_id="host.native",
            capabilities=(make_capability(),),
            status=ProviderStatus.FAILED,
        )


def test_assessment_cannot_reference_unknown_capability():
    with pytest.raises(ValueError, match="unknown capability"):
        CapabilityInventory(assessments=(CapabilityAssessment(
            capability_id="missing",
            availability=Availability.UNKNOWN,
            authorization=Authorization.UNKNOWN,
        ),))


@pytest.mark.asyncio
async def test_host_inventory_is_always_discovered():
    from loop_maker.capabilities.discovery import CapabilityDiscovery, HostInventoryProvider
    from loop_maker.capabilities.models import DiscoveryContext

    capability = make_capability(provider_id="host.inventory")
    inventory = await CapabilityDiscovery(
        HostInventoryProvider((capability,))
    ).discover(DiscoveryContext())
    assert [item.id for item in inventory.capabilities] == [capability.id]


@pytest.mark.asyncio
async def test_supplemental_provider_requires_explicit_allowlist():
    from loop_maker.capabilities.discovery import CapabilityDiscovery, HostInventoryProvider
    from loop_maker.capabilities.models import DiscoveryContext

    supplemental = make_capability(
        capability_id="agent:extra:research",
        provider_id="extra",
    )
    class SupplementalProvider:
        provider_id = "extra"

        async def discover(self, context):
            return ProviderDiscoveryResult(
                provider_id=self.provider_id,
                capabilities=(supplemental,),
            )

    discovery = CapabilityDiscovery(
        HostInventoryProvider(),
        (SupplementalProvider(),),
    )
    without_permission = await discovery.discover(DiscoveryContext())
    with_permission = await discovery.discover(
        DiscoveryContext(allowed_providers=("extra",))
    )
    assert not without_permission.capabilities
    assert [item.id for item in with_permission.capabilities] == [supplemental.id]


@pytest.mark.asyncio
async def test_provider_failure_does_not_discard_host_inventory():
    from loop_maker.capabilities.discovery import CapabilityDiscovery, HostInventoryProvider
    from loop_maker.capabilities.models import DiscoveryContext

    host_capability = make_capability(provider_id="host.inventory")
    class BrokenProvider:
        provider_id = "broken"

        async def discover(self, context):
            raise RuntimeError("internal details must not leak")

    inventory = await CapabilityDiscovery(
        HostInventoryProvider((host_capability,)),
        (BrokenProvider(),),
    ).discover(DiscoveryContext(allowed_providers=("broken",)))
    assert [item.id for item in inventory.capabilities] == [host_capability.id]
    assert inventory.provider_results[1].status is ProviderStatus.FAILED
    assert "internal details" not in inventory.provider_results[1].errors[0].message


@pytest.mark.asyncio
async def test_entry_point_provider_normalizes_existing_adapter_without_loading_plugins():
    from loop_maker.capabilities.discovery import EntryPointAdapterProvider
    from loop_maker.capabilities.models import DiscoveryContext

    class ExistingAdapter:
        agent_id = "research-agent"

        def capabilities(self):
            return {"web_search": True}

        async def execute(self, task, context):
            raise AssertionError("discovery must never execute an adapter")

    result = await EntryPointAdapterProvider(
        {"research": ExistingAdapter()}
    ).discover(DiscoveryContext())
    assert result.status is ProviderStatus.SUCCESS
    descriptor = result.capabilities[0]
    assert descriptor.category is CapabilityCategory.AGENT
    assert descriptor.interface.kind is InterfaceKind.DELEGATED_AGENT
    assert descriptor.metadata["legacy_capabilities"] == {"web_search": True}


@pytest.mark.asyncio
async def test_entry_point_provider_reports_invalid_adapter_partially():
    from loop_maker.capabilities.discovery import EntryPointAdapterProvider
    from loop_maker.capabilities.models import DiscoveryContext

    class InvalidAdapter:
        agent_id = "broken"

        def capabilities(self):
            return []

    result = await EntryPointAdapterProvider(
        {"broken": InvalidAdapter()}
    ).discover(DiscoveryContext())
    assert result.status is ProviderStatus.FAILED
    assert result.complete is False
    assert result.errors[0].code == "adapter_contract_invalid"
