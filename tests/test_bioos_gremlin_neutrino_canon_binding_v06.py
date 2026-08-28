from __future__ import annotations

import copy
import unittest

from tools.bioos_gremlin_neutrino_canon_binding_v06 import (
    BioOSCanonBindingV06Error,
    GREMLIN_CANON_COMMIT,
    GREMLIN_LEDGER_BLOB_SHA,
    SHARED_ABSOLUTE_SCOPE,
    authority_snapshot,
    build_canon_ir_v06,
    make_m10_canon_receipt_v06,
    validate_canon_ir_v06,
)


class BioOSGremlinNeutrinoCanonBindingV06Tests(unittest.TestCase):
    def test_exact_authority_pin_and_default_claims(self) -> None:
        ir = build_canon_ir_v06()
        self.assertTrue(validate_canon_ir_v06(ir))
        self.assertEqual(ir["authority_source"]["canon_commit"], GREMLIN_CANON_COMMIT)
        self.assertEqual(ir["authority_source"]["ledger_blob_sha"], GREMLIN_LEDGER_BLOB_SHA)
        self.assertEqual([v["claim_id"] for v in ir["claims"]], ["C-Nu-1", "C-Nu-2", "C-Nu-3"])
        self.assertFalse(ir["execution_contract"]["authority_grant"])
        self.assertFalse(ir["execution_contract"]["execution_admitted"])
        self.assertFalse(ir["execution_contract"]["production_runtime_write"])

    def test_tampered_external_authority_pin_fails_closed(self) -> None:
        bad = authority_snapshot()
        bad["canon_commit"] = "0" * 40
        with self.assertRaises(BioOSCanonBindingV06Error):
            build_canon_ir_v06(source_snapshot=bad)

    def test_cnu_layer_binding_is_typed(self) -> None:
        ir = build_canon_ir_v06(claim_ids=("C-Nu-1", "C-Nu-2", "C-Nu-3"))
        by_id = {v["claim_id"]: v for v in ir["claims"]}
        self.assertEqual(by_id["C-Nu-1"]["m0_m11_layers"], ["M3", "M4", "M6", "M9", "M10", "M11"])
        self.assertEqual(by_id["C-Nu-2"]["m0_m11_layers"], ["M6", "M10", "M11"])
        self.assertEqual(by_id["C-Nu-3"]["m0_m11_layers"], ["M4", "M9", "M10", "M11"])

    def test_shared_absolute_spectrum_hits_m11_no_go(self) -> None:
        ir = build_canon_ir_v06(usage_scope=SHARED_ABSOLUTE_SCOPE)
        self.assertTrue(ir["m11_no_go"])
        self.assertEqual(ir["m11_reason"], "SHARED_ABSOLUTE_NEUTRINO_SPECTRUM_AUTHORITY_WITHHELD")
        self.assertFalse(ir["execution_contract"]["execution_admitted"])

    def test_branch_local_spectrum_does_not_trigger_cross_framework_no_go(self) -> None:
        for scope in ("GRADED_PROJECTION_BRANCH", "TIR_TETRAHEDRON_BRANCH"):
            ir = build_canon_ir_v06(usage_scope=scope)
            self.assertTrue(ir["branch_scope_declared"])
            self.assertFalse(ir["m11_no_go"])
            self.assertFalse(ir["execution_contract"]["execution_admitted"])

    def test_shared_absolute_scope_cannot_omit_firewall(self) -> None:
        with self.assertRaises(BioOSCanonBindingV06Error):
            build_canon_ir_v06(claim_ids=("C-Nu-1", "C-Nu-2"), usage_scope=SHARED_ABSOLUTE_SCOPE)

    def test_ir_commitment_tamper_fails(self) -> None:
        ir = build_canon_ir_v06()
        bad = copy.deepcopy(ir)
        bad["claims"][0]["status"] = "CANONICAL"
        with self.assertRaises(BioOSCanonBindingV06Error):
            validate_canon_ir_v06(bad)

    def test_m10_receipt_is_deterministic_append_only_and_non_authoritative(self) -> None:
        ir = build_canon_ir_v06(usage_scope="KNOWLEDGE_BINDING_ONLY")
        r1 = make_m10_canon_receipt_v06(ir, evidence_refs=("z", "a"))
        r2 = make_m10_canon_receipt_v06(ir, evidence_refs=("a", "z"))
        self.assertEqual(r1, r2)
        self.assertTrue(r1["append_only"])
        self.assertFalse(r1["authority_grant"])
        self.assertFalse(r1["execution_admitted"])
        self.assertFalse(r1["production_runtime_write"])
        self.assertEqual(r1["evidence_refs"], ["a", "z"])


if __name__ == "__main__":
    unittest.main()
