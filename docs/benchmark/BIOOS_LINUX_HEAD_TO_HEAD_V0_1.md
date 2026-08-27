# BioOS vs Linux same-host head-to-head v0.1

Status: `PASS_HOST_REFERENCE`  
Epistemic: `MEASURED_HOST_REFERENCE`  
Canon: `false`

## Scope

This benchmark compares the exact Terminal36D V8 host runtime against Linux controls on the same host and the same deterministic 288-byte payload. It is deliberately conservative: Linux primitive and IPC controls are compiled native C/OpenSSL (`-O3 -march=native`), while BioOS is the current Python host runtime.

This is not a bare-metal BioOS benchmark and not a universal Linux comparison.

Host: `INTEL(R) XEON(R) PLATINUM 8573C`, Linux `6.18.35`, Python `3.13.5`.

Exact runtime hashes:

- `terminal36d.py` — `78082702c4b7a17a061ca7b9b83f4c21765307c70dfbefd301466224389cce9b`
- `vector_kernel.py` — `68663aea2c188b77b46e5ecf2488bfdfb27a7f2cd8387fb78b6bc5dce6de0e14`
- `concept_gates.py` — `a3aeda6f1ca0c445767bba8176c5b6c7d791bd97e03b33fe2ed8dccb9c97bc49`

Payload SHA-256: `5643c75565a50bf65726c84ada2f5d78192774edc7cb9437d5725302d1409287`.

## Median latency

| Path | Median us/op | ops/s | Relative to BioOS full |
|---|---:|---:|---:|
| Linux native C SHA-256 | 0.508 | 1967667 | 0.013x |
| Linux mmap local copy + hash | 0.503 | 1988969 | 0.013x |
| Linux tmpfs pwrite+pread+hash | 0.964 | 1037313 | 0.025x |
| BioOS direct PHASENAV_HASH_BATCH | 1.169 | 855142 | 0.030x |
| Linux pipe process + hash | 26.514 | 37716 | 0.682x |
| Linux shared mmap process + hash | 37.463 | 26693 | 0.964x |
| Linux Unix socket process + hash | 38.055 | 26277 | 0.979x |
| BioOS full Terminal36D.execute | 38.880 | 25720 | 1.000x |
| Linux fork/exec sha256sum | 1981.076 | 505 | 50.953x |

## Direct findings

The direct BioOS hash primitive is only **2.30x slower** than an optimized native-C SHA-256 call while returning the existing BioOS structured result.

Against Linux cross-process paths, the direct BioOS hot primitive is:

- **22.67x faster** than a persistent pipe worker;
- **32.04x faster** than a shared-mmap worker with synchronization;
- **32.54x faster** than a Unix-socket worker;
- **1694.1x faster** than fork/exec per operation.

The full BioOS `Terminal36D.execute()` path is:

- 1.47x the latency of the native-C pipe path;
- within **3.8%** of the shared-mmap process path;
- within **2.2%** of the Unix-socket process path;
- **50.95x faster** than fork/exec.

This full path also performs the Terminal36D concept gate, typed capability dispatch, timestamps, structured result construction and content-addressed receipt hashing. Receipts were kept in memory; disk receipt persistence was disabled for this benchmark.

## Boundary

The result supports a strong architectural statement: retaining work inside the BioOS resident/vector hot path can remove process/IPC overhead by one to three orders of magnitude depending on the Linux comparison path. It does not establish that every BioOS operation is faster than a Linux syscall or native in-process function. Native C remains faster for the raw primitive.

PNStore durability, device-backed I/O, QEMU/bare-metal execution, networking and audio require separate head-to-head gates.

Receipt: `71660810c8685402271fa49afdf346e13c6529111ba2f7694df4f3f1454840ba`.
