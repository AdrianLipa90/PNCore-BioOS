import math
import unittest
from math import gcd

from tools.t36_identity_record_v01 import (
    RECORD_BYTES,
    T36IdentityRecord,
    derive_configuration_sha256,
    derive_crystal_id,
    derive_genesis_anchor_commitment,
    derive_origin_binding_sha256,
)


class T36IdentityV01Tests(unittest.TestCase):
    def test_exact_clock_period_doubling_matches_b1(self):
        f0 = 783 / 100
        t0 = 100 / 783
        self.assertEqual(f0 / 2, 783 / 200)
        self.assertAlmostEqual(2 * t0, 200 / 783, places=15)
        self.assertAlmostEqual(1 / (2 * t0), 3.915, places=15)

    def test_spinor_sheet_and_four_pi_return(self):
        phi = 0.731
        def state(n: int) -> complex:
            theta = (phi + 2 * math.pi * n) / 2
            return complex(math.cos(theta), math.sin(theta))
        s0, s1, s2 = state(0), state(1), state(2)
        self.assertAlmostEqual(abs(s1 + s0), 0.0, places=12)
        self.assertAlmostEqual(abs(s2 - s0), 0.0, places=12)

    def test_identity_record_exact_256_byte_roundtrip(self):
        anchor = bytes(range(32))
        crystal_id = derive_crystal_id(anchor)
        commitment = derive_genesis_anchor_commitment(anchor)
        pnv, basis, source, rom, pnr, program, scheduler = (
            bytes([i]) * 32 for i in range(1, 8)
        )
        origin = derive_origin_binding_sha256(crystal_id, pnv, source, basis, pnr)
        cfg = derive_configuration_sha256(pnv, basis, source, rom, pnr, program, scheduler)
        record = T36IdentityRecord(
            flags=0x7,
            crystal_id=crystal_id,
            genesis_anchor_commitment=commitment,
            origin_binding_sha256=origin,
            pnvector_payload_sha256=pnv,
            source_context_sha256=source,
            basis_binding=basis,
            configuration_sha256=cfg,
            phase_index=11,
            boot_epoch=3,
        )
        raw = record.pack()
        self.assertEqual(len(raw), RECORD_BYTES)
        restored = T36IdentityRecord.unpack(raw)
        self.assertEqual(restored, record)
        self.assertEqual(restored.spinor_sheet, 1)

    def test_domain_separated_bindings_change_independently(self):
        anchor = b"a" * 32
        crystal = derive_crystal_id(anchor)
        commitment = derive_genesis_anchor_commitment(anchor)
        self.assertNotEqual(crystal, commitment)
        parts = [bytes([i]) * 32 for i in range(1, 8)]
        cfg = derive_configuration_sha256(*parts)
        origin = derive_origin_binding_sha256(crystal, parts[0], parts[2], parts[1], parts[4])
        self.assertNotEqual(cfg, origin)

    def test_configuration_change_does_not_change_crystal_id(self):
        anchor = b"a" * 32
        crystal = derive_crystal_id(anchor)
        cfg1 = derive_configuration_sha256(*(bytes([i]) * 32 for i in range(1, 8)))
        cfg2 = derive_configuration_sha256(*(bytes([i]) * 32 for i in range(2, 9)))
        self.assertNotEqual(cfg1, cfg2)
        self.assertEqual(crystal, derive_crystal_id(anchor))

    def test_stage2_ratio_box_count_and_worst_composition(self):
        candidates = []
        for q in range(1, 17):
            for p in range(1, 65):
                if 0.25 <= p / q <= 4.0 and gcd(p, q) == 1:
                    candidates.append((p, q))
        self.assertEqual(len(candidates), 301)

        worst = None
        for p1, q1 in candidates:
            for p2, q2 in candidates:
                num, den = p1 * q2, q1 * p2
                g = gcd(num, den)
                m, n = num // g, den // g
                load = m * m + n * n
                if worst is None or load > worst[0]:
                    worst = (load, (p1, q1), (p2, q2), (m, n))
        self.assertEqual(worst, (1784161, (59, 15), (63, 16), (944, 945)))

    def test_worst_ratio_requires_10474_substeps(self):
        kappa = math.log(2) / (24 * math.pi)
        l_bound = kappa * 1784161
        t0 = 100 / 783
        n_sub = math.ceil(t0 * l_bound / 0.2)
        self.assertEqual(n_sub, 10474)

    def test_dense_1_to_1_graph_fits_one_base_tick(self):
        kappa = math.log(2) / (24 * math.pi)
        l_bound = 630 * (kappa / 35) * 2
        dt_safe = 0.2 / l_bound
        self.assertAlmostEqual(l_bound, 36 * kappa, places=15)
        self.assertGreater(dt_safe, 100 / 783)


if __name__ == "__main__":
    unittest.main()
