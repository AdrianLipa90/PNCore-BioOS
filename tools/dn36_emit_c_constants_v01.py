from __future__ import annotations

import hashlib
import json

from tools.dn36_fundamental_vector_commit_v01 import DOMAIN_DEFAULT, _genome_constants


def _u8_row(name: str, values: tuple[int, ...]) -> str:
    body = ", ".join(str(int(value)) for value in values)
    return f"static const uint8_t {name}[36] = {{{body}}};"


def _u64_row(name: str, values: tuple[int, ...]) -> str:
    body = ", ".join(f"UINT64_C(0x{int(value):016x})" for value in values)
    return f"static const uint64_t {name}[36] = {{{body}}};"


def main() -> int:
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
    print("#ifndef BIOOS_DN36_GENERATED_CONSTANTS_V01_H")
    print("#define BIOOS_DN36_GENERATED_CONSTANTS_V01_H")
    print("#include <stdint.h>")
    print(f"/* generator_receipt_sha256={digest} */")
    print(_u8_row("DN36_OPERATOR", operator))
    print(_u8_row("DN36_ROUTE", route))
    print(_u64_row("DN36_PHASE", phase))
    print(_u64_row("DN36_INITIAL", initial))
    print("#endif")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
