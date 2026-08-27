import copy
import unittest

from pnv_state_memory import (
    semantic_commitment,
    t36_identity_semantic_state,
    t36_phase_semantic_state,
)
from tools.hypercrystal_state_v01 import (
    HypercrystalComponent,
    HypercrystalStateError,
    compose_hypercrystal,
    validate_hypercrystal,
)


RECEIPT = "aa" * 32
CRYSTAL = "11" * 32
GENESIS = "22" * 32
CONFIG = "77" * 32


def identity_state(phase_index=8, boot_epoch=3, crystal_id=CRYSTAL):
    return t36_identity_semantic_state(
        crystal_id=crystal_id,
        genesis_anchor_commitment=GENESIS,
        origin_binding_sha256="33" * 32,
        pnvector_payload_sha256="44" * 32,
        source_context_sha256="55" * 32,
        basis_binding="66" * 32,
        configuration_sha256=CONFIG,
        phase_index=phase_index,
        boot_epoch=boot_epoch,
    )


def phase_state(boot_epoch=3, crystal_id=CRYSTAL, tick=101):
    values=[0.03125*i for i in range(36)]
    return t36_phase_semantic_state(
        values,
        source_receipt=RECEIPT,
        observation_generation="live-g101",
        identity_context={"crystal_id":crystal_id,"boot_epoch":boot_epoch},
        tick=tick,
        clock_binding={"f0":{"kind":"RATIONAL","p":783,"q":100}},
    )


def component(role, seed, projection=None):
    return HypercrystalComponent(
        role=role,
        semantic_schema=f"{role}_SEMANTIC_V0_1",
        semantic_commitment=(f"{seed:02x}"*32),
        generation_ref=f"g-{role.lower()}",
        projection_role=projection,
    )


class HypercrystalStateV01Tests(unittest.TestCase):
    def test_nexus_is_hypercrystal_with_required_identity_and_phase(self):
        h=compose_hypercrystal(identity_state=identity_state(),phase_state=phase_state())
        self.assertEqual(h["canonical_name"],"NEXUS")
        self.assertEqual(h["system_form"],"HYPERCRYSTAL")
        self.assertEqual(h["identity_context"]["crystal_id"],CRYSTAL)
        self.assertEqual([c["role"] for c in h["components"]],["IDENTITY","PHASE"])
        self.assertTrue(validate_hypercrystal(h))

    def test_component_order_does_not_change_hypercrystal_commitment(self):
        a=[component("DICTIONARY",0x91,"HYPERCRYSTAL_PROJECTION[DICTIONARY]/v0.1"),component("QHTRI",0x92)]
        b=list(reversed(a))
        ha=compose_hypercrystal(identity_state=identity_state(),phase_state=phase_state(),additional_components=a)
        hb=compose_hypercrystal(identity_state=identity_state(),phase_state=phase_state(),additional_components=b)
        self.assertEqual(ha["hypercrystal_semantic_commitment"],hb["hypercrystal_semantic_commitment"])

    def test_adding_dictionary_projection_evolves_hypercrystal_under_same_crystal_id(self):
        base=compose_hypercrystal(identity_state=identity_state(),phase_state=phase_state())
        enriched=compose_hypercrystal(
            identity_state=identity_state(),
            phase_state=phase_state(),
            additional_components=[component("DICTIONARY",0x93,"HYPERCRYSTAL_PROJECTION[DICTIONARY]/v0.1")],
        )
        self.assertEqual(base["identity_context"]["crystal_id"],enriched["identity_context"]["crystal_id"])
        self.assertNotEqual(base["hypercrystal_semantic_commitment"],enriched["hypercrystal_semantic_commitment"])

    def test_cqcl_and_gremlin_are_fields_of_same_hypercrystal(self):
        h=compose_hypercrystal(
            identity_state=identity_state(),
            phase_state=phase_state(),
            additional_components=[component("CQCL",0x94),component("GREMLIN",0x95)],
        )
        roles={c["role"] for c in h["components"]}
        self.assertEqual(roles,{"IDENTITY","PHASE","CQCL","GREMLIN"})
        self.assertFalse(h["authority_grant"])
        self.assertFalse(h["execution_admitted"])

    def test_crystal_id_mismatch_fails_closed(self):
        with self.assertRaisesRegex(HypercrystalStateError,"CRYSTAL_ID mismatch"):
            compose_hypercrystal(
                identity_state=identity_state(),
                phase_state=phase_state(crystal_id="99"*32),
            )

    def test_boot_epoch_mismatch_fails_closed(self):
        with self.assertRaisesRegex(HypercrystalStateError,"boot_epoch mismatch"):
            compose_hypercrystal(
                identity_state=identity_state(boot_epoch=3),
                phase_state=phase_state(boot_epoch=4),
            )

    def test_duplicate_component_role_fails_closed(self):
        with self.assertRaisesRegex(HypercrystalStateError,"duplicate"):
            compose_hypercrystal(
                identity_state=identity_state(),
                phase_state=phase_state(),
                additional_components=[component("QHTRI",0x96),component("QHTRI",0x97)],
            )

    def test_commitment_tamper_fails_closed(self):
        h=compose_hypercrystal(identity_state=identity_state(),phase_state=phase_state())
        bad=copy.deepcopy(h)
        bad["hypercrystal_semantic_commitment"]="00"*32
        with self.assertRaisesRegex(HypercrystalStateError,"commitment mismatch"):
            validate_hypercrystal(bad)

    def test_identity_phase_semantic_commitments_are_component_refs(self):
        ident=identity_state()
        phase=phase_state()
        h=compose_hypercrystal(identity_state=ident,phase_state=phase)
        refs={c["role"]:c["semantic_commitment"] for c in h["components"]}
        self.assertEqual(refs["IDENTITY"],semantic_commitment(ident))
        self.assertEqual(refs["PHASE"],semantic_commitment(phase))


if __name__ == "__main__":
    unittest.main()
