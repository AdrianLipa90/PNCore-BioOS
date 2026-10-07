from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping

from tools.dn36_fundamental_vector_commit_v01 import commit

SCHEMA = "BIOOS_DN36_DNCRYPT_AUX_BINDING_V0_1"
AAD_SCHEMA = "BIOOS_DNCRYPT_USER_AAD_WITH_DN36_AUX_V0_1"
BINDING_PREFIX = b"BIOOS/DN36/DNCRYPT-AUX/V0.1\x00"
DN36_DOMAIN = b"BIOOS/DN36/V0.1"
PAUX_EXACT_BYTES = 288


class DN36DNCryptBindingError(ValueError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise DN36DNCryptBindingError("value is not canonical-JSON serializable") from exc


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _u32be(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 0xFFFFFFFF:
        raise DN36DNCryptBindingError("length outside uint32 range")
    return value.to_bytes(4, "big")


def _validate_paux(paux_exact: bytes | bytearray | memoryview) -> bytes:
    if not isinstance(paux_exact, (bytes, bytearray, memoryview)):
        raise DN36DNCryptBindingError("PAUX payload must be bytes-like")
    raw = bytes(paux_exact)
    if len(raw) != PAUX_EXACT_BYTES:
        raise DN36DNCryptBindingError(
            f"PAUX-EXACT payload must be exactly {PAUX_EXACT_BYTES} bytes"
        )
    return raw


def _validate_core(core: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(core, Mapping):
        raise DN36DNCryptBindingError("AAD core must be a mapping")
    clean = dict(core)
    if "dn36_aux" in clean:
        raise DN36DNCryptBindingError("AAD core must not contain dn36_aux")
    if not isinstance(clean.get("object_id"), str) or not clean["object_id"]:
        raise DN36DNCryptBindingError("AAD core requires non-empty object_id")
    canonical_json_bytes(clean)
    return clean


def binding_input(paux_exact: bytes, aad_core: Mapping[str, Any]) -> bytes:
    paux = _validate_paux(paux_exact)
    core = _validate_core(aad_core)
    core_raw = canonical_json_bytes(core)
    return (
        BINDING_PREFIX
        + _u32be(len(paux))
        + paux
        + _u32be(len(core_raw))
        + core_raw
    )


@dataclass(frozen=True)
class DN36AuxRecord:
    schema: str
    profile: str
    paux_exact_bytes: int
    paux_sha256: str
    aad_core_sha256: str
    binding_input_sha256: str
    state2304_sha256: str
    fold256_hex: str
    standard_anchor: str
    security_claim: bool
    identity_authority: bool
    aead_authority: bool
    canon_allowed: bool

    def payload(self) -> dict[str, object]:
        return asdict(self)


def build_aux_record(paux_exact: bytes, aad_core: Mapping[str, Any]) -> DN36AuxRecord:
    paux = _validate_paux(paux_exact)
    core = _validate_core(aad_core)
    core_raw = canonical_json_bytes(core)
    material = binding_input(paux, core)
    result = commit(material, domain=DN36_DOMAIN)
    return DN36AuxRecord(
        schema=SCHEMA,
        profile="DN36_AUXILIARY_NON_AUTHORITY_V0_1",
        paux_exact_bytes=len(paux),
        paux_sha256=_sha256(paux),
        aad_core_sha256=_sha256(core_raw),
        binding_input_sha256=_sha256(material),
        state2304_sha256=_sha256(result.state2304),
        fold256_hex=result.fold256.hex(),
        standard_anchor=f"blake2b-256:{result.anchor256.hex()}",
        security_claim=False,
        identity_authority=False,
        aead_authority=False,
        canon_allowed=False,
    )


def build_authenticated_user_aad(
    paux_exact: bytes,
    aad_core: Mapping[str, Any],
) -> bytes:
    core = _validate_core(aad_core)
    aux = build_aux_record(paux_exact, core).payload()
    envelope = {
        "schema": AAD_SCHEMA,
        "core": core,
        "dn36_aux": aux,
    }
    return canonical_json_bytes(envelope)


def parse_authenticated_user_aad(raw: bytes | bytearray | memoryview) -> dict[str, Any]:
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise DN36DNCryptBindingError("authenticated user AAD must be bytes-like")
    try:
        value = json.loads(bytes(raw).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DN36DNCryptBindingError("authenticated user AAD is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict) or value.get("schema") != AAD_SCHEMA:
        raise DN36DNCryptBindingError("authenticated user AAD schema mismatch")
    if canonical_json_bytes(value) != bytes(raw):
        raise DN36DNCryptBindingError("authenticated user AAD is not canonical JSON")
    core = value.get("core")
    aux = value.get("dn36_aux")
    if not isinstance(core, dict) or not isinstance(aux, dict):
        raise DN36DNCryptBindingError("authenticated user AAD core/dn36_aux missing")
    _validate_core(core)
    return value


def verify_authenticated_user_aad(
    paux_exact: bytes,
    authenticated_user_aad: bytes,
    *,
    expected_core: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    paux = _validate_paux(paux_exact)
    parsed = parse_authenticated_user_aad(authenticated_user_aad)
    core = _validate_core(parsed["core"])

    if expected_core is not None:
        expected = _validate_core(expected_core)
        if canonical_json_bytes(core) != canonical_json_bytes(expected):
            raise DN36DNCryptBindingError("authenticated AAD core does not match expected core")

    recomputed = build_aux_record(paux, core).payload()
    supplied = parsed["dn36_aux"]
    if canonical_json_bytes(supplied) != canonical_json_bytes(recomputed):
        raise DN36DNCryptBindingError("DN36 auxiliary commitment mismatch")

    return {
        "schema": "BIOOS_DN36_DNCRYPT_AUX_VERIFY_V0_1",
        "status": "PASS",
        "object_id": core["object_id"],
        "paux_sha256": recomputed["paux_sha256"],
        "aad_core_sha256": recomputed["aad_core_sha256"],
        "state2304_sha256": recomputed["state2304_sha256"],
        "fold256_hex": recomputed["fold256_hex"],
        "standard_anchor": recomputed["standard_anchor"],
        "security_claim": False,
        "identity_authority": False,
        "aead_authority": False,
        "canon_allowed": False,
    }
