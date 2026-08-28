from __future__ import annotations

import copy
import unittest

from tools.bioos_cnu_qhtri_admission_v061 import (
    BioOSCNuQHTRIAdmissionV061Error,
    build_cnu_qhtri_admission_v061,
    validate_cnu_qhtri_admission_v061,
)
from tools.bioos_gremlin_canon_binding_v06 import build_neutrino_canon_binding_v06


class BioOSCNuQHTRIAdmissionV061Tests(unittest.TestCase):
    def setUp(self):
        self.binding = build_neutrino_canon_binding_v06(binding_id="bioos-cnu-v061-test")

    def test_cnu1_open_preconditions_are_zero_force(self):
        env = build_cnu_qhtri_admission_v061(self.binding, claim_id="C-Nu-1")
        self.assertTrue(validate_cnu_qhtri_admission_v061(env))
        self.assertEqual(env["status"], "PRECONDITION_OPEN_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 0.0)
        self.assertEqual(env["m0_m11_projection"]["M11"]["closure"], 0.0)
        self.assertEqual(env["qhtri_admission_ir"]["character_term_count"], 0)
        self.assertFalse(env["execution_admitted"])

    def test_cnu1_ready_preconditions_still_wait_for_capability(self):
        env = build_cnu_qhtri_admission_v061(
            self.binding,
            claim_id="C-Nu-1",
            satisfied_preconditions=[
                "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME",
                "PMNS_ORIENTATION_BOUND",
            ],
        )
        self.assertEqual(env["status"], "CAPABILITY_OPEN_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 0.0)
        self.assertEqual(env["m0_m11_projection"]["M11"]["closure"], 1.0)
        self.assertEqual(env["qhtri_admission_ir"]["character_term_count"], 0)

    def test_positive_capability_requires_provenance_ref(self):
        with self.assertRaises(BioOSCNuQHTRIAdmissionV061Error):
            build_cnu_qhtri_admission_v061(
                self.binding,
                claim_id="C-Nu-1",
                satisfied_preconditions=[
                    "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME",
                    "PMNS_ORIENTATION_BOUND",
                ],
                capability_admission=1.0,
            )

    def test_ready_capability_is_metadata_ready_but_zero_force(self):
        env = build_cnu_qhtri_admission_v061(
            self.binding,
            claim_id="C-Nu-1",
            satisfied_preconditions=[
                "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME",
                "PMNS_ORIENTATION_BOUND",
            ],
            capability_admission=1.0,
            capability_ref="PNCAP:test-capability",
            runtime_validator_confidence=1.0,
        )
        self.assertTrue(validate_cnu_qhtri_admission_v061(env))
        self.assertEqual(env["status"], "READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 1.0)
        self.assertEqual(env["m0_m11_projection"]["M11"]["closure"], 1.0)
        self.assertEqual(env["qhtri_admission_ir"]["character_term_count"], 0)
        self.assertTrue(env["operator_binding_required"])
        self.assertFalse(env["execution_admitted"])

    def test_cnu3_shared_spectrum_is_hard_no_go_zero_force(self):
        env = build_cnu_qhtri_admission_v061(
            self.binding,
            claim_id="C-Nu-3",
            request_shared_absolute_spectrum=True,
            capability_admission=1.0,
            capability_ref="PNCAP:test-capability",
        )
        self.assertEqual(env["status"], "M11_NO_GO_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M11"]["no_go"], 1.0)
        self.assertEqual(env["m0_m11_projection"]["M11"]["closure"], 0.0)
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 0.0)
        self.assertEqual(env["qhtri_admission_ir"]["character_term_count"], 0)

    def test_cnu2_probability_shadow_is_zero_force_knowledge_path(self):
        env = build_cnu_qhtri_admission_v061(
            self.binding,
            claim_id="C-Nu-2",
            runtime_validator_confidence=1.0,
        )
        self.assertEqual(env["claim_role"], "PROBABILITY_SHADOW_FIREWALL")
        self.assertEqual(env["status"], "CAPABILITY_OPEN_ZERO_FORCE")
        self.assertEqual(env["qhtri_admission_ir"]["force_status"], "ZERO_FORCE_ADMISSION_METADATA_ONLY")
        self.assertFalse(env["production_runtime_write"])

    def test_gate_scalars_fail_closed_outside_unit_interval(self):
        with self.assertRaises(BioOSCNuQHTRIAdmissionV061Error):
            build_cnu_qhtri_admission_v061(
                self.binding,
                claim_id="C-Nu-2",
                runtime_validator_confidence=1.01,
            )
        with self.assertRaises(BioOSCNuQHTRIAdmissionV061Error):
            build_cnu_qhtri_admission_v061(
                self.binding,
                claim_id="C-Nu-2",
                capability_admission=-0.01,
            )

    def test_envelope_tamper_fails_closed(self):
        env = build_cnu_qhtri_admission_v061(self.binding, claim_id="C-Nu-2")
        tampered = copy.deepcopy(env)
        tampered["execution_admitted"] = True
        with self.assertRaises(BioOSCNuQHTRIAdmissionV061Error):
            validate_cnu_qhtri_admission_v061(tampered)

        tampered = copy.deepcopy(env)
        tampered["qhtri_admission_ir"]["character_term_count"] = 1
        with self.assertRaises(BioOSCNuQHTRIAdmissionV061Error):
            validate_cnu_qhtri_admission_v061(tampered)


if __name__ == "__main__":
    unittest.main()
