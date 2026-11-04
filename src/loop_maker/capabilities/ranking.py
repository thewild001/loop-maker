"""Optional intelligent ranking constrained by deterministic selection.

Rankers may reorder eligible candidates only. They cannot add candidates,
change assessments, authorize operations, resolve bindings, or invoke tools.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol, Sequence

from .models import CapabilityCategory, CapabilityInventory, InterfaceKind
from .selection import (
    DeterministicCapabilitySelector,
    SelectedCapability,
    SelectionRequest,
    SelectionResult,
)


@dataclass(frozen=True, slots=True)
class RankingContext:
    """Minimal request context exposed to an optional ranker."""

    operation_id: str
    objective: str | None


@dataclass(frozen=True, slots=True)
class RankingCandidate:
    """Sanitized candidate view; assessment evidence and arbitrary metadata are excluded."""

    capability_id: str
    name: str
    description: str
    category: CapabilityCategory
    provider_id: str
    interface_kind: InterfaceKind
    operation_id: str
    operation_description: str
    tags: tuple[str, ...]


class CapabilityRanker(Protocol):
    """Order candidate IDs by relevance; implementations must not execute them."""

    def rank(
        self,
        context: RankingContext,
        candidates: tuple[RankingCandidate, ...],
    ) -> Sequence[str]:
        """Return every candidate ID exactly once, in preferred order."""
        ...


class CapabilityRankingPipeline:
    """Apply optional intelligent ordering after mandatory deterministic gates.

    Any ranker exception or malformed ordering falls back to the deterministic
    order. The ranker is deliberately not given assessments, context references,
    arbitrary metadata, or the ability to alter candidate eligibility.
    """

    def __init__(
        self,
        selector: DeterministicCapabilitySelector | None = None,
        ranker: CapabilityRanker | None = None,
    ) -> None:
        self._selector = selector or DeterministicCapabilitySelector()
        self._ranker = ranker

    def select(
        self,
        inventory: CapabilityInventory,
        request: SelectionRequest,
    ) -> SelectionResult:
        # Rank the full eligible set first; max_results is applied afterwards.
        deterministic = self._selector.select(
            inventory, request, apply_limit=False
        )
        if not deterministic.selected or self._ranker is None:
            return self._limit(deterministic, request.max_results)

        candidates = tuple(
            self._candidate(item) for item in deterministic.selected
        )
        try:
            ordered_ids = self._ranker.rank(
                RankingContext(
                    operation_id=request.operation_id,
                    objective=request.objective,
                ),
                candidates,
            )
            ordered = self._validate_order(
                ordered_ids,
                tuple(item.capability.id for item in deterministic.selected),
            )
        except Exception:
            # Ranking is an optimization, never a dependency or a policy gate.
            return self._limit(deterministic, request.max_results)

        by_id = {item.capability.id: item for item in deterministic.selected}
        ranked = tuple(
            replace(by_id[capability_id], rank=index)
            for index, capability_id in enumerate(ordered, start=1)
        )
        return SelectionResult(
            selected=ranked[:request.max_results],
            approval_required=deterministic.approval_required,
            rejected=deterministic.rejected,
        )

    @staticmethod
    def _candidate(item: SelectedCapability) -> RankingCandidate:
        capability = item.capability
        operation = next(
            operation
            for operation in capability.operations
            if operation.id == item.operation_id
        )
        return RankingCandidate(
            capability_id=capability.id,
            name=capability.name,
            description=capability.description,
            category=capability.category,
            provider_id=capability.source.provider_id,
            interface_kind=capability.interface.kind,
            operation_id=operation.id,
            operation_description=operation.description,
            tags=capability.constraints.tags,
        )

    @staticmethod
    def _validate_order(
        proposed: Sequence[str],
        eligible_ids: tuple[str, ...],
    ) -> tuple[str, ...]:
        if not isinstance(proposed, (tuple, list)):
            raise ValueError("ranker output must be a tuple or list of IDs")
        if not all(isinstance(item, str) and item for item in proposed):
            raise ValueError("ranker output contains an invalid capability ID")
        ordered = tuple(proposed)
        if len(ordered) != len(eligible_ids):
            raise ValueError("ranker must return every eligible candidate exactly once")
        if len(set(ordered)) != len(ordered):
            raise ValueError("ranker output contains duplicate IDs")
        if set(ordered) != set(eligible_ids):
            raise ValueError("ranker output must be a permutation of eligible IDs")
        return ordered

    @staticmethod
    def _limit(
        result: SelectionResult,
        max_results: int | None,
    ) -> SelectionResult:
        selected = result.selected if max_results is None else result.selected[:max_results]
        ranked = tuple(
            replace(item, rank=index)
            for index, item in enumerate(selected, start=1)
        )
        return SelectionResult(
            selected=ranked,
            approval_required=result.approval_required,
            rejected=result.rejected,
        )
