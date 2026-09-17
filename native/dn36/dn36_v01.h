#ifndef BIOOS_DN36_V01_H
#define BIOOS_DN36_V01_H

#include <stddef.h>
#include <stdint.h>

#define DN36_DIM 36u
#define DN36_BLOCK_BYTES (DN36_DIM * 8u)
#define DN36_STATE_BYTES DN36_BLOCK_BYTES
#define DN36_FOLD_BYTES 32u
#define DN36_ROUNDS 12u

/*
 * Native v0.1 supports the pinned BIOOS/DN36/V0.1 domain profile only.
 * Constants for that profile are generated from the Python reference.
 */
int dn36_commit_default_v01(
    const uint8_t *payload,
    size_t payload_len,
    uint8_t state_out[DN36_STATE_BYTES],
    uint8_t fold_out[DN36_FOLD_BYTES]
);

#endif
