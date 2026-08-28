import copy
import math
import unittest

from tools.qhtri_m0_m11_gate_fabric_v01 import (
    DIM,
    KAPPA,
    AnalogGateFabricError,
    analog_and,
    analog_not,
    analog_or,
    analog_xor,
    circular_barycenter,
    compile_gate_fabric,
    make_m10_receipt,
    qhtri_force,
    qhtri_step,
    stability_bound,
)


def vec(x):
    return [float(x)] * DIM


class QHTRIM0M11AnalogGateFabricTests(unittest.TestCase):
    def test_continuous_boolean_primitives_close_on_binary_boundary(self):
        for a in (0.0, 1.0):
            for b in (0.0, 1.0):
                self.assertEqual(analog_and(a, b), float(bool(a) and bool(b)))
                self.assertEqual(analog_or(a, b), float(bool(a) or bool(b)))
                self.assertEqual(analog_xor(a, b), float(bool(a) ^ bool(b)))
            self.assertEqual(analog_not(a), 1.0 - a)

    def test_whole_lane_dimension_is_mandatory(self):
        with self.assertRaisesRegex(AnalogGateFabricError, "exactly 36"):
            compile_gate_fabric({"M1": {"target": [0.0] * 12}})

    def test_m0_requires_provenance_and_does_not_fabricate_source(self):
        fabric = compile_gate_fabric({"M0": {"target": vec(0.4), "activation": 1.0}})
        self.assertEqual(fabric.layer_status["M0"], "UNPROVENANCED_SOURCE_QUIET")
        self.assertFalse(any(term.layer == "M0" for term in fabric.anchors))

    def test_m1_anchor_moves_phase_toward_target(self):
        fabric = compile_gate_fabric({
            "M1": {
                "target": vec(0.5),
                "command_activation": 1.0,
                "context_admission": 1.0,
            }
        })
        result = qhtri_step(vec(0.0), vec(0.0), fabric, dt_requested=0.01)
        self.assertGreater(result["theta_after"][0], 0.0)
        self.assertEqual(result["layer_status"]["M1"], "ACTIVE_WORKING_SET")

    def test_m3_semantic_barycenter_is_full_36d(self):
        fabric = compile_gate_fabric({
            "M3": {
                "targets": [vec(0.2), vec(0.4)],
                "weights": [1.0, 1.0],
                "activation": 1.0,
            }
        })
        term = next(term for term in fabric.anchors if term.layer == "M3")
        self.assertEqual(len(term.target), 36)
        self.assertEqual(len(term.gain), 36)
        self.assertAlmostEqual(term.target[0], 0.3, places=12)

    def test_m5_explicit_affect_modulates_salience_only(self):
        base = compile_gate_fabric({"M1": {"target": vec(0.5)}})
        mod = compile_gate_fabric({
            "M1": {"target": vec(0.5)},
            "M5": {"explicit": True, "salience_multiplier": 2.0},
        })
        g0 = next(t for t in base.anchors if t.layer == "M1").gain[0]
        g1 = next(t for t in mod.anchors if t.layer == "M1").gain[0]
        self.assertAlmostEqual(g1, 2.0 * g0, places=15)
        self.assertEqual(mod.layer_status["M5"], "EXPLICIT_MODULATION")
        self.assertEqual(base.affect_multiplier, 1.0)

    def test_m6_torsion_edge_executes_existing_qhtri_gradient(self):
        fabric = compile_gate_fabric({
            "M6": {
                "edges": [{"i": 0, "j": 1, "m": 1, "n": 1, "tau": 0.0, "K": KAPPA, "R": 1.0}]
            }
        })
        theta = vec(0.0)
        theta[0] = 0.5
        force = qhtri_force(theta, fabric)
        self.assertLess(force[0], 0.0)
        self.assertGreater(force[1], 0.0)
        self.assertAlmostEqual(force[0], -force[1], places=15)

    def test_m7_braid_disagreement_weakens_attractor_without_selection(self):
        fabric = compile_gate_fabric({
            "M7": {
                "targets": [vec(0.0), vec(math.pi)],
                "weights": [1.0, 1.0],
            }
        })
        term = next(term for term in fabric.anchors if term.layer == "M7")
        self.assertTrue(all(g <= 1e-15 for g in term.gain))
        self.assertEqual(fabric.layer_status["M7"], "BRAID_ACTIVE")

    def test_m8_is_protected_and_survives_m11_no_go(self):
        with self.assertRaisesRegex(AnalogGateFabricError, "M8 protected identity mutation denied"):
            compile_gate_fabric({"M8": {"target": vec(0.0), "mutation_attempt": True}})

        fabric = compile_gate_fabric({
            "M4": {
                "procedure_match": 1.0,
                "validator_confidence": 1.0,
                "capability_admission": 1.0,
            },
            "M7": {
                "targets": [vec(0.5)],
                "weights": [1.0],
                "effect_carrying": True,
            },
            "M8": {"target": vec(0.1), "identity_ref": "crystal:test"},
            "M11": {"validation_confidence": 1.0, "uncertainty": 0.0, "no_go": 1.0},
        })
        m7 = next(term for term in fabric.anchors if term.layer == "M7")
        m8 = next(term for term in fabric.anchors if term.layer == "M8")
        self.assertTrue(all(g == 0.0 for g in m7.gain))
        self.assertTrue(all(g > 0.0 for g in m8.gain))
        self.assertEqual(fabric.layer_status["M11"], "NO_GO")

    def test_m9_holonomy_transports_target(self):
        holonomy = vec(0.0)
        holonomy[0] = 0.25
        fabric = compile_gate_fabric({
            "M9": {"target": vec(0.1), "holonomy": holonomy, "confidence": 1.0}
        })
        m9 = next(term for term in fabric.anchors if term.layer == "M9")
        self.assertAlmostEqual(m9.target[0], 0.35, places=12)
        self.assertAlmostEqual(m9.target[1], 0.1, places=12)

    def test_m10_is_zero_force_receipt_observer(self):
        fabric = compile_gate_fabric({"M10": {"append_only": True}})
        force = qhtri_force(vec(0.7), fabric)
        self.assertTrue(all(v == 0.0 for v in force))
        step = qhtri_step(vec(0.7), vec(0.0), fabric, dt_requested=0.01)
        receipt_a = make_m10_receipt(step, hypercrystal_commitment="11" * 32, evidence_refs=["b", "a"])
        receipt_b = make_m10_receipt(step, hypercrystal_commitment="11" * 32, evidence_refs=["a", "b"])
        self.assertEqual(receipt_a["receipt_id"], receipt_b["receipt_id"])
        self.assertTrue(receipt_a["append_only"])
        self.assertFalse(receipt_a["authority_grant"])

    def test_m10_overwrite_mode_is_denied(self):
        with self.assertRaisesRegex(AnalogGateFabricError, "append-only"):
            compile_gate_fabric({"M10": {"append_only": False}})

    def test_high_order_torsion_enters_stability_budget(self):
        fabric = compile_gate_fabric({
            "M6": {
                "edges": [{"i": 0, "j": 1, "m": 944, "n": 945, "K": KAPPA, "R": 1.0}]
            }
        })
        L = stability_bound(fabric)
        self.assertGreater(L, 10000.0)
        step = qhtri_step(vec(0.1), vec(0.0), fabric, dt_requested=0.1)
        self.assertLess(step["dt_used"], 0.0001)

    def test_full_layer_profile_compiles_without_coordinate_mapping(self):
        frames = {
            "M0": {"target": vec(0.1), "provenance_ref": "obs:1"},
            "M1": {"target": vec(0.2)},
            "M2": {"target": vec(0.25), "transition_explicit": True},
            "M3": {"targets": [vec(0.3), vec(0.35)], "weights": [0.8, 0.7]},
            "M4": {"procedure_match": 1.0, "validator_confidence": 0.9, "capability_admission": 1.0},
            "M5": {"explicit": True, "salience_multiplier": 1.1},
            "M6": {"edges": [{"i": 2, "j": 3, "m": 1, "n": 1, "K": KAPPA, "R": 0.8}]},
            "M7": {"targets": [vec(0.4), vec(0.45)], "weights": [0.6, 0.5]},
            "M8": {"target": vec(0.0), "identity_ref": "crystal:root"},
            "M9": {"target": vec(0.5), "holonomy": vec(0.01)},
            "M10": {"append_only": True},
            "M11": {"validation_confidence": 0.95, "uncertainty": 0.1, "no_go": 0.0},
        }
        fabric = compile_gate_fabric(frames)
        self.assertEqual(set(fabric.layer_status), {f"M{i}" for i in range(12)})
        self.assertTrue(fabric.identity_anchor_present)
        step = qhtri_step(vec(0.0), vec(0.0), fabric, dt_requested=0.01)
        self.assertEqual(len(step["theta_after"]), 36)
        self.assertFalse(step["authority_grant"])
        self.assertFalse(step["execution_admitted"])


if __name__ == "__main__":
    unittest.main()
