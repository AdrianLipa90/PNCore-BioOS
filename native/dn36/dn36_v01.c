#include "dn36_v01.h"
#include "dn36_generated_constants_v01.h"

#include <limits.h>
#include <stdlib.h>
#include <string.h>

#define DN36_WORD_MASK UINT64_MAX
#define DN36_DOMAIN_LEN 15u

static const uint8_t DN36_DOMAIN[DN36_DOMAIN_LEN] = {
    'B','I','O','O','S','/','D','N','3','6','/','V','0','.','1'
};

static const uint8_t BASIS_N[DN36_DIM] = {
    1,1, 2,2,
    2,2,2,2,2,2,
    3,3,
    3,3,3,3,3,3,
    4,4,
    3,3,3,3,3,3,3,3,3,3,
    4,4,4,4,4,4
};

static const uint8_t BASIS_L[DN36_DIM] = {
    0,0, 0,0,
    1,1,1,1,1,1,
    0,0,
    1,1,1,1,1,1,
    0,0,
    2,2,2,2,2,2,2,2,2,2,
    1,1,1,1,1,1
};

static const int8_t BASIS_ML[DN36_DIM] = {
    0,0, 0,0,
    -1,-1,0,0,1,1,
    0,0,
    -1,-1,0,0,1,1,
    0,0,
    -2,-2,-1,-1,0,0,1,1,2,2,
    -1,-1,0,0,1,1
};

static const uint8_t BASIS_SPIN[DN36_DIM] = {
    0,1, 0,1,
    0,1,0,1,0,1,
    0,1,
    0,1,0,1,0,1,
    0,1,
    0,1,0,1,0,1,0,1,0,1,
    0,1,0,1,0,1
};

static const int8_t TETRA_SIGNS[4][3] = {
    { 1,  1,  1},
    { 1, -1, -1},
    {-1,  1, -1},
    {-1, -1,  1}
};

static uint64_t rotl64(uint64_t value, unsigned count) {
    count &= 63u;
    if (count == 0u) {
        return value;
    }
    return (value << count) | (value >> (64u - count));
}

static unsigned rotation(unsigned lane, unsigned round_index, unsigned branch) {
    const unsigned n = BASIS_N[lane];
    const unsigned ell = BASIS_L[lane];
    const int ml = BASIS_ML[lane];
    const unsigned spin = BASIS_SPIN[lane];
    const unsigned ml_shifted = (unsigned)(ml + (int)ell);
    return 1u + (
        11u * n
        + 7u * (ell + 1u)
        + 3u * ml_shifted
        + 13u * spin
        + 5u * round_index
        + 17u * branch
    ) % 63u;
}

static uint64_t load_le64(const uint8_t *p) {
    uint64_t out = 0u;
    for (unsigned i = 0u; i < 8u; ++i) {
        out |= ((uint64_t)p[i]) << (8u * i);
    }
    return out;
}

static void store_le64(uint8_t *p, uint64_t value) {
    for (unsigned i = 0u; i < 8u; ++i) {
        p[i] = (uint8_t)(value >> (8u * i));
    }
}

static size_t golden_mean_schedule(const uint8_t block[DN36_BLOCK_BYTES], uint8_t *schedule) {
    size_t cursor = 0u;
    for (size_t byte_index = 0u; byte_index < DN36_BLOCK_BYTES; ++byte_index) {
        const uint8_t byte = block[byte_index];
        for (int shift = 7; shift >= 0; --shift) {
            if (((byte >> (unsigned)shift) & 1u) != 0u) {
                schedule[cursor++] = 1u;
                schedule[cursor++] = 0u;
            } else {
                schedule[cursor++] = 0u;
            }
        }
    }
    return cursor;
}

