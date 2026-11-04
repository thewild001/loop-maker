import pytest

from loop_maker.capabilities.models import (
    Authorization,
    Availability,
    CapabilityAssessment,
    CapabilityCategory,
    CapabilityConstraints,
    CapabilityDescriptor,
    CapabilityInterface,
    CapabilityInventory,
    CapabilityOperation,
    CapabilitySource,
    InterfaceKind,
)
from loop_maker.capabilities.selection import (
    DeterministicCapabilitySelector,
    RejectionCode,
    SelectionRequest,
)


def make_capability(
    capability_id="tool.search",
    provider_id="host.native",
    *,
    name="Search",
    tags=("web",),
    category=CapabilityCategory.TOOL,
    interface=InterfaceKind.NATIVE,
    operations=(CapabilityOperation("search", "Search"),),
):
    return CapabilityDescriptor(
        id=capability_id,
        name=name,
        description="Search capability.",
        category=category,
        source=CapabilitySource(provider_id, "host", capability_id),
        interface=CapabilityInterface(interface, capability_id),
        operations=operations,
        constraints=CapabilityConstraints(tags=tags),
    )


def assessment(
    capability_id,
    *,
    availability=Availability.AVAILABLE,
    authorization=Authorization.ALLOWED,
):
    return CapabilityAssessment(
        capability_id=capability_id,
        operation_id="search",
        availability=availability,
        authorization=authorization,
    )


def inventory_for(*capabilities, assessments=None):
    return CapabilityInventory(
        capabilities=tuple(capabilities),
        assessments=tuple(
            assessments if assessments is not None
            else [assessment(item.id) for item in capabilities]
        ),
    )


def test_selects_only_capabilities_matching_operation_and_policy():
    good = make_capability("good")
    wrong_operation = CapabilityDescriptor(
        id="wrong.operation",
        name="Other",
        description="Does not support search.",
        category=CapabilityCategory.TOOL,
        source=CapabilitySource("host.native", "host", "other"),
        interface=CapabilityInterface(InterfaceKind.NATIVE, "other"),
        operations=(CapabilityOperation("delete", "Delete"),),
    )
    denied = make_capability("denied")
    result = DeterministicCapabilitySelector().select(
        inventory_for(
            good,
            wrong_operation,
            denied,
            assessments=[
                assessment("good"),
                assessment("denied", authorization=Authorization.DENIED),
            ],
        ),
        SelectionRequest(operation_id="search"),
    )
    assert [item.capability.id for item in result.selected] == ["good"]
    assert {item.capability_id: item.code for item in result.rejected} == {
        "wrong.operation": RejectionCode.OPERATION_NOT_SUPPORTED,
        "denied": RejectionCode.ACCESS_DENIED,
    }


def test_unknown_availability_or_authorization_never_becomes_eligible():
    unknown_availability = make_capability("unknown.availability")
    unknown_authorization = make_capability("unknown.authorization")
    result = DeterministicCapabilitySelector().select(
        inventory_for(
            unknown_availability,
            unknown_authorization,
            assessments=[
                assessment("unknown.availability", availability=Availability.UNKNOWN),
                assessment("unknown.authorization", authorization=Authorization.UNKNOWN),
            ],
        ),
        SelectionRequest(operation_id="search"),
    )
    assert not result.selected
    assert {item.code for item in result.rejected} == {
        RejectionCode.AVAILABILITY_UNKNOWN,
        RejectionCode.AUTHORIZATION_UNKNOWN,
    }


def test_requires_approval_is_separated_from_selected_capabilities():
    capability = make_capability("approval")
    result = DeterministicCapabilitySelector().select(
        inventory_for(capability, assessments=[
            assessment("approval", authorization=Authorization.REQUIRES_APPROVAL)
        ]),
        SelectionRequest(operation_id="search"),
    )
    assert not result.selected
    assert [item.capability.id for item in result.approval_required] == ["approval"]
    assert "not an execution grant" in result.approval_required[0].reasons[0]


def test_degraded_availability_requires_explicit_opt_in():
    capability = make_capability("degraded")
    inventory = inventory_for(capability, assessments=[
        assessment("degraded", availability=Availability.DEGRADED)
    ])
    selector = DeterministicCapabilitySelector()
    denied = selector.select(inventory, SelectionRequest(operation_id="search"))
    allowed = selector.select(
        inventory, SelectionRequest(operation_id="search", allow_degraded=True)
    )
    assert denied.rejected[0].code is RejectionCode.DEGRADED_NOT_ALLOWED
    assert len(allowed.selected) == 1


