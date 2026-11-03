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
    DiscoveryError,
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
    with pytest.raises(ValueError, match="source provider"):
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
