import unittest

from tools.qhtri_m0_m11_gate_fabric_v01 import compile_gate_fabric, qhtri_step
from tools.qhtri_m0_m11_gate_ir_v01 import (
    gate_ir,
    make_m10_receipt_v2,
    validate_gate_ir,
)


def vec(x):
    return [float(x)] * 36


class QHTRIGateIRTests(unittest.TestCase):
    def test_four_kernel_families_are_exact(self):
        fabric = compile_gate_fabric({
            "M1": {"target": vec(0.2)},
            "M4": {"procedure_match": 1.0, "validator_confidence": 0.9, "capability_admission": 1.0},
            "M6": {"edges": [{"i": 0, "j": 1, "m": 1, "n": 1, "tau": 0.0, "K": 0.1, "R": 0.8}]},
            "M10": {"append_only": True},
            "M11": {"validation_confidence": 0.8, "uncertainty": 0.1, "no_go": 0.0},
        })
        ir = gate_ir(fabric)
        self.assertTrue(validate_gate_ir(ir))
        self.assertEqual(set(ir["kernel_families"]), {
            "K0_PHASE_LOCK_ANCHOR",
            "K1_TORSION_COUPLING",
            "K2_GAIN_MODULATION",
            "K3_RECEIPT_OBSERVER",
        })

    def test_commitment_is_deterministic(self):
        frames = {
            "M1": {"target": vec(0.2)},
            "M6": {"edges": [{"i": 2, "j": 3, "m": 2, "n": 3, "tau": 0.1, "K": 0.2, "R": 0.7}]},
        }
        a = gate_ir(compile_gate_fabric(frames))
        b = gate_ir(compile_gate_fabric(frames))
        self.assertEqual(a["operator_profile_commitment"], b["operator_profile_commitment"])

    def test_operator_change_changes_commitment(self):
        a = gate_ir(compile_gate_fabric({"M1": {"target": vec(0.2)}}))
        b = gate_ir(compile_gate_fabric({"M1": {"target": vec(0.3)}}))
        self.assertNotEqual(a["operator_profile_commitment"], b["operator_profile_commitment"])

    def test_m10_v2_receipt_binds_operator_profile(self):
        fabric = compile_gate_fabric({
            "M1": {"target": vec(0.2)},
            "M10": {"append_only": True},
        })
        step = qhtri_step(vec(0.0), vec(0.0), fabric, dt_requested=0.01)
        receipt = make_m10_receipt_v2(
            step,
            fabric,
            hypercrystal_commitment="11" * 32,
            evidence_refs=["b", "a"],
        )
        ir = gate_ir(fabric)
        self.assertEqual(receipt["operator_profile_commitment"], ir["operator_profile_commitment"])
        self.assertTrue(receipt["append_only"])
        self.assertFalse(receipt["authority_grant"])


if __name__ == "__main__":
    unittest.main()
