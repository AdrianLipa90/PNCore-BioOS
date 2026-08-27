from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

from tools.identity_nexus_v01 import compute_identity_nexus

PINNED_DICTIONARY_COMMIT = "3aa1651da9735d94d2a9cbffec13203eeeedd502"
PINNED_DICTIONARY_BRANCH = "feat/t36-identity-nexus-projection"


def _sha_jsonl(rows: list[dict]) -> str:
    raw = "".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in rows).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _git_head(repo: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        ).strip()
    except Exception as exc:
        raise RuntimeError("Dictionary source must be an exact Git checkout with readable HEAD") from exc
    if len(out) != 40:
        raise RuntimeError("invalid Dictionary Git HEAD")
    return out


def _phase36(path: Path) -> list[float]:
    raw = path.read_bytes()
    if len(raw) != 288:
        raise ValueError("PAUX-EXACT input must be exactly 288 bytes")
    values = list(struct.unpack("<36d", raw))
    if not all(math.isfinite(x) for x in values):
        raise ValueError("PAUX-EXACT input contains non-finite values")
    return values


def _load_context(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") == "PNV-T36-CRYSTAL-CONTEXT/0.1":
        return raw
    try:
        ctx = raw["metadata"]["t36_identity"]
    except (KeyError, TypeError) as exc:
        raise ValueError("crystal context file must be context or State Memory checkpoint") from exc
    out = dict(ctx)
    if raw.get("object_id"):
        out["source_object_id"] = raw["object_id"]
    return out


def build_live_nexus(
    *,
    dictionary_repo: Path,
    paux_exact: Path,
    crystal_context: Path,
    expected_commit: str = PINNED_DICTIONARY_COMMIT,
    active_limit: int = 16,
) -> tuple[dict, dict]:
    repo = dictionary_repo.resolve()
    actual_head = _git_head(repo)
    if actual_head != expected_commit:
        raise RuntimeError(f"Dictionary commit mismatch: expected {expected_commit}, got {actual_head}")

    sys.path.insert(0, str(repo / "src"))
    try:
        registry_mod = importlib.import_module("consciousness_dictionary.registry")
        compiler_mod = importlib.import_module("consciousness_dictionary.compiler")
        query_mod = importlib.import_module("consciousness_dictionary.query")

        receipt_path = repo / "artifacts" / "v0.2-alpha" / "COMPILE_RECEIPT.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        lexicon = registry_mod.Lexicon.load(
            repo / "ontology" / "registry" / "v0_2",
            repo / "ontology" / "relations" / "extra_relations.jsonl",
        )
        states = compiler_mod.compile_states(lexicon)
        relations = compiler_mod.compile_relation_observables(lexicon, states)
        state_sha = _sha_jsonl(states)
        relation_sha = _sha_jsonl(relations)
        if len(states) != int(receipt["states"]):
            raise RuntimeError("Dictionary state count does not match compile receipt")
        if len(relations) != int(receipt["relations"]):
            raise RuntimeError("Dictionary relation count does not match compile receipt")
        if state_sha != receipt["state_sha256"]:
            raise RuntimeError("Dictionary current states do not reproduce compile receipt")
        if relation_sha != receipt["relation_sha256"]:
            raise RuntimeError("Dictionary current relations do not reproduce compile receipt")

        phase = _phase36(paux_exact)
        rows = query_mod.external_phase_projection(lexicon, phase, limit=len(states))
        context = _load_context(crystal_context)
        binding = {
            "repository": "AdrianLipa90/The-Consciousness-Dictionary",
            "branch": PINNED_DICTIONARY_BRANCH,
            "commit": actual_head,
            "states": receipt["states"],
            "relations": receipt["relations"],
            "state_sha256": receipt["state_sha256"],
            "relation_sha256": receipt["relation_sha256"],
        }
        nexus = compute_identity_nexus(
            crystal_context=context,
            dictionary_binding=binding,
            projection_rows=rows,
            active_limit=active_limit,
        )
        evidence = {
            "schema": "IDENTITY_NEXUS_DICTIONARY_HYDRATION_RECEIPT_V0_1",
            "status": "PASS_DICTIONARY_REPRODUCTION_AND_PROJECTION",
            "dictionary_commit": actual_head,
            "states": len(states),
            "relations": len(relations),
            "state_sha256": state_sha,
            "relation_sha256": relation_sha,
            "paux_exact_sha256": hashlib.sha256(paux_exact.read_bytes()).hexdigest(),
            "crystal_id": nexus["crystal"]["crystal_id"],
            "nexus_generation_id": nexus["nexus_generation_id"],
            "nexus_coherence": nexus["nexus_coherence"],
            "active_count": len(nexus["active_terms"]),
            "authority_grant": False,
        }
        return nexus, evidence
    finally:
        try:
            sys.path.remove(str(repo / "src"))
        except ValueError:
            pass


def main() -> int:
    p = argparse.ArgumentParser(description="Hydrate BioOS Identity NEXUS from exact Consciousness Dictionary checkout")
    p.add_argument("--dictionary-repo", type=Path, required=True)
    p.add_argument("--paux-exact", type=Path, required=True)
    p.add_argument("--crystal-context", type=Path, required=True)
    p.add_argument("--expected-dictionary-commit", default=PINNED_DICTIONARY_COMMIT)
    p.add_argument("--active-limit", type=int, default=16)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--receipt", type=Path)
    a = p.parse_args()
    nexus, receipt = build_live_nexus(
        dictionary_repo=a.dictionary_repo,
        paux_exact=a.paux_exact,
        crystal_context=a.crystal_context,
        expected_commit=a.expected_dictionary_commit,
        active_limit=a.active_limit,
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(nexus, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.receipt:
        a.receipt.parent.mkdir(parents=True, exist_ok=True)
        a.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
