.section .pnr.genesis,"a"
.align 16
.global pnr_genesis_header
.global pnr_genesis_program_digest
.global pnr_genesis_schedule_digest

# PN Realization v0.1: architecture-specific physical realization metadata.
pnr_genesis_header:
    .long 0x31524e50              # "PNR1"
    .long 1                       # version
    .long 0x00008664              # x86_64 architecture id
    .long 0x00000001              # identity-bound realization flag
pnr_genesis_program_digest:
    .byte 0x4d, 0xd5, 0x96, 0x0a, 0xad, 0x4a, 0xde, 0x90, 0x29, 0x85, 0x91, 0x47, 0xc9, 0x0d, 0xb5, 0xb2, 0xf4, 0xfc, 0x83, 0x35, 0x34, 0x07, 0x78, 0x6e, 0x66, 0xe6, 0x47, 0x62, 0x79, 0xca, 0x89, 0x74
pnr_genesis_schedule_digest:
    .byte 0xbd, 0x6e, 0x79, 0xf1, 0x14, 0x68, 0xa3, 0xd5, 0xe2, 0x44, 0xb8, 0xdf, 0x4a, 0xda, 0x6e, 0x3b, 0x74, 0x94, 0x18, 0x7c, 0xaa, 0x97, 0x1c, 0xad, 0x0a, 0x26, 0xea, 0x16, 0xca, 0xd3, 0x8c, 0x34
pnr_genesis_composition_digest:
    .byte 0x8f, 0xf8, 0x3e, 0xa0, 0x5b, 0x1c, 0x4e, 0x57, 0x4b, 0xb5, 0x24, 0xc3, 0x21, 0x52, 0x8f, 0xa8, 0x31, 0xe8, 0x81, 0xef, 0x34, 0x9d, 0xd3, 0x05, 0x16, 0x54, 0xc7, 0x54, 0xde, 0xa8, 0x19, 0x4a
    .long pncore_entry             # physical entry point
    .long 0x00005200               # Sigma_0 target
    .long 0x00005400               # PNMap/MMU evidence target
    .long 0x00005000               # PNVector Handoff target
    .long 0x00005300               # transition evidence target
    .long 0x00005500               # harmonic scheduler evidence target
    .long pn_sched_classify_tick   # physical dyadic selector
    .long pn_sched_jitter_demote    # bounded slower-band demotion policy
    .long 0x00005700               # PN Clock evidence target
    .long pn_clock_probe_tsc_deadline_exact # exact hardware clock probe
    .long pn_clock_deadline_for_tick       # absolute phase-index mapper
    .long 0x00005800               # PNStore media evidence target
    .long pnstore_prepare_commit    # append-only extent preparation
    .long pnstore_publish_head      # alternating HEAD publication
    .long pnstore_recover           # verified dual-HEAD recovery
    .long 176                      # complete PNR header bytes
