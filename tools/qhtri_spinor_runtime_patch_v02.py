from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path
from typing import Iterable

SCHEMA = "BIOOS-QHTRI-SPINOR-RUNTIME-PATCH/0.2"
PATCH_RELATIVE_PATH = Path("runtime_candidates/qhtri_spinor_v02/QHTRI_SPINOR_RUNTIME_V0_2.patch")
PATCH_SHA256 = "449438aa38b019be1612342619edbb370c3e97e1562a22331be18f0ef8c729fa"

SOURCE_SHA256 = {
    "ciel_geometry/noema_surface_mmap.py": "79d11a6b1f147173f6ccdd59187f1b9447f6e015e5858edf8c6634daa8b0e2bd",
    "ciel_geometry/phasenav/continuous_propagator.py": "9881e9fede149b2ed74e1085c1bfa516d856f4dfa59268cf2acf7e3ae7243205",
}

CANDIDATE_SHA256 = {
    "ciel_geometry/noema_surface_mmap.py": "ae1edfe99b929441c0d217f0af430b3721e6242149d0e91bcd54e83a2c3cda99",
    "ciel_geometry/phasenav/continuous_propagator.py": "1dcf02f21f0a60999b861c590dc3efaa836a600f0c634dfc5ad6f819fb5ea555",
}

CANDIDATE_MANIFEST_SHA256 = "7abaadfa7fbea0abd0b1bd54f77150847e57e9851b5b69ece508a97eca9a00d9"


class QhtriSpinorRuntimePatchError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_range(text: str) -> tuple[int, int]:
    if "," in text:
        start, count = text.split(",", 1)
        return int(start), int(count)
    return int(text), 1


def _apply_unified_file(source_lines: list[str], diff_lines: list[str]) -> list[str]:
    output: list[str] = []
    source_index = 0
    i = 0
    hunk_re = re.compile(r"^@@ -(\d+(?:,\d+)?) \+(\d+(?:,\d+)?) @@")
    while i < len(diff_lines):
        match = hunk_re.match(diff_lines[i])
        if not match:
            raise QhtriSpinorRuntimePatchError(f"expected hunk header, got: {diff_lines[i].rstrip()}")
        old_start, old_count = _parse_range(match.group(1))
        target_index = old_start - 1
        if target_index < source_index:
            raise QhtriSpinorRuntimePatchError("overlapping/out-of-order hunks")
        output.extend(source_lines[source_index:target_index])
        source_index = target_index
        consumed_old = 0
        i += 1
        while i < len(diff_lines) and not diff_lines[i].startswith("@@ "):
            line = diff_lines[i]
            if line.startswith("\\ No newline at end of file"):
                i += 1
                continue
            if not line:
                raise QhtriSpinorRuntimePatchError("malformed empty diff line")
            marker, payload = line[0], line[1:]
            if marker == " ":
                if source_index >= len(source_lines) or source_lines[source_index] != payload:
                    raise QhtriSpinorRuntimePatchError("context mismatch while applying spinor patch")
                output.append(payload)
                source_index += 1
                consumed_old += 1
            elif marker == "-":
                if source_index >= len(source_lines) or source_lines[source_index] != payload:
                    raise QhtriSpinorRuntimePatchError("removal mismatch while applying spinor patch")
                source_index += 1
                consumed_old += 1
            elif marker == "+":
                output.append(payload)
            else:
                raise QhtriSpinorRuntimePatchError(f"unsupported diff marker: {marker!r}")
            i += 1
        if consumed_old != old_count:
            raise QhtriSpinorRuntimePatchError(
                f"hunk old-count mismatch: consumed {consumed_old}, declared {old_count}"
            )
    output.extend(source_lines[source_index:])
    return output


def _split_patch(patch_text: str) -> list[tuple[str, list[str]]]:
    lines = patch_text.splitlines(keepends=True)
    result: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("--- a/"):
            raise QhtriSpinorRuntimePatchError(f"expected file header at line {i + 1}")
        old_path = lines[i][6:].strip()
        i += 1
        if i >= len(lines) or not lines[i].startswith("+++ b/"):
            raise QhtriSpinorRuntimePatchError("missing candidate file header")
        new_path = lines[i][6:].strip()
        if old_path != new_path:
            raise QhtriSpinorRuntimePatchError("spinor patch may not rename files")
        i += 1
        body: list[str] = []
        while i < len(lines) and not lines[i].startswith("--- a/"):
            body.append(lines[i])
            i += 1
        result.append((old_path, body))
    return result


def verify_source(source_root: str | Path) -> dict[str, str]:
    root = Path(source_root)
    actual: dict[str, str] = {}
    for rel, expected in SOURCE_SHA256.items():
        path = root / rel
        if not path.is_file():
            raise QhtriSpinorRuntimePatchError(f"missing pinned runtime source: {rel}")
        digest = _sha256(path)
        actual[rel] = digest
        if digest != expected:
            raise QhtriSpinorRuntimePatchError(
                f"SOURCE_HASH_MISMATCH {rel}: {digest} != {expected}"
            )
    return actual


def verify_candidate(candidate_root: str | Path) -> dict[str, str]:
    root = Path(candidate_root)
    actual: dict[str, str] = {}
    for rel, expected in CANDIDATE_SHA256.items():
        path = root / rel
        if not path.is_file():
            raise QhtriSpinorRuntimePatchError(f"missing generated candidate: {rel}")
        digest = _sha256(path)
        actual[rel] = digest
        if digest != expected:
            raise QhtriSpinorRuntimePatchError(
                f"CANDIDATE_HASH_MISMATCH {rel}: {digest} != {expected}"
            )
    return actual


def apply_pinned_patch(
    source_root: str | Path,
    output_root: str | Path,
    *,
    patch_path: str | Path,
) -> dict[str, object]:
    source = Path(source_root)
    output = Path(output_root)
    patch = Path(patch_path)
    verify_source(source)
    if not patch.is_file():
        raise QhtriSpinorRuntimePatchError("spinor patch artifact is missing")
    patch_digest = _sha256(patch)
    if patch_digest != PATCH_SHA256:
        raise QhtriSpinorRuntimePatchError(
            f"PATCH_HASH_MISMATCH: {patch_digest} != {PATCH_SHA256}"
        )
    if output.exists():
        raise QhtriSpinorRuntimePatchError("output_root already exists; refusing overwrite")
    shutil.copytree(source, output)
    try:
        for rel, hunks in _split_patch(patch.read_text("utf-8")):
            if rel not in SOURCE_SHA256:
                raise QhtriSpinorRuntimePatchError(f"undeclared patched file: {rel}")
            target = output / rel
            source_lines = target.read_text("utf-8").splitlines(keepends=True)
            candidate_lines = _apply_unified_file(source_lines, hunks)
            target.write_text("".join(candidate_lines), encoding="utf-8")
        generated = verify_candidate(output)
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return {
        "schema": SCHEMA,
        "source_sha256": dict(SOURCE_SHA256),
        "patch_sha256": PATCH_SHA256,
        "candidate_sha256": generated,
        "candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
        "status": "PASS",
        "promotion_state": "STAGED_CANDIDATE_ONLY",
    }