static int build_frame(const uint8_t *payload, size_t payload_len, uint8_t **frame_out, size_t *block_count_out) {
    const size_t prefix_len = 2u + DN36_DOMAIN_LEN + 8u;
    if (payload_len > SIZE_MAX - prefix_len - 1u) {
        return -1;
    }
    const size_t frame_len = prefix_len + payload_len + 1u;
    if (frame_len > SIZE_MAX - (DN36_BLOCK_BYTES - 1u)) {
        return -1;
    }
    const size_t block_count = (frame_len + DN36_BLOCK_BYTES - 1u) / DN36_BLOCK_BYTES;
    if (block_count == 0u || block_count > SIZE_MAX / DN36_BLOCK_BYTES) {
        return -1;
    }
    const size_t padded_len = block_count * DN36_BLOCK_BYTES;
    uint8_t *frame = (uint8_t *)calloc(padded_len, 1u);
    if (frame == NULL) {
        return -1;
    }

    size_t cursor = 0u;
    frame[cursor++] = 0u;
    frame[cursor++] = (uint8_t)DN36_DOMAIN_LEN;
    memcpy(frame + cursor, DN36_DOMAIN, DN36_DOMAIN_LEN);
    cursor += DN36_DOMAIN_LEN;

    const uint64_t payload_u64 = (uint64_t)payload_len;
    for (unsigned i = 0u; i < 8u; ++i) {
        frame[cursor + i] = (uint8_t)(payload_u64 >> (56u - 8u * i));
    }
    cursor += 8u;
    if (payload_len != 0u) {
        if (payload == NULL) {
            free(frame);
            return -1;
        }
        memcpy(frame + cursor, payload, payload_len);
        cursor += payload_len;
    }
    frame[cursor] = 0x80u;

    *frame_out = frame;
    *block_count_out = block_count;
    return 0;
}

static void fold256_words(const uint64_t state[DN36_DIM], uint8_t fold_out[DN36_FOLD_BYTES]) {
    uint64_t acc[4] = {
        UINT64_C(0x243F6A8885A308D3),
        UINT64_C(0x13198A2E03707344),
        UINT64_C(0xA4093822299F31D0),
        UINT64_C(0x082EFA98EC4E6C89)
    };

    for (unsigned lane = 0u; lane < DN36_DIM; ++lane) {
        const unsigned bucket = lane & 3u;
        const uint64_t value = state[lane];
        acc[bucket] ^= rotl64(
            value + UINT64_C(0x9E3779B97F4A7C15) * (uint64_t)(lane + 1u),
            (7u * lane + 11u * bucket) % 63u + 1u
        );
        acc[(bucket + 1u) & 3u] += rotl64(
            value,
            (13u * lane + 17u) % 63u + 1u
        );
    }

    for (unsigned round_index = 0u; round_index < 8u; ++round_index) {
        uint64_t a = acc[0];
        uint64_t b = acc[1];
        uint64_t c = acc[2];
        uint64_t d = acc[3];
        a += b + UINT64_C(0x9E3779B97F4A7C15) * (uint64_t)(round_index + 1u);
        d = rotl64(d ^ a, 32u);
        c += d;
        b = rotl64(b ^ c, 24u);
        a += b;
        d = rotl64(d ^ a, 16u);
        c += d;
        b = rotl64(b ^ c, 63u);
        acc[0] = a;
        acc[1] = b;
        acc[2] = c;
        acc[3] = d;
    }

    for (unsigned i = 0u; i < 4u; ++i) {
        store_le64(fold_out + 8u * i, acc[i]);
    }
}

