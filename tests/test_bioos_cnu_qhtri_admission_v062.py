from __future__ import annotations

import copy
import hashlib
import json
import unittest

from tools.bioos_cnu_qhtri_admission_v062 import (
    DOMAIN,
    BioOSCNuQHTRIAdmissionV062Error,
    build_cnu_qhtri_admission_v062,
    validate_cnu_qhtri_admission_v062,
)
from tools.bioos_gremlin_canon_binding_v06 import build_neutrino_canon_binding_v06


def _reseal(envelope):
    core = dict(envelope)
    core.pop("admission_commitment", None)
    payload = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.blake2b(DOMAIN + payload, digest_size=32).hexdigest()


class BioOSCNuQHTRIAdmissionV062Tests(unittest.TestCase):
    def setUp(self):
        self.binding = build_neutrino_canon_binding_v06(binding_id="bioos-cnu-v062-test")

    def test_cnu1_is_only_operator_bindable_claim(self):
        env = build_cnu_qhtri_admission_v062(
            self.binding,
            claim_id="C-Nu-1",
            satisfied_preconditions=[
                "SOURCE_BOUND_ORTHONORMAL_NEUTRINO_FRAME",
                "PMNS_ORIENTATION_BOUND",
            ],
            capability_admission=1.0,
            capability_ref="PNCAP:test-capability",
        )
        self.assertTrue(validate_cnu_qhtri_admission_v062(env, self.binding))
        self.assertEqual(env["binding_mode"], "OPERATOR_BINDABLE")
        self.assertTrue(env["operator_binding_required"])
        self.assertEqual(env["status"], "READY_FOR_SEPARATE_OPERATOR_BINDING_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 1.0)
        self.assertEqual(env["qhtri_admission_ir"]["character_term_count"], 0)
        self.assertFalse(env["execution_admitted"])

    def test_cnu2_is_permanently_knowledge_only(self):
        env = build_cnu_qhtri_admission_v062(
            self.binding,
            claim_id="C-Nu-2",
            runtime_validator_confidence=1.0,
        )
        self.assertTrue(validate_cnu_qhtri_admission_v062(env, self.binding))
        self.assertEqual(env["binding_mode"], "KNOWLEDGE_ONLY")
        self.assertFalse(env["operator_binding_required"])
        self.assertEqual(env["status"], "KNOWLEDGE_ONLY_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 0.0)
        self.assertEqual(env["runtime_validation"]["effective_capability_admission"], 0.0)

        with self.assertRaises(BioOSCNuQHTRIAdmissionV062Error):
            build_cnu_qhtri_admission_v062(
                self.binding,
                claim_id="C-Nu-2",
                capability_admission=1.0,
                capability_ref="PNCAP:forbidden",
            )

    def test_cnu3_is_enforcement_only_and_no_go_stays_fail_closed(self):
        clear = build_cnu_qhtri_admission_v062(
            self.binding,
            claim_id="C-Nu-3",
            request_shared_absolute_spectrum=False,
        )
        self.assertTrue(validate_cnu_qhtri_admission_v062(clear, self.binding))
        self.assertEqual(clear["binding_mode"], "ENFORCEMENT_ONLY")
        self.assertFalse(clear["operator_binding_required"])
        self.assertEqual(clear["status"], "FIREWALL_CLEAR_ZERO_FORCE")
        self.assertEqual(clear["m0_m11_projection"]["M4"]["admission"], 0.0)

        blocked = build_cnu_qhtri_admission_v062(
            self.binding,
            claim_id="C-Nu-3",
            request_shared_absolute_spectrum=True,
        )
        self.assertTrue(validate_cnu_qhtri_admission_v062(blocked, self.binding))
        self.assertEqual(blocked["status"], "M11_NO_GO_ZERO_FORCE")
        self.assertEqual(blocked["m0_m11_projection"]["M11"]["no_go"], 1.0)
        self.assertEqual(blocked["m0_m11_projection"]["M11"]["closure"], 0.0)
        self.assertEqual(blocked["m0_m11_projection"]["M4"]["admission"], 0.0)

        with self.assertRaises(BioOSCNuQHTRIAdmissionV062Error):
            build_cnu_qhtri_admission_v062(
                self.binding,
                claim_id="C-Nu-3",
                capability_admission=1.0,
                capability_ref="PNCAP:forbidden",
            )

    def test_open_cnu1_preconditions_zero_capability_and_zero_force(self):
        env = build_cnu_qhtri_admission_v062(self.binding, claim_id="C-Nu-1")
        self.assertTrue(validate_cnu_qhtri_admission_v062(env, self.binding))
        self.assertEqual(env["status"], "PRECONDITION_OPEN_ZERO_FORCE")
        self.assertEqual(env["m0_m11_projection"]["M4"]["admission"], 0.0)
        self.assertEqual(env["m0_m11_projection"]["M11"]["closure"], 0.0)
        self.assertEqual(env["qhtri_admission_ir"]["character_term_count"], 0)

    def test_policy_reseal_tamper_fails_closed(self):
        env = build_cnu_qhtri_admission_v062(self.binding, claim_id="C-Nu-2")
        tampered = copy.deepcopy(env)
        tampered["binding_mode"] = "OPERATOR_BINDABLE"
        tampered["operator_binding_required"] = True
        tampered["admission_commitment"] = _reseal(tampered)
        with self.assertRaises(BioOSCNuQHTRIAdmissionV062Error):
            validate_cnu_qhtri_admission_v062(tampered, self.binding)

    def test_non_operator_effective_capability_reseal_tamper_fails_closed(self):
        env = build_cnu_qhtri_admission_v062(self.binding, claim_id="C-Nu-3")
        tampered = copy.deepcopy(env)
        tampered["runtime_validation"]["effective_capability_admission"] = 1.0
        tampered["admission_commitment"] = _reseal(tampered)
        with self.assertRaises(BioOSCNuQHTRIAdmissionV062Error):
            validate_cnu_qhtri_admission_v062(tampered, self.binding)


if __name__ == "__main__":
    unittest.main()