def test_filters_apply_category_interface_provider_and_tags():
    candidates = (
        make_capability("eligible", provider_id="preferred"),
        make_capability("wrong.provider", provider_id="other"),
        make_capability("wrong.tag", tags=("local",)),
        make_capability("wrong.interface", interface=InterfaceKind.MCP_TOOL),
        make_capability("wrong.category", category=CapabilityCategory.AGENT),
    )
    result = DeterministicCapabilitySelector().select(
        inventory_for(*candidates),
        SelectionRequest(
            operation_id="search",
            categories=(CapabilityCategory.TOOL,),
            interface_kinds=(InterfaceKind.NATIVE,),
            required_tags=("web",),
            allowed_providers=("preferred", "other"),
            excluded_providers=("other",),
        ),
    )
    assert [item.capability.id for item in result.selected] == ["eligible"]
    assert len(result.rejected) == 4


def test_ranking_is_stable_and_uses_explicit_provider_preference():
    first = make_capability("zeta", provider_id="ordinary", name="Alpha")
    second = make_capability("beta", provider_id="preferred", name="Zulu")
    third = make_capability("alpha", provider_id="ordinary", name="Alpha")
    selector = DeterministicCapabilitySelector()
    request = SelectionRequest(
        operation_id="search", preferred_providers=("preferred",)
    )
    expected = ["beta", "alpha", "zeta"]
    for _ in range(3):
        result = selector.select(inventory_for(first, second, third), request)
        assert [item.capability.id for item in result.selected] == expected
        assert [item.rank for item in result.selected] == [1, 2, 3]


def test_max_results_limits_selected_candidates_without_changing_rejections():
    first = make_capability("one", name="A")
    second = make_capability("two", name="B")
    third = make_capability("three", name="C")
    result = DeterministicCapabilitySelector().select(
        inventory_for(first, second, third),
        SelectionRequest(operation_id="search", max_results=2),
    )
    assert len(result.selected) == 2
    assert not result.rejected




def test_context_bound_assessments_are_never_reused_across_sessions():
    capability = make_capability("session-bound")
    foreign = CapabilityAssessment(
        capability_id="session-bound",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
        context_ref="session-A",
    )
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(capabilities=(capability,), assessments=(foreign,)),
        SelectionRequest(operation_id="search", context_ref="session-B"),
    )
    assert not result.selected
    assert result.rejected[0].code is RejectionCode.ASSESSMENT_CONTEXT_MISMATCH


def test_context_specific_assessment_takes_precedence_over_global_assessment():
    capability = make_capability("session-precedence")
    global_assessment = CapabilityAssessment(
        capability_id="session-precedence",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
    )
    session_assessment = CapabilityAssessment(
        capability_id="session-precedence",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.DENIED,
        context_ref="session-A",
    )
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(
            capabilities=(capability,),
            assessments=(global_assessment, session_assessment),
        ),
        SelectionRequest(operation_id="search", context_ref="session-A"),
    )
    assert not result.selected
    assert result.rejected[0].code is RejectionCode.ACCESS_DENIED


def test_context_bound_assessment_is_not_used_without_matching_request_context():
    capability = make_capability("no-context")
    scoped = CapabilityAssessment(
        capability_id="no-context",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
        context_ref="session-A",
    )
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(capabilities=(capability,), assessments=(scoped,)),
        SelectionRequest(operation_id="search"),
    )
    assert result.rejected[0].code is RejectionCode.ASSESSMENT_CONTEXT_MISMATCH


def test_missing_assessment_is_rejected_closed():
    capability = make_capability("unassessed")
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(capabilities=(capability,)),
        SelectionRequest(operation_id="search"),
    )
    assert result.rejected[0].code is RejectionCode.ASSESSMENT_MISSING


def test_request_validates_required_operation_and_limit():
    with pytest.raises(ValueError, match="operation_id"):
        SelectionRequest(operation_id=" ")
    with pytest.raises(ValueError, match="max_results"):
        SelectionRequest(operation_id="search", max_results=0)


