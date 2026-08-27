import copy
import math
import unittest

from tools.identity_nexus_v01 import (
    IdentityNexusError,
    KAPPA,
    compute_identity_nexus,
    validate_nexus_generation,
)


TERM_COUNT = 548


def crystal(phase_index=12):
    return {
        "crystal_id": "11" * 32,
        "configuration_sha256": "22" * 32,
        "boot_epoch": 3,
        "phase_index": phase_index,
        "spinor_sheet": phase_index & 1,
        "source_object_id": "33" * 32,
    }


def dictionary(states=TERM_COUNT):
    return {
        "repository": "AdrianLipa90/The-Consciousness-Dictionary",
        "branch": "feat/t36-identity-nexus-projection",
        "commit": "3aa1651da9735d94d2a9cbffec13203eeeedd502",
        "states": states,
        "relations": 306,
        "state_sha256": "56d758c54f27323ef7edcf5164d224801f182ec83cda04216953cfaeda135501",
        "relation_sha256": "8484cd1314df4b18c21207b7fe234e71007e5c4c59aaf356cffd4abea0d36e8a",
    }


def rows(count=TERM_COUNT, base_r=0.81):
    out=[]
    for i in range(count):
        r=min(0.999, base_r + (i % 17) * 0.001)
        out.append({
            "term_id": f"T-{i:04d}",
            "name": f"Term {i}",
            "phase_index": i + 1,
            "coherence": r,
            "phase": ((i % 21) - 10) * 0.1,
            "angular_distance": 1.0 - 0.25 * r,
            "informational_action": -KAPPA * math.log(r + 1e-12),
            "semantic_equivalence": False,
            "authority_grant": False,
        })
    return out


class IdentityNexusV01Tests(unittest.TestCase):
    def test_complete_548_term_projection_and_bounded_active_set(self):
        nexus=compute_identity_nexus(
            crystal_context=crystal(), dictionary_binding=dictionary(), projection_rows=rows(), active_limit=16
        )
        self.assertEqual(nexus["term_count"], 548)
        self.assertEqual(len(nexus["active_terms"]), 16)
        self.assertTrue(0.0 <= nexus["nexus_coherence"] <= 1.0)
        self.assertFalse(nexus["authority_grant"])
        self.assertTrue(validate_nexus_generation(nexus))

    def test_equal_r_global_coherence_is_scale_stable(self):
        r=0.93
        rr=[]
        for i in range(548):
            rr.append({
                "term_id": f"X-{i}", "name": str(i), "phase_index": i+1,
                "coherence": r, "phase": 0.0, "angular_distance": 0.4,
                "informational_action": -KAPPA*math.log(r+1e-12),
                "semantic_equivalence": False, "authority_grant": False,
            })
        nexus=compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rr)
        self.assertAlmostEqual(nexus["nexus_coherence"],r+1e-12,places=11)

    def test_active_order_is_deterministic(self):
        rr=rows()
        a=compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rr)
        b=compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=list(reversed(rr)))
        self.assertEqual(a["active_terms"],b["active_terms"])
        self.assertEqual(a["nexus_coherence"],b["nexus_coherence"])
        self.assertEqual(a["nexus_generation_id"],b["nexus_generation_id"])

    def test_term_count_mismatch_fails_closed(self):
        with self.assertRaisesRegex(IdentityNexusError,"term count mismatch"):
            compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rows(547))

    def test_duplicate_term_fails_closed(self):
        rr=rows(); rr[4]=copy.deepcopy(rr[3])
        with self.assertRaisesRegex(IdentityNexusError,"duplicate term_id"):
            compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rr)

    def test_authority_promotion_attempt_fails_closed(self):
        rr=rows(); rr[0]["authority_grant"]=True
        with self.assertRaisesRegex(IdentityNexusError,"authority grant"):
            compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rr)

    def test_semantic_equivalence_attempt_fails_closed(self):
        rr=rows(); rr[0]["semantic_equivalence"]=True
        with self.assertRaisesRegex(IdentityNexusError,"semantic equivalence"):
            compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rr)

    def test_bad_spinor_sheet_fails_closed(self):
        c=crystal(); c["spinor_sheet"] ^= 1
        with self.assertRaisesRegex(IdentityNexusError,"spinor_sheet"):
            compute_identity_nexus(crystal_context=c,dictionary_binding=dictionary(),projection_rows=rows())

    def test_generation_hash_detects_tamper(self):
        nexus=compute_identity_nexus(crystal_context=crystal(),dictionary_binding=dictionary(),projection_rows=rows())
        nexus["nexus_coherence"] *= 0.5
        with self.assertRaisesRegex(IdentityNexusError,"generation hash mismatch"):
            validate_nexus_generation(nexus)


if __name__=="__main__":
    unittest.main()
