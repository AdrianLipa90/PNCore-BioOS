import math
import unittest

from tools.qhtri_m0_m11_gate_fabric_v01 import (
    compile_gate_fabric,
    qhtri_force,
    qhtri_step,
    stability_bound,
)
from tools.qhtri_m0_m11_gate_ir_v02 import (
    character_force,
    character_stability_bound,
    gate_ir_v02,
    make_m10_receipt_v3,
    validate_gate_ir_v02,
)


def vec(x):
    return [float(x)] * 36


def ramp(scale=0.03):
    return [scale * i for i in range(36)]


class QHTRIGateIRV02Tests(unittest.TestCase):
    def _fabric(self):
        return compile_gate_fabric({
            "M1": {"target": vec(0.2)},
            "M3": {"targets": [vec(0.1), vec(0.3)], "weights": [0.4, 0.6]},
            "M4": {"procedure_match": 1.0, "validator_confidence": 0.9, "capability_admission": 1.0},
            "M6": {"edges": [
                {"i": 0, "j": 1, "m": 3, "n": 2, "tau": 0.37, "K": 0.2, "R": 0.8},
                {"i": 5, "j": 9, "m": 1, "n": 4, "tau": -0.2, "K": 0.1, "R": 0.7},
            ]},
            "M7": {"targets": [vec(-0.2), vec(0.4)], "weights": [0.5, 0.5]},
            "M10": {"append_only": True},
            "M11": {"validation_confidence": 0.8, "uncertainty": 0.1, "no_go": 0.0},
        })

    def test_three_force_execution_families(self):
        ir = gate_ir_v02(self._fabric())
        self.assertTrue(validate_gate_ir_v02(ir))
        self.assertEqual(set(ir["kernel_families"]), {
            "KCHI_TORUS_CHARACTER_FIELD",
            "K2_GAIN_MODULATION",
            "K3_RECEIPT_OBSERVER",
        })
        self.assertEqual(ir["geometry"]["force_kernel_families"], 3)
        self.assertEqual(ir["geometry"]["dual_lattice"], "Z^36")
        self.assertEqual(ir["reducers"]["PHASE_CENTROID"]["active_layers"], ["M3", "M7"])
        self.assertFalse(ir["normalization"]["gcd_reduction"])

    def test_character_force_matches_existing_executor(self):
        fabric = self._fabric()
        ir = gate_ir_v02(fabric)
        a = qhtri_force(ramp(), fabric)
        b = character_force(ramp(), ir)
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=12)

    def test_character_bound_matches_existing_stability_bound(self):
        fabric = self._fabric()
        ir = gate_ir_v02(fabric)
        self.assertAlmostEqual(character_stability_bound(ir), stability_bound(fabric), places=12)

    def test_orientation_gauge_has_same_commitments(self):
        a = compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 3, "n": 2, "tau": 0.4, "K": 0.2, "R": 0.7}]},
        })
        b = compile_gate_fabric({
            "M6": {"edges": [{"i": 1, "j": 0, "m": 2, "n": 3, "tau": -0.4, "K": 0.2, "R": 0.7}]},
        })
        ia = gate_ir_v02(a)
        ib = gate_ir_v02(b)
        self.assertEqual(ia["character_field_commitment"], ib["character_field_commitment"])
        self.assertEqual(ia["operator_profile_commitment"], ib["operator_profile_commitment"])

    def test_tau_period_is_numeric_gauge_without_tolerance_hash_collapse(self):
        a = compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 3, "n": 2, "tau": 0.4, "K": 0.2, "R": 0.7}]},
        })
        b = compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 3, "n": 2, "tau": 0.4 + 2.0 * math.pi, "K": 0.2, "R": 0.7}]},
        })
        theta = ramp(0.07)
        fa = character_force(theta, gate_ir_v02(a))
        fb = character_force(theta, gate_ir_v02(b))
        for x, y in zip(fa, fb):
            self.assertAlmostEqual(x, y, places=12)

    def test_gcd_normalization_is_rejected_by_identity(self):
        high = gate_ir_v02(compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 2, "n": 4, "tau": 0.0, "K": 0.2, "R": 0.7}]},
        }))
        reduced = gate_ir_v02(compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 1, "n": 2, "tau": 0.0, "K": 0.2, "R": 0.7}]},
        }))
        self.assertNotEqual(high["character_field_commitment"], reduced["character_field_commitment"])
        high_mode = high["kernel_families"]["KCHI_TORUS_CHARACTER_FIELD"][0]["ell"]
        self.assertEqual(high_mode[0], 4)
        self.assertEqual(high_mode[1], -2)

    def test_field_identity_and_semantic_profile_identity_are_distinct(self):
        a = gate_ir_v02(compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 3, "n": 2, "tau": 0.4, "K": 0.2, "R": 0.7, "source_ref": "A"}]},
        }))
        b = gate_ir_v02(compile_gate_fabric({
            "M6": {"edges": [{"i": 0, "j": 1, "m": 3, "n": 2, "tau": 0.4, "K": 0.2, "R": 0.7, "source_ref": "B"}]},
        }))
        self.assertEqual(a["character_field_commitment"], b["character_field_commitment"])
        self.assertNotEqual(a["operator_profile_commitment"], b["operator_profile_commitment"])

    def test_m10_v3_binds_field_and_profile(self):
        fabric = self._fabric()
        step = qhtri_step(ramp(), vec(0.0), fabric, dt_requested=0.01)
        receipt = make_m10_receipt_v3(
            step,
            fabric,
            hypercrystal_commitment="11" * 32,
            evidence_refs=["b", "a"],
        )
        ir = gate_ir_v02(fabric)
        self.assertEqual(receipt["character_field_commitment"], ir["character_field_commitment"])
        self.assertEqual(receipt["operator_profile_commitment"], ir["operator_profile_commitment"])
        self.assertTrue(receipt["append_only"])
        self.assertFalse(receipt["authority_grant"])


if __name__ == "__main__":
    unittest.main()
