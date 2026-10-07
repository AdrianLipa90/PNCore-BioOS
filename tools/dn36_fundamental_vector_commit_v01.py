from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import struct
from typing import Sequence

DIM = 36
WORD_MASK = (1 << 64) - 1
BLOCK_BYTES = DIM * 8
ROUNDS = 12
DOMAIN_DEFAULT = b"BIOOS/DN36/V0.1"
SCHEMA = "BIOOS_DN36_FUNDAMENTAL_VECTOR_COMMIT_V0_1"

# Frozen Resonant-Chemistry Aufbau36 ordering.
_SUBSHELLS = (
    ("1s", 1, 0),
    ("2s", 2, 0),
    ("2p", 2, 1),
    ("3s", 3, 0),
    ("3p", 3, 1),
    ("4s", 4, 0),
    ("3d", 3, 2),
    ("4p", 4, 1),
)

# Tetrahedral frame sign representatives from Resonant-Chemistry/TIR binding.
_TETRA_SIGNS = (
    (1, 1, 1),
    (1, -1, -1),
    (-1, 1, -1),
    (-1, -1, 1),
)


def basis36() -> tuple[tuple[int, str, int, int, int, int], ...]:
    slots: list[tuple[int, str, int, int, int, int]] = []
    for subshell, n, ell in _SUBSHELLS:
        for m_l in range(-ell, ell + 1):
            for spin in (0, 1):  # alpha, beta
                slots.append((len(slots), subshell, n, ell, m_l, spin))
    if len(slots) != DIM:
        raise RuntimeError(f"DN36 basis drift: {len(slots)} != {DIM}")
    return tuple(slots)


_BASIS36 = basis36()


def _rotl64(value: int, count: int) -> int:
    count &= 63
    value &= WORD_MASK
    if count == 0:
        return value
    return ((value << count) | (value >> (64 - count))) & WORD_MASK


def golden_mean_encode(raw: bytes) -> tuple[int, ...]:
    """Injective engineering morphism 0->0, 1->10 into the TIR no-11 language."""
    symbols: list[int] = []
    for byte in raw:
        for shift in range(7, -1, -1):
            if (byte >> shift) & 1:
                symbols.extend((1, 0))
            else:
                symbols.append(0)
    return tuple(symbols)


def golden_mean_decode(symbols: Sequence[int]) -> bytes:
    bits: list[int] = []
    i = 0
    values = tuple(int(x) for x in symbols)
    while i < len(values):
        symbol = values[i]
        if symbol == 1:
            if i + 1 >= len(values) or values[i + 1] != 0:
                raise ValueError("invalid golden-mean morphism stream")
            bits.append(1)
            i += 2
        elif symbol == 0:
            bits.append(0)
            i += 1
        else:
            raise ValueError("golden-mean stream must be binary")
    if len(bits) % 8:
        raise ValueError("decoded golden-mean stream is not byte aligned")
    out = bytearray()
    for offset in range(0, len(bits), 8):
        value = 0
        for bit in bits[offset : offset + 8]:
            value = (value << 1) | bit
        out.append(value)
    return bytes(out)


@lru_cache(maxsize=None)
def _genome_constants(domain: bytes) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """DNCrypt-v0.3-shaped deterministic constants; not secret material."""
    raw = hashlib.shake_256(domain + b"|DN36|GENOME").digest(DIM + 3 * DIM * 8)
    cursor = 0
    operator = tuple(raw[cursor : cursor + DIM])
    cursor += DIM

    route_keys = tuple(
        int.from_bytes(raw[cursor + 8 * i : cursor + 8 * i + 8], "little")
        for i in range(DIM)
    )
    cursor += DIM * 8
    route = tuple(sorted(range(DIM), key=lambda lane: (route_keys[lane], lane)))

    phase = tuple(
        int.from_bytes(raw[cursor + 8 * i : cursor + 8 * i + 8], "little")
        for i in range(DIM)
    )
    cursor += DIM * 8
    initial = tuple(
        int.from_bytes(raw[cursor + 8 * i : cursor + 8 * i + 8], "little")
        for i in range(DIM)
    )
    return operator, route, phase, initial


def _rotation(slot: tuple[int, str, int, int, int, int], round_index: int, branch: int) -> int:
    _, _, n, ell, m_l, spin = slot
    return 1 + (
        11 * n
        + 7 * (ell + 1)
        + 3 * (m_l + ell)
        + 13 * spin
        + 5 * round_index
        + 17 * branch
    ) % 63


def _framed_blocks(payload: bytes, domain: bytes) -> bytes:
    if len(domain) > 0xFFFF:
        raise ValueError("domain is too long")
    framed = (
        struct.pack(">H", len(domain))
        + domain
        + struct.pack(">Q", len(payload))
        + payload
        + b"\x80"
    )
    return framed + b"\x00" * ((-len(framed)) % BLOCK_BYTES)