def test_capability_wide_assessment_is_fallback_to_operation_specific_state():
    capability = make_capability("scoped")
    generic = CapabilityAssessment(
        capability_id="scoped",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
    )
    operation_specific = assessment(
        "scoped", authorization=Authorization.DENIED
    )
    selector = DeterministicCapabilitySelector()

    generic_result = selector.select(
        CapabilityInventory(capabilities=(capability,), assessments=(generic,)),
        SelectionRequest(operation_id="search"),
    )
    specific_result = selector.select(
        CapabilityInventory(
            capabilities=(capability,),
            assessments=(generic, operation_specific),
        ),
        SelectionRequest(operation_id="search"),
    )
    assert len(generic_result.selected) == 1
    assert specific_result.rejected[0].code is RejectionCode.ACCESS_DENIED



def test_conflicting_same_timestamp_assessments_resolve_conservatively():
    from datetime import datetime, timezone

    capability = make_capability("conflict")
    timestamp = datetime.now(timezone.utc)
    allowed = CapabilityAssessment(
        capability_id="conflict",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
        assessed_at=timestamp,
    )
    denied = CapabilityAssessment(
        capability_id="conflict",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.DENIED,
        assessed_at=timestamp,
    )
    selector = DeterministicCapabilitySelector()
    request = SelectionRequest(operation_id="search")

    for assessments in ((allowed, denied), (denied, allowed)):
        result = selector.select(
            CapabilityInventory(
                capabilities=(capability,), assessments=assessments
            ),
            request,
        )
        assert not result.selected
        assert result.rejected[0].code is RejectionCode.ACCESS_DENIED



def test_assessment_for_unrelated_operation_cannot_authorize_requested_operation():
    capability = make_capability(
        "cross-operation",
        operations=(
            CapabilityOperation("search", "Search"),
            CapabilityOperation("delete", "Delete"),
        ),
    )
    delete_assessment = CapabilityAssessment(
        capability_id="cross-operation",
        operation_id="delete",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
    )
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(
            capabilities=(capability,),
            assessments=(delete_assessment,),
        ),
        SelectionRequest(operation_id="search"),
    )
    assert not result.selected
    assert result.rejected[0].code is RejectionCode.ASSESSMENT_MISSING


def test_generic_assessment_is_used_when_only_other_operation_assessment_also_exists():
    capability = make_capability(
        "generic-fallback",
        operations=(
            CapabilityOperation("search", "Search"),
            CapabilityOperation("delete", "Delete"),
        ),
    )
    generic = CapabilityAssessment(
        capability_id="generic-fallback",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
    )
    unrelated = CapabilityAssessment(
        capability_id="generic-fallback",
        operation_id="delete",
        availability=Availability.AVAILABLE,
        authorization=Authorization.DENIED,
    )
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(
            capabilities=(capability,),
            assessments=(unrelated, generic),
        ),
        SelectionRequest(operation_id="search"),
    )
    assert len(result.selected) == 1
    assert result.selected[0].assessment is generic


def test_operation_specific_global_assessment_precedes_context_generic_assessment():
    capability = make_capability("scope-precedence")
    context_generic = CapabilityAssessment(
        capability_id="scope-precedence",
        availability=Availability.AVAILABLE,
        authorization=Authorization.ALLOWED,
        context_ref="session-A",
    )
    operation_global = CapabilityAssessment(
        capability_id="scope-precedence",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.DENIED,
    )
    result = DeterministicCapabilitySelector().select(
        CapabilityInventory(
            capabilities=(capability,),
            assessments=(context_generic, operation_global),
        ),
        SelectionRequest(operation_id="search", context_ref="session-A"),
    )
    assert not result.selected
    assert result.rejected[0].code is RejectionCode.ACCESS_DENIED


@pytest.mark.parametrize("value", [1.5, True, 0, -1])
def test_max_results_requires_a_strictly_positive_integer(value):
    with pytest.raises(ValueError, match="max_results"):
        SelectionRequest(operation_id="search", max_results=value)


def test_request_rejects_non_boolean_allow_degraded():
    with pytest.raises(TypeError, match="allow_degraded"):
        SelectionRequest(operation_id="search", allow_degraded="false")


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"categories": [CapabilityCategory.TOOL]}, TypeError),
        ({"categories": ("tool",)}, TypeError),
        ({"interface_kinds": [InterfaceKind.NATIVE]}, TypeError),
        ({"interface_kinds": ("native",)}, TypeError),
        ({"required_tags": "web"}, TypeError),
        ({"allowed_providers": "host.native"}, TypeError),
        ({"excluded_providers": ["host.native"]}, TypeError),
        ({"preferred_providers": "host.native"}, TypeError),
    ],
)
def test_request_rejects_invalid_collection_shapes_and_values(kwargs, error):
    with pytest.raises(error):
        SelectionRequest(operation_id="search", **kwargs)
