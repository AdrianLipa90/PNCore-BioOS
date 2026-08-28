import math
import unittest

from tools.qhtri_phase_logic_v01 import (
    boolean_phase,
    coherence_and,
    coherence_or,
    coherence_truth,
    equatorial_cp1_overlap_squared,
    phase_not,
    phase_xnor,
    phase_xor,
    vector_phase_not,
    vector_xnor,
    vector_xor,
)


class QHTRIPhaseLogicTests(unittest.TestCase):
    def test_boolean_boundary_truth_table_is_exact(self):
        for a in (0, 1):
            for b in (0, 1):
                ta = boolean_phase(a)
                tb = boolean_phase(b)
                self.assertEqual(phase_xor(ta, tb), float(bool(a) ^ bool(b)))
                self.assertEqual(phase_xnor(ta, tb), float(not (bool(a) ^ bool(b))))
                aa = coherence_truth(ta)
                bb = coherence_truth(tb)
                self.assertEqual(coherence_and(aa, bb), float(bool(a) and bool(b)))
                self.assertEqual(coherence_or(aa, bb), float(bool(a) or bool(b)))

    def test_not_is_pi_translation(self):
        for theta in (0.0, 0.2, -1.7, math.pi):
            self.assertAlmostEqual(
                coherence_truth(phase_not(theta)),
                1.0 - coherence_truth(theta),
                places=14,
            )

    def test_xnor_is_qhtri_lock_coherence(self):
        self.assertAlmostEqual(phase_xnor(0.4, 0.4), 1.0, places=15)
        self.assertAlmostEqual(phase_xnor(0.4, 0.4 + math.pi), 0.0, places=15)

    def test_xor_is_qhtri_antilock_coherence(self):
        self.assertAlmostEqual(phase_xor(0.4, 0.4), 0.0, places=15)
        self.assertAlmostEqual(phase_xor(0.4, 0.4 + math.pi), 1.0, places=15)

    def test_equatorial_cp1_overlap_is_same_scalar(self):
        for a, b in ((0.0, 0.0), (0.2, 1.1), (-2.0, 0.7), (math.pi, 0.0)):
            self.assertAlmostEqual(
                equatorial_cp1_overlap_squared(a, b),
                phase_xnor(a, b),
                places=15,
            )

    def test_t36_vector_logic_preserves_whole_lane_shape(self):
        a = [i * 0.01 for i in range(36)]
        b = [i * -0.02 for i in range(36)]
        self.assertEqual(len(vector_phase_not(a)), 36)
        self.assertEqual(len(vector_xor(a, b)), 36)
        self.assertEqual(len(vector_xnor(a, b)), 36)


if __name__ == "__main__":
    unittest.main()
