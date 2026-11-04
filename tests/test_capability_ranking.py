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
from loop_maker.capabilities.ranking import (
    CapabilityRankingPipeline,
    RankingCandidate,
)
from loop_maker.capabilities.selection import SelectionRequest


def make_capability(capability_id, name):
    return CapabilityDescriptor(
        id=capability_id,
        name=name,
        description=f"{name} capability.",
        category=CapabilityCategory.TOOL,
        source=CapabilitySource("host.native", "host", capability_id),
        interface=CapabilityInterface(InterfaceKind.NATIVE, capability_id),
        operations=(CapabilityOperation("search", "Search"),),
        constraints=CapabilityConstraints(tags=("web",)),
        metadata={"private": "must not be sent to ranker"},
    )


def make_inventory():
    capabilities = (
        make_capability("a", "Alpha"),
        make_capability("b", "Beta"),
        make_capability("c", "Gamma"),
    )
    assessments = tuple(
        CapabilityAssessment(
            capability_id=item.id,
            operation_id="search",
            availability=Availability.AVAILABLE,
            authorization=Authorization.ALLOWED,
            evidence="sensitive evidence",
        )
        for item in capabilities
    )
    return CapabilityInventory(capabilities=capabilities, assessments=assessments)


class FixedRanker:
    def __init__(self, result):
        self.result = result
        self.context = None
        self.candidates = None

    def rank(self, context, candidates):
        self.context = context
        self.candidates = candidates
        return self.result


def test_ranker_reorders_only_deterministically_eligible_candidates():
    ranker = FixedRanker(["c", "a", "b"])
    result = CapabilityRankingPipeline(ranker=ranker).select(
        make_inventory(),
        SelectionRequest(operation_id="search", objective="Find authoritative sources"),
    )
    assert [item.capability.id for item in result.selected] == ["c", "a", "b"]
    assert [item.rank for item in result.selected] == [1, 2, 3]
    assert ranker.context.objective == "Find authoritative sources"
    assert all(isinstance(item, RankingCandidate) for item in ranker.candidates)
    assert not hasattr(ranker.candidates[0], "assessment")
    assert not hasattr(ranker.candidates[0], "metadata")


def test_max_results_is_applied_after_intelligent_ranking():
    ranker = FixedRanker(["c", "b", "a"])
    result = CapabilityRankingPipeline(ranker=ranker).select(
        make_inventory(),
        SelectionRequest(operation_id="search", max_results=2),
    )
    assert [item.capability.id for item in result.selected] == ["c", "b"]
    assert [item.rank for item in result.selected] == [1, 2]


@pytest.mark.parametrize(
    "bad_output",
    [
        ["a", "a", "c"],
        ["a", "b"],
        ["a", "b", "unknown"],
        ["a", "b", 3],
        "abc",
        None,
    ],
)
def test_invalid_ranker_output_falls_back_to_deterministic_order(bad_output):
    ranker = FixedRanker(bad_output)
    result = CapabilityRankingPipeline(ranker=ranker).select(
        make_inventory(), SelectionRequest(operation_id="search")
    )
    assert [item.capability.id for item in result.selected] == ["a", "b", "c"]


def test_ranker_exception_falls_back_to_deterministic_order():
    class BrokenRanker:
        def rank(self, context, candidates):
            raise RuntimeError("provider unavailable")

    result = CapabilityRankingPipeline(ranker=BrokenRanker()).select(
        make_inventory(), SelectionRequest(operation_id="search")
    )
    assert [item.capability.id for item in result.selected] == ["a", "b", "c"]


def test_no_ranker_uses_deterministic_order():
    result = CapabilityRankingPipeline().select(
        make_inventory(), SelectionRequest(operation_id="search")
    )
    assert [item.capability.id for item in result.selected] == ["a", "b", "c"]


def test_ranker_cannot_reintroduce_denied_candidates():
    inventory = make_inventory()
    denied = CapabilityAssessment(
        capability_id="c",
        operation_id="search",
        availability=Availability.AVAILABLE,
        authorization=Authorization.DENIED,
    )
    inventory = CapabilityInventory(
        capabilities=inventory.capabilities,
        assessments=(*inventory.assessments[:2], denied),
    )
    ranker = FixedRanker(["c", "b", "a"])
    result = CapabilityRankingPipeline(ranker=ranker).select(
        inventory, SelectionRequest(operation_id="search")
    )
    assert [item.capability.id for item in result.selected] == ["a", "b"]
