from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from tools.noema_qhtri_semantic_autonomy_v01 import (
    SemanticAutonomyError,
    build_autonomous_feedback_execution_receipt,
    validate_autonomous_feedback_execution_receipt,
    validate_semantic_autonomy_capability,
)


@dataclass(frozen=True)
class AutonomyEpochSnapshot:
    capability_sha256: str
    capability_epoch: int
    next_effect_index: int
    consumed_effects: int


class SemanticAutonomyEpoch:
    """Stateful fail-closed allocator for bounded L1 internal effects.

    The caller never chooses an effect index. The epoch owns the monotonic
    counter and advances it only after a valid execution receipt has been
    built and revalidated against the same capability.
    """

    def __init__(self, capability: Mapping[str, Any], *, next_effect_index: int = 0) -> None:
        validate_semantic_autonomy_capability(capability)
        if isinstance(next_effect_index, bool):
            raise SemanticAutonomyError("next_effect_index must be an integer")
        try:
            index = int(next_effect_index)
        except (TypeError, ValueError) as exc:
            raise SemanticAutonomyError("next_effect_index must be an integer") from exc
        if index != next_effect_index or index < 0:
            raise SemanticAutonomyError("next_effect_index must be non-negative")
        if index > capability["max_internal_effects_per_epoch"]:
            raise SemanticAutonomyError("next_effect_index exceeds capability budget")
        self._capability = dict(capability)
        self._next_effect_index = index

    @property
    def next_effect_index(self) -> int:
        return self._next_effect_index

    @property
    def capability_sha256(self) -> str:
        return self._capability["capability_sha256"]

    def snapshot(self) -> AutonomyEpochSnapshot:
        return AutonomyEpochSnapshot(
            capability_sha256=self._capability["capability_sha256"],
            capability_epoch=int(self._capability["capability_epoch"]),
            next_effect_index=self._next_effect_index,
            consumed_effects=self._next_effect_index,
        )

    def execute_feedback(
        self,
        feedback_receipt: Mapping[str, Any],
        *,
        operator_class: str,
        current_tick: int,
        estimated_memory_bytes: int = 0,
        estimated_energy_proxy: float = 0.0,
        state_memory_append: bool = False,
    ) -> dict[str, Any]:
        if self._next_effect_index >= self._capability["max_internal_effects_per_epoch"]:
            raise SemanticAutonomyError("bounded autonomy epoch effect budget exhausted")

        effect_index = self._next_effect_index
        receipt = build_autonomous_feedback_execution_receipt(
            feedback_receipt,
            self._capability,
            operator_class=operator_class,
            current_tick=current_tick,
            effect_index=effect_index,
            estimated_memory_bytes=estimated_memory_bytes,
            estimated_energy_proxy=estimated_energy_proxy,
            state_memory_append=state_memory_append,
        )
        validate_autonomous_feedback_execution_receipt(
            receipt,
            feedback_receipt=feedback_receipt,
            capability=self._capability,
        )
        if receipt["effect_index"] != effect_index:
            raise SemanticAutonomyError("autonomy epoch effect index mismatch")

        self._next_effect_index += 1
        return receipt

    def admit_replayed_receipt(
        self,
        receipt: Mapping[str, Any],
        *,
        feedback_receipt: Mapping[str, Any],
    ) -> None:
        """Advance recovery state only for the exact next receipt.

        This is intended for append-only State Memory/PNFS replay. Duplicate,
        stale, or out-of-order receipts fail closed.
        """
        validate_autonomous_feedback_execution_receipt(
            receipt,
            feedback_receipt=feedback_receipt,
            capability=self._capability,
        )
        if receipt["effect_index"] != self._next_effect_index:
            raise SemanticAutonomyError(
                f"autonomy replay order mismatch: {receipt['effect_index']} != {self._next_effect_index}"
            )
        self._next_effect_index += 1
