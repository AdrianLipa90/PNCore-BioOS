#define _POSIX_C_SOURCE 200809L
#include "dn36_v01.h"

#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static int hex_nibble(char ch) {
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return 10 + ch - 'a';
    if (ch >= 'A' && ch <= 'F') return 10 + ch - 'A';
    return -1;
}

static int decode_hex(const char *text, uint8_t **out, size_t *out_len) {
    const size_t n = strlen(text);
    if ((n & 1u) != 0u) return -1;
    const size_t bytes_len = n / 2u;
    uint8_t *buf = NULL;
    if (bytes_len != 0u) {
        buf = (uint8_t *)malloc(bytes_len);
        if (buf == NULL) return -1;
    }
    for (size_t i = 0u; i < bytes_len; ++i) {
        const int hi = hex_nibble(text[2u * i]);
        const int lo = hex_nibble(text[2u * i + 1u]);
        if (hi < 0 || lo < 0) {
            free(buf);
            return -1;
        }
        buf[i] = (uint8_t)((hi << 4) | lo);
    }
    *out = buf;
    *out_len = bytes_len;
    return 0;
}

static void print_hex(const uint8_t *data, size_t n) {
    static const char HEX[] = "0123456789abcdef";
    for (size_t i = 0u; i < n; ++i) {
        putchar(HEX[data[i] >> 4]);
        putchar(HEX[data[i] & 15u]);
    }
}

static uint64_t elapsed_ns(const struct timespec *start, const struct timespec *end) {
    const uint64_t sec = (uint64_t)(end->tv_sec - start->tv_sec);
    const int64_t nsec = (int64_t)end->tv_nsec - (int64_t)start->tv_nsec;
    if (nsec >= 0) {
        return sec * UINT64_C(1000000000) + (uint64_t)nsec;
    }
    return (sec - 1u) * UINT64_C(1000000000) + (uint64_t)(nsec + INT64_C(1000000000));
}

static void sort5(double values[5]) {
    for (unsigned i = 1u; i < 5u; ++i) {
        const double value = values[i];
        unsigned j = i;
        while (j > 0u && values[j - 1u] > value) {
            values[j] = values[j - 1u];
            --j;
        }
        values[j] = value;
    }
}

static int commit_mode(const char *hex_payload) {
    uint8_t *payload = NULL;
    size_t payload_len = 0u;
    if (decode_hex(hex_payload, &payload, &payload_len) != 0) {
        fprintf(stderr, "invalid hex payload\n");
        return 2;
    }

    uint8_t state[DN36_STATE_BYTES];
    uint8_t fold[DN36_FOLD_BYTES];
    const int rc = dn36_commit_default_v01(payload, payload_len, state, fold);
    free(payload);
    if (rc != 0) {
        fprintf(stderr, "dn36 commit failed\n");
        return 3;
    }

    printf("{\"schema\":\"BIOOS_DN36_NATIVE_COMMIT_V0_1\",\"payload_bytes\":%zu,\"state2304_hex\":\"", payload_len);
    print_hex(state, sizeof(state));
    printf("\",\"fold256_hex\":\"");
    print_hex(fold, sizeof(fold));
    printf("\",\"security_claim\":false,\"canon_allowed\":false}\n");
    return 0;
}

static int bench_mode(const char *iterations_text, const char *hex_payload) {
    errno = 0;
    char *endptr = NULL;
    const unsigned long parsed = strtoul(iterations_text, &endptr, 10);
    if (errno != 0 || endptr == iterations_text || *endptr != '\0' || parsed == 0ul) {
        fprintf(stderr, "invalid iteration count\n");
        return 2;
    }

    uint8_t *payload = NULL;
    size_t payload_len = 0u;
    if (decode_hex(hex_payload, &payload, &payload_len) != 0) {
        fprintf(stderr, "invalid hex payload\n");
        return 2;
    }

    double samples[5];
    volatile uint8_t sink = 0u;
    for (unsigned trial = 0u; trial < 5u; ++trial) {
        struct timespec start;
        struct timespec end;
        if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
            free(payload);
            return 4;
        }
        for (unsigned long i = 0ul; i < parsed; ++i) {
            uint8_t state[DN36_STATE_BYTES];
            uint8_t fold[DN36_FOLD_BYTES];
            if (dn36_commit_default_v01(payload, payload_len, state, fold) != 0) {
                free(payload);
                return 3;
            }
            sink ^= fold[0];
        }
        if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
            free(payload);
            return 4;
        }
        samples[trial] = (double)elapsed_ns(&start, &end) / (double)parsed;
    }
    free(payload);
    sort5(samples);

    printf(
        "{\"schema\":\"BIOOS_DN36_NATIVE_BENCH_V0_1\","
        "\"implementation\":\"scalar_c_o3\","
        "\"payload_bytes\":%zu,"
        "\"iterations_per_trial\":%lu,"
        "\"trials\":5,"
        "\"min_ns_per_op\":%.9f,"
        "\"median_ns_per_op\":%.9f,"
        "\"max_ns_per_op\":%.9f,"
        "\"ops_per_s_from_median\":%.9f,"
        "\"gb_per_s_from_median\":%.12f,"
        "\"sink\":%u,"
        "\"security_claim\":false,"
        "\"canon_allowed\":false,"
        "\"claim_boundary\":\"scalar native C host measurement; no SIMD claim and no cryptographic validation\"}\n",
        payload_len,
        parsed,
        samples[0],
        samples[2],
        samples[4],
        1.0e9 / samples[2],
        (double)payload_len / samples[2],
        (unsigned)sink
    );
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3 && strcmp(argv[1], "--commit") == 0) {
        return commit_mode(argv[2]);
    }
    if (argc == 4 && strcmp(argv[1], "--bench") == 0) {
        return bench_mode(argv[2], argv[3]);
    }
    fprintf(stderr, "usage: %s --commit HEX | --bench ITERATIONS HEX\n", argv[0]);
    return 2;
}