int dn36_commit_default_v01(
    const uint8_t *payload,
    size_t payload_len,
    uint8_t state_out[DN36_STATE_BYTES],
    uint8_t fold_out[DN36_FOLD_BYTES]
) {
    if (state_out == NULL || fold_out == NULL) {
        return -1;
    }

    uint8_t *frame = NULL;
    size_t block_count = 0u;
    if (build_frame(payload, payload_len, &frame, &block_count) != 0) {
        return -1;
    }

    uint64_t state[DN36_DIM];
    memcpy(state, DN36_INITIAL, sizeof(state));

    for (size_t block_index = 0u; block_index < block_count; ++block_index) {
        const uint8_t *block = frame + block_index * DN36_BLOCK_BYTES;
        uint8_t schedule[DN36_BLOCK_BYTES * 16u];
        const size_t schedule_len = golden_mean_schedule(block, schedule);
        if (schedule_len == 0u) {
            free(frame);
            return -1;
        }

        for (unsigned lane = 0u; lane < DN36_DIM; ++lane) {
            const uint64_t word = load_le64(block + 8u * lane);
            const uint64_t operator_word = (uint64_t)DN36_OPERATOR[lane] * UINT64_C(0x0101010101010101);
            state[lane] ^= word
                + operator_word
                + DN36_PHASE[lane]
                + (uint64_t)block_index * UINT64_C(0x9E3779B97F4A7C15);
            state[lane] = rotl64(
                state[lane],
                rotation(lane, (unsigned)(block_index % DN36_ROUNDS), 0u)
            );
        }

        for (unsigned round_index = 0u; round_index < DN36_ROUNDS; ++round_index) {
            uint64_t old[DN36_DIM];
            uint64_t next[DN36_DIM];
            memcpy(old, state, sizeof(old));
            memset(next, 0, sizeof(next));

            for (unsigned lane = 0u; lane < DN36_DIM; ++lane) {
                const unsigned j = DN36_ROUTE[(lane + round_index) % DN36_DIM];
                const unsigned k = DN36_ROUTE[(lane + 1u + 7u * round_index) % DN36_DIM];
                const unsigned q = DN36_ROUTE[(lane + 17u + 5u * round_index) % DN36_DIM];
                const int8_t *tetra = TETRA_SIGNS[(lane + round_index) & 3u];
                const unsigned gm_symbol = schedule[(round_index * DN36_DIM + lane) % schedule_len];

                const uint64_t a = old[lane]
                    + old[j]
                    + (uint64_t)(DN36_OPERATOR[lane] + 1u)
                        * (uint64_t)(round_index + 1u)
                        * UINT64_C(0x9E3779B1);
                const uint64_t b = rotl64(
                    old[k] ^ DN36_PHASE[lane],
                    rotation(lane, round_index, gm_symbol)
                );
                const uint64_t c = rotl64(
                    old[q] + DN36_PHASE[j],
                    rotation(j, round_index, 1u - gm_symbol)
                );

                uint64_t mixed = a ^ b;
                mixed = tetra[0] > 0 ? mixed + c : mixed ^ c;

                const uint64_t neighbor = rotl64(
                    old[(lane + 13u) % DN36_DIM],
                    (round_index + lane) % 63u + 1u
                );
                mixed = tetra[1] > 0 ? mixed ^ neighbor : mixed - neighbor;

                if (gm_symbol != 0u) {
                    mixed += rotl64(
                        old[(lane + 23u) % DN36_DIM] ^ c,
                        rotation(q, round_index, 1u)
                    );
                } else {
                    mixed ^= rotl64(
                        old[(lane + 23u) % DN36_DIM] + b,
                        rotation(q, round_index, 0u)
                    );
                }

                if (tetra[2] < 0) {
                    mixed ^= DN36_WORD_MASK;
                }

                const unsigned final_rotation = rotation(lane, round_index, gm_symbol)
                    ^ ((DN36_OPERATOR[j] & 31u) + 1u);
                next[DN36_ROUTE[lane]] = rotl64(mixed, final_rotation);
            }
            memcpy(state, next, sizeof(state));
        }

        for (unsigned lane = 0u; lane < DN36_DIM; ++lane) {
            state[lane] ^= rotl64(
                state[(lane + 1u) % DN36_DIM],
                (DN36_OPERATOR[lane] % 63u) + 1u
            );
        }
    }

    free(frame);

    for (unsigned lane = 0u; lane < DN36_DIM; ++lane) {
        store_le64(state_out + 8u * lane, state[lane]);
    }
    fold256_words(state, fold_out);
    return 0;
}
