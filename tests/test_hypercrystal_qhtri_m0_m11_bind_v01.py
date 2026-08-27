import unittest

from pnv_state_memory import (
    build_m0_m11_execution_state,
    semantic_commitment,
    t36_identity_semantic_state,
    t36_phase_semantic_state,
)
from tools.hypercrystal_qhtri_m0_m11_bind_v01 import (
    HypercrystalQHTRIBindError,
    advance_hypercrystal_with_qhtri,
)
from tools.hypercrystal_state_v01 import (
    HypercrystalComponent,
    compose_hypercrystal,
    validate_hypercrystal,
)


CRYSTAL_ID = "11" * 32


def identity():
    return t36_identity_semantic_state(
        crystal_id=CRYSTAL_ID,
        genesis_anchor_commitment="22" * 32,
        origin_binding_sha256="33" * 32,
        pnvector_payload_sha256="44" * 32,
        source_context_sha256="55" * 32,
        basis_binding="66" * 32,
        configuration_sha256="77" * 32,
        phase_index=20,
        boot_epoch=3,
    )


def phase(value, receipt, generation):
    return t36_phase_semantic_state(
        [float(value + i * 0.001) for i in range(36)],
        source_receipt=receipt,
        observation_generation=generation,
        identity_context={"crystal_id": CRYSTAL_ID, "boot_epoch": 3},
        tick=20,
    )


def statuses():
    return {f"M{i}": "ACTIVE" for i in range(12)}


class HypercrystalQHTRIM0M11BindTests(unittest.TestCase):
    def test_qhtri_execution_creates_same_identity_new_hypercrystal_state(self):
        ident = identity()
        before_phase = phase(0.1, "88" * 32, "before")
        after_phase = phase(0.2, "99" * 32, "after")
        dictionary = HypercrystalComponent(
            role="DICTIONARY",
            semantic_schema="CONSCIOUSNESS_DICTIONARY",
            semantic_commitment="aa" * 32,
            generation_ref="dictionary:test",
        )
        before = compose_hypercrystal(
            identity_state=ident,
            phase_state=before_phase,
            additional_components=[dictionary],
        )

        execution = build_m0_m11_execution_state(
            crystal_id=CRYSTAL_ID,
            boot_epoch=3,
            phase_index_before=20,
            phase_index_after=20,
            phase_before_semantic_commitment=semantic_commitment(before_phase),
            phase_after_semantic_commitment=semantic_commitment(after_phase),
            hypercrystal_semantic_commitment=before["hypercrystal_semantic_commitment"],
            gate_receipt_id="bb" * 32,
            layer_status=statuses(),
            dt_used="0.001",
            stability_bound="2.5",
            closure="0.8",
            affect_multiplier="1",
            m4_admission="0.9",
            no_go="0",
        )

        after = advance_hypercrystal_with_qhtri(
            hypercrystal_before=before,
            identity_state=ident,
            phase_after_state=after_phase,
            qhtri_execution_state=execution,
        )

        self.assertTrue(validate_hypercrystal(after))
        self.assertEqual(after["identity_context"]["crystal_id"], CRYSTAL_ID)
        self.assertNotEqual(
            after["hypercrystal_semantic_commitment"],
            before["hypercrystal_semantic_commitment"],
        )
        roles = {c["role"]: c for c in after["components"]}
        self.assertIn("QHTRI", roles)
        self.assertIn("DICTIONARY", roles)
        self.assertEqual(roles["PHASE"]["semantic_commitment"], semantic_commitment(after_phase))
        self.assertEqual(roles["QHTRI"]["semantic_commitment"], semantic_commitment(execution))

    def test_wrong_parent_hypercrystal_commitment_rejected(self):
        ident = identity()
        before_phase = phase(0.1, "88" * 32, "before")
        after_phase = phase(0.2, "99" * 32, "after")
        before = compose_hypercrystal(identity_state=ident, phase_state=before_phase)
        execution = build_m0_m11_execution_state(
            crystal_id=CRYSTAL_ID,
            boot_epoch=3,
            phase_index_before=20,
            phase_index_after=20,
            phase_before_semantic_commitment=semantic_commitment(before_phase),
            phase_after_semantic_commitment=semantic_commitment(after_phase),
            hypercrystal_semantic_commitment="cc" * 32,
            gate_receipt_id="bb" * 32,
            layer_status=statuses(),
            dt_used="0.001",
            stability_bound="2.5",
            closure="0.8",
            affect_multiplier="1",
            m4_admission="0.9",
            no_go="0",
        )
        with self.assertRaisesRegex(HypercrystalQHTRIBindError, "parent"):
            advance_hypercrystal_with_qhtri(
                hypercrystal_before=before,
                identity_state=ident,
                phase_after_state=after_phase,
                qhtri_execution_state=execution,
            )


if __name__ == "__main__":
    unittest.main()
