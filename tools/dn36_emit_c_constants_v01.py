from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.dn36_fundamental_vector_commit_v01 import DOMAIN_DEFAULT, _genome_constants


def _u8_row(name: str, values: tuple[int, ...]) -> str:
    body = ", ".join(str(int(value)) for value in values)
    return f"static const uint8_t {name}[36] = {{{body}}};"


def _u64_row(name: str, values: tuple[int, ...]) -> str:
    body = ", ".join(f"UINT64_C(0x{int(value):016x})" for value in values)
    return f"static const uint64_t {name}[36] = {{{body}}};"


def render_header() -> str:
    operator, route, phase, initial = _genome_constants(DOMAIN_DEFAULT)
    canonical = json.dumps(
        {
            "domain_hex": DOMAIN_DEFAULT.hex(),
            "operator": list(operator),
            "route": list(route),
            "phase": list(phase),
            "initial": list(initial),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    lines = [
        "#ifndef BIOOS_DN36_GENERATED_CONSTANTS_V01_H",
        "#define BIOOS_DN36_GENERATED_CONSTANTS_V01_H",
        "#include <stdint.h>",
        f"/* generator_receipt_sha256={digest} */",
        _u8_row("DN36_OPERATOR", operator),
        _u8_row("DN36_ROUTE", route),
        _u64_row("DN36_PHASE", phase),
        _u64_row("DN36_INITIAL", initial),
        "#endif",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    header = render_header()
    if args.out is None:
        print(header, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(header, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
