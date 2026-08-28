from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.bioos_gremlin_canon_binding_v06 import (
    BIOOS_V05_PARENT_COMMIT,
    GREMLIN_CANON_COMMIT,
    GREMLIN_LEDGER_BLOB_SHA,
    GREMLIN_PIN_MANIFEST_COMMITMENT,
    BioOSGremlinCanonBindingV06Error,
    build_canon_pin_manifest_v06,
    build_neutrino_canon_binding_v06,
    evaluate_c_nu_use_v06,
    make_m10_canon_binding_receipt_v06,
    validate_canon_pin_manifest_v06,
    validate_neutrino_canon_binding_v06,
)

PIN_PATH = (
    Path(__file__).resolve().parents[1]
    / "provenance"
    / "BIOOS_GREMLIN_CANON_PIN_V0_6.json"
)


class BioOSGremlinCanonBindingV06Tests(unittest.TestCase):
    def setUp(self):
        self.binding = build_neutrino_canon_binding_v06(
            binding_id="bioos-cnu-v06",
            evidence_refs=["GREMLIN:PR4", "NOEMA:live-tether-active"],
        )

    def test_machine_readable_canon_pin_matches_compiled_contract(self):
        manifest = json.loads(PIN_PATH.read_text(encoding="utf-8"))
        self.assertTrue(validate_canon_pin_manifest_v06(manifest))
        self.assertEqual(manifest, build_canon_pin_manifest_v06())
        self.assertEqual(
            manifest["manifest_commitment"],
            GREMLIN_PIN_MANIFEST_COMMITMENT,
        )

    def test_machine_readable_canon_pin_tamper_fails_closed(self):
        manifest = json.loads(PIN_PATH.read_text(encoding="utf-8"))
        manifest["canonical_claims"][0]["status"] = "CANONICAL"
        with self.assertRaises(BioOSGremlinCanonBindingV06Error):
            validate_canon_pin_manifest_v06(manifest)

    def test_exact_canon_and_parent_pins(self):
        self.assertTrue(validate_neutrino_canon_binding_v06(self.binding))
        self.assertEqual(self.binding["source_authority"]["commit"], GREMLIN_CANON_COMMIT)
        self.assertEqual(self.binding["source_authority"]["ledger_blob_sha"], GREMLIN_LEDGER_BLOB_SHA)
        self.assertEqual(
            self.binding["source_authority"]["pin_manifest_commitment"],
            GREMLIN_PIN_MANIFEST_COMMITMENT,
        )
        self.assertEqual(self.binding["bioos_parent"]["commit"], BIOOS_V05_PARENT_COMMIT)
        self.assertFalse(self.binding["authority"]["authority_grant"])
        self.assertFalse(self.binding["authority"]["execution_admitted"])

    def test_cnu1_requires_embedding_and_pmns_preconditions(self):
        pending = evaluate_c_nu_use_v06(self.binding, claim_id="C-Nu-1")
        self.assertEqual(pending["status"], "PRECONDITION_OPEN")
        self.assertEqual(len(pending["missing_preconditions"]), 2)
        self.assertFalse(pending["m4_candidate_admitted"])
        self.assertFalse(pending["execution_admitted"])

        ready = evaluate_c_nu_use_v06(
            self.binding,
            claim_id="C-Nu-1",
            satisfied_preconditions=[
                "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME",
                "PMNS_ORIENTATION_BOUND",
            ],
        )
        self.assertEqual(ready["status"], "READY_FOR_SEPARATE_M4_RUNTIME_VALIDATION")
        self.assertTrue(ready["m4_candidate_admitted"])
        self.assertFalse(ready["execution_admitted"])

    def test_cnu3_shared_absolute_spectrum_is_m11_no_go(self):
        r = evaluate_c_nu_use_v06(
            self.binding,
            claim_id="C-Nu-3",
            request_shared_absolute_spectrum=True,
        )
        self.assertTrue(r["m11_no_go"])
        self.assertFalse(r["m4_candidate_admitted"])
        self.assertFalse(r["execution_admitted"])
        self.assertEqual(r["status"], "M11_NO_GO")

    def test_probability_shadow_firewall_is_knowledge_only(self):
        c2 = next(c for c in self.binding["claims"] if c["claim_id"] == "C-Nu-2")
        self.assertEqual(c2["effect_policy"], "KNOWLEDGE_FIREWALL_NO_DIRECT_EFFECT")
        self.assertEqual(c2["semantic_layers"], ["M6"])
        self.assertEqual(c2["enforcement_layers"], ["M10", "M11"])

    def test_m10_receipt_binds_machine_readable_canon_pin(self):
        r = make_m10_canon_binding_receipt_v06(
            self.binding,
            receipt_id="m10-cnu-bind-001",
            evidence_refs=["runner:host-conformance"],
        )
        self.assertTrue(r["append_only"])
        self.assertFalse(r["authority_grant"])
        self.assertFalse(r["execution_admitted"])
        self.assertEqual(r["gremlin_canon_commit"], GREMLIN_CANON_COMMIT)
        self.assertEqual(
            r["gremlin_pin_manifest_commitment"],
            GREMLIN_PIN_MANIFEST_COMMITMENT,
        )

    def test_tamper_fails_closed(self):
        t = copy.deepcopy(self.binding)
        t["authority"]["execution_admitted"] = True
        with self.assertRaises(BioOSGremlinCanonBindingV06Error):
            validate_neutrino_canon_binding_v06(t)

        with self.assertRaises(BioOSGremlinCanonBindingV06Error):
            build_neutrino_canon_binding_v06(
                binding_id="wrong-pin",
                gremlin_canon_commit="0" * 40,
            )

        with self.assertRaises(BioOSGremlinCanonBindingV06Error):
            build_neutrino_canon_binding_v06(
                binding_id="wrong-manifest-pin",
                gremlin_pin_manifest_commitment="0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