def dn36_state(payload: bytes, *, domain: bytes = DOMAIN_DEFAULT) -> tuple[int, ...]:
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError("payload must be bytes-like")
    payload_bytes = bytes(payload)
    domain_bytes = bytes(domain)
    operator, route, phase, initial = _genome_constants(domain_bytes)
    state = list(initial)
    framed = _framed_blocks(payload_bytes, domain_bytes)

    for block_index, offset in enumerate(range(0, len(framed), BLOCK_BYTES)):
        block = framed[offset : offset + BLOCK_BYTES]
        words = struct.unpack("<36Q", block)
        schedule = golden_mean_encode(block)
        schedule_len = len(schedule)

        for lane, word in enumerate(words):
            operator_word = operator[lane] * 0x0101010101010101
            state[lane] ^= (
                word
                + operator_word
                + phase[lane]
                + block_index * 0x9E3779B97F4A7C15
            ) & WORD_MASK
            state[lane] = _rotl64(
                state[lane], _rotation(_BASIS36[lane], block_index % ROUNDS, 0)
            )

        for round_index in range(ROUNDS):
            old = state[:]
            new = [0] * DIM
            for lane in range(DIM):
                j = route[(lane + round_index) % DIM]
                k = route[(lane + 1 + 7 * round_index) % DIM]
                q = route[(lane + 17 + 5 * round_index) % DIM]
                tetra = _TETRA_SIGNS[(lane + round_index) % 4]
                gm_symbol = schedule[(round_index * DIM + lane) % schedule_len]

                a = (
                    old[lane]
                    + old[j]
                    + (operator[lane] + 1) * (round_index + 1) * 0x9E3779B1
                ) & WORD_MASK
                b = _rotl64(
                    old[k] ^ phase[lane],
                    _rotation(_BASIS36[lane], round_index, gm_symbol),
                )
                c = _rotl64(
                    (old[q] + phase[j]) & WORD_MASK,
                    _rotation(_BASIS36[j], round_index, 1 - gm_symbol),
                )

                mixed = a ^ b
                mixed = (mixed + c) & WORD_MASK if tetra[0] > 0 else mixed ^ c

                neighbor = _rotl64(old[(lane + 13) % DIM], (round_index + lane) % 63 + 1)
                mixed = mixed ^ neighbor if tetra[1] > 0 else (mixed - neighbor) & WORD_MASK

                if gm_symbol:
                    mixed = (
                        mixed
                        + _rotl64(
                            old[(lane + 23) % DIM] ^ c,
                            _rotation(_BASIS36[q], round_index, 1),
                        )
                    ) & WORD_MASK
                else:
                    mixed ^= _rotl64(
                        (old[(lane + 23) % DIM] + b) & WORD_MASK,
                        _rotation(_BASIS36[q], round_index, 0),
                    )

                if tetra[2] < 0:
                    mixed ^= WORD_MASK

                final_rotation = _rotation(_BASIS36[lane], round_index, gm_symbol) ^ (
                    (operator[j] & 31) + 1
                )
                new[route[lane]] = _rotl64(mixed, final_rotation)
            state = new

        for lane in range(DIM):
            state[lane] ^= _rotl64(
                state[(lane + 1) % DIM], (operator[lane] % 63) + 1
            )

    return tuple(value & WORD_MASK for value in state)


def state2304_bytes(state: Sequence[int]) -> bytes:
    values = tuple(int(value) for value in state)
    if len(values) != DIM or any(value < 0 or value > WORD_MASK for value in values):
        raise ValueError("state must contain exactly 36 uint64 lanes")
    return b"".join(struct.pack("<Q", value) for value in values)


def fold256(state: Sequence[int]) -> bytes:
    """Experimental fold only. No cryptographic-strength claim is attached."""
    values = tuple(int(value) for value in state)
    if len(values) != DIM:
        raise ValueError("state must contain 36 lanes")
    acc = [
        0x243F6A8885A308D3,
        0x13198A2E03707344,
        0xA4093822299F31D0,
        0x082EFA98EC4E6C89,
    ]
    for lane, value in enumerate(values):
        bucket = lane & 3
        acc[bucket] ^= _rotl64(
            (value + 0x9E3779B97F4A7C15 * (lane + 1)) & WORD_MASK,
            (7 * lane + 11 * bucket) % 63 + 1,
        )
        acc[(bucket + 1) & 3] = (
            acc[(bucket + 1) & 3]
            + _rotl64(value, (13 * lane + 17) % 63 + 1)
        ) & WORD_MASK

    for round_index in range(8):
        a, b, c, d = acc
        a = (a + b + 0x9E3779B97F4A7C15 * (round_index + 1)) & WORD_MASK
        d = _rotl64(d ^ a, 32)
        c = (c + d) & WORD_MASK
        b = _rotl64(b ^ c, 24)
        a = (a + b) & WORD_MASK
        d = _rotl64(d ^ a, 16)
        c = (c + d) & WORD_MASK
        b = _rotl64(b ^ c, 63)
        acc = [a, b, c, d]
    return b"".join(struct.pack("<Q", value) for value in acc)


@dataclass(frozen=True, slots=True)
class DN36Commitment:
    state2304: bytes
    fold256: bytes
    anchor256: bytes

    def receipt(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "status": "EXPERIMENTAL_MEASURED_CANDIDATE",
            "dimension": DIM,
            "rounds": ROUNDS,
            "state2304_hex": self.state2304.hex(),
            "fold256_hex": self.fold256.hex(),
            "anchor256_blake2b_hex": self.anchor256.hex(),
            "security_claim": False,
            "replacement_for_standard_hash": False,
            "canon_allowed": False,
        }


def commit(payload: bytes, *, domain: bytes = DOMAIN_DEFAULT) -> DN36Commitment:
    state = dn36_state(payload, domain=domain)
    state_bytes = state2304_bytes(state)
    candidate_fold = fold256(state)
    # Standard anchor remains mandatory during the experimental stage.
    anchor = hashlib.blake2b(
        state_bytes,
        digest_size=32,
        person=b"BioOS-DN36-v01",
    ).digest()
    return DN36Commitment(state_bytes, candidate_fold, anchor)
