from __future__ import annotations

import hashlib
import importlib.util
import math
import struct
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "pnvector_handoff_builder_v01.py"
spec = importlib.util.spec_from_file_location("pnvector_handoff_builder_v01", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class PNVectorHandoffBuilderV01Tests(unittest.TestCase):
    def setUp(self):
        self.vector = struct.pack("<36d", *[i / 16.0 for i in range(36)])
        self.basis = hashlib.sha256(b"basis-test").digest()
        self.source = hashlib.sha256(b"source-test").digest()

    def test_exact_geometry_and_embedded_hash(self):
        block = mod.build(self.vector, self.basis, self.source, 0x7)
        self.assertEqual(len(block), 416)
        self.assertEqual(block[0:4], b"PNVH")
        self.assertEqual(block[4:8], b"36\x00\x00")
        self.assertEqual(block[32:64], self.basis)
        self.assertEqual(block[64:96], hashlib.sha256(self.vector).digest())
        self.assertEqual(block[96:128], self.source)
        self.assertEqual(block[128:], self.vector)
        info = mod.verify(block)
        self.assertEqual(info["flags"], 0x7)

    def test_vector_hash_tamper_fails_closed(self):
        block = bytearray(mod.build(self.vector, self.basis, self.source, 0x7))
        block[64] ^= 0x01
        with self.assertRaises(ValueError):
            mod.verify(bytes(block))

    def test_payload_tamper_fails_closed(self):
        block = bytearray(mod.build(self.vector, self.basis, self.source, 0x7))
        block[128] ^= 0x01
        with self.assertRaises(ValueError):
            mod.verify(bytes(block))

    def test_nonfinite_vector_rejected(self):
        values = [0.0] * 36
        values[9] = math.nan
        vector = struct.pack("<36d", *values)
        with self.assertRaises(ValueError):
            mod.build(vector, self.basis, self.source, 0x7)

    def test_wrong_vector_size_rejected(self):
        with self.assertRaises(ValueError):
            mod.build(self.vector[:-8], self.basis, self.source, 0x7)

    def test_wrong_basis_size_rejected(self):
        with self.assertRaises(ValueError):
            mod.build(self.vector, self.basis[:-1], self.source, 0x7)


if __name__ == "__main__":
    unittest.main()
