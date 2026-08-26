.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry, @function

.set PN_PNVH,          0x5000
.set PN_SIGMA0,        0x5200
.set PN_EVIDENCE,      0x5300
.set PN_MAP_EVIDENCE,  0x5400
.set PN_SCHED_EVIDENCE,0x5500
.set PN_SCHED_POLICY_STATE,0x5540
.set PN_CLOCK_TEST_STATE,0x5600
.set PN_CLOCK_HW_STATE,  0x5680
.set PN_CLOCK_EVIDENCE,  0x5700
.set PN_PML4,          0x7000
.set PN_PDPT,          0x8000
.set PN_PD,            0x9000

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

pncore_entry:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'C'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC 0x0a

    # PNVector Handoff structural admission.
    cmpl $0x48564e50, PN_PNVH+0          # "PNVH"
    jne pncore_fail
    cmpl $0x00003633, PN_PNVH+4          # "36\0\0"
    jne pncore_fail
    cmpw $1, PN_PNVH+8                    # major
    jne pncore_fail
    cmpw $0, PN_PNVH+10                   # minor
    jne pncore_fail
    cmpl $128, PN_PNVH+12                 # header bytes
    jne pncore_fail
    cmpl $416, PN_PNVH+16                 # total bytes
    jne pncore_fail
    cmpw $36, PN_PNVH+20                  # vector dimension
    jne pncore_fail
    cmpw $8, PN_PNVH+22                   # float64 width
    jne pncore_fail
    cmpl $0x01020304, PN_PNVH+24          # LE endian marker
    jne pncore_fail
    movl PN_PNVH+28, %eax
    andl $0x7, %eax
    cmpl $0x7, %eax
    jne pncore_fail

    # MMU/page-walk substrate verification. Exact authority remains PNR/PNObject.
    movq %cr3, %rax
    andq $0xfffffffffffff000, %rax
    cmpq $PN_PML4, %rax
    jne pncore_fail
    cmpl $0x00008003, PN_PML4
    jne pncore_fail
    cmpl $0x00009003, PN_PDPT
    jne pncore_fail
    cmpl $0x00000083, PN_PD
    jne pncore_fail

    # Bind bounded page-walk evidence.
    movl $0x304d4e50, PN_MAP_EVIDENCE+0   # "PNM0"
    movl $1,          PN_MAP_EVIDENCE+4
    movl $PN_PML4,    PN_MAP_EVIDENCE+8
    movl $0x000f0000, PN_MAP_EVIDENCE+12  # selector VA inside ROM
    movl $0x00000000, PN_MAP_EVIDENCE+16  # resolved 2 MiB frame base
    movl $0x00000083, PN_MAP_EVIDENCE+20  # exact PDE authority bits
    movl $1,          PN_MAP_EVIDENCE+24

    # Validate PNR header and exact program/schedule identity bindings.
    movl $pnr_genesis_header, %ebx
    cmpl $0x31524e50, 0(%rbx)             # "PNR1"
    jne pncore_fail
    cmpl $1, 4(%rbx)
    jne pncore_fail
    cmpl $0x00008664, 8(%rbx)
    jne pncore_fail

    movl $pnr_genesis_program_digest, %esi
    movl $expected_genesis_program_digest, %edi
    movl $32, %ecx
    cld
    repe cmpsb
    jne pncore_fail

    movl $pnr_genesis_schedule_digest, %esi
    movl $expected_genesis_schedule_digest, %edi
    movl $32, %ecx
    repe cmpsb
    jne pncore_fail

    OUTC 'P'
    OUTC 'N'
    OUTC 'R'
    OUTC '.'
    OUTC 'O'
    OUTC 'K'
    OUTC 0x0a

    # Reaching this point is the lowered physical predicate:
    # boot.admission EQUAL 1 -> bioos.genesis.

    # Materialize first physical BioOS state record (Sigma_0 candidate).
    movl $0x30534e50, PN_SIGMA0+0         # "PNS0"
    movl $1,          PN_SIGMA0+4
    movl $pnr_genesis_program_digest, %esi
    movl $PN_SIGMA0+8, %edi
    movl $32, %ecx
    rep movsb
    movl $pnr_genesis_schedule_digest, %esi
    movl $PN_SIGMA0+40, %edi
    movl $32, %ecx
    rep movsb
    movl $pnr_genesis_header, PN_SIGMA0+72
    movl $PN_MAP_EVIDENCE, PN_SIGMA0+76
    movl $PN_PNVH, PN_SIGMA0+80
    movl $1, PN_SIGMA0+84
    # Bind exact PNVH vector digest and source-context digest into Sigma_0.
    movl $PN_PNVH+64, %esi
    movl $PN_SIGMA0+88, %edi
    movl $64, %ecx
    rep movsb

    # Transition evidence binds realization, Sigma, PNMap and PNVector state carrier.
    movl $0x30454e50, PN_EVIDENCE+0       # "PNE0"
    movl $1,          PN_EVIDENCE+4
    movl $pnr_genesis_header, PN_EVIDENCE+8
    movl $PN_SIGMA0,  PN_EVIDENCE+12
    movl $PN_MAP_EVIDENCE, PN_EVIDENCE+16
    movl $PN_PNVH, PN_EVIDENCE+20
    movl $1,          PN_EVIDENCE+24

    # PN Harmonic Scheduler physical selector self-test.
    movq $1, %rdi
    call pn_sched_classify_tick
    cmpl $1, %eax
    jne pncore_fail
    movq $2, %rdi
    call pn_sched_classify_tick
    cmpl $2, %eax
    jne pncore_fail
    movq $4, %rdi
    call pn_sched_classify_tick
    cmpl $3, %eax
    jne pncore_fail
    movq $8, %rdi
    call pn_sched_classify_tick
    cmpl $4, %eax
    jne pncore_fail
    movq $16, %rdi
    call pn_sched_classify_tick
    cmpl $5, %eax
    jne pncore_fail
    movq $32, %rdi
    call pn_sched_classify_tick
    cmpl $6, %eax
    jne pncore_fail
    movq $64, %rdi
    call pn_sched_classify_tick
    cmpl $7, %eax
    jne pncore_fail
    movq $128, %rdi
    call pn_sched_classify_tick
    cmpl $8, %eax
    jne pncore_fail
    movq $128, %rdi
    call pn_sched_admit_band
    testl %eax, %eax
    jne pncore_fail

    movl $0x43534e50, PN_SCHED_EVIDENCE+0  # "PNSC"
    movl $1,          PN_SCHED_EVIDENCE+4
    movl $7830,       PN_SCHED_EVIDENCE+8  # milli-Hz base
    movl $7,          PN_SCHED_EVIDENCE+12 # active B1..B7
    movl $1,          PN_SCHED_EVIDENCE+16 # B0 bounded service lane
    movl $1,          PN_SCHED_EVIDENCE+20 # no catch-up
    movl $1,          PN_SCHED_EVIDENCE+24 # running -> skip
    movl $1,          PN_SCHED_EVIDENCE+28 # >=B8 reserved quiet

    # Deterministic jitter demotion: 3 consecutive violations -> one slower band.
    movl $2, PN_SCHED_POLICY_STATE+0
    movl $0, PN_SCHED_POLICY_STATE+4
    movq $0, PN_SCHED_POLICY_STATE+8
    movl $PN_SCHED_POLICY_STATE, %edi
    movq $101, %rsi
    movq $100, %rdx
    call pn_sched_jitter_demote
    cmpl $2, %eax
    jne pncore_fail
    movl $PN_SCHED_POLICY_STATE, %edi
    movq $101, %rsi
    movq $100, %rdx
    call pn_sched_jitter_demote
    cmpl $2, %eax
    jne pncore_fail
    movl $PN_SCHED_POLICY_STATE, %edi
    movq $101, %rsi
    movq $100, %rdx
    call pn_sched_jitter_demote
    cmpl $3, %eax
    jne pncore_fail
    movl $PN_SCHED_POLICY_STATE, %edi
    movq $50, %rsi
    movq $100, %rdx
    call pn_sched_jitter_demote
    cmpl $3, %eax
    jne pncore_fail
    cmpl $0, PN_SCHED_POLICY_STATE+4
    jne pncore_fail
    movl $3, PN_SCHED_EVIDENCE+32 # consecutive-over threshold
    movl $0, PN_SCHED_EVIDENCE+36 # auto-promotion denied

    # PN Clock exact-rational physical realization self-test.
    # Synthetic ratio: crystal=24 MHz, numerator=125, denominator=1 -> 3 GHz TSC.
    movl $PN_CLOCK_TEST_STATE, %edi
    movl $1, %esi
    movl $125, %edx
    movl $24000000, %ecx
    movabsq $1000000000000, %r8
    call pn_clock_init_rational
    cmpl $1, %eax
    jne pncore_fail

    movl $PN_CLOCK_TEST_STATE, %edi
    movq $783, %rsi
    call pn_clock_deadline_for_tick
    movabsq $1300000000000, %rcx
    cmpq %rcx, %rax
    jne pncore_fail

    # Jump beyond tick 10 and verify direct future selection with skipped windows.
    movl $PN_CLOCK_TEST_STATE, %edi
    movq $10, %rsi
    call pn_clock_deadline_for_tick
    addq $17, %rax
    movq %rax, %rsi
    movl $PN_CLOCK_TEST_STATE, %edi
    call pn_clock_next_after_tsc
    cmpq %rsi, %rax
    jbe pncore_fail
    cmpq $11, PN_CLOCK_TEST_STATE+40
    jb pncore_fail
    cmpq $10, PN_CLOCK_TEST_STATE+56
    jb pncore_fail

    # Probe actual hardware. Failure leaves timed admission quiet; it does not invent a frequency.
    movl $PN_CLOCK_HW_STATE, %edi
    call pn_clock_probe_tsc_deadline_exact
    movl %eax, %r9d

    movl $0x4b434e50, PN_CLOCK_EVIDENCE+0   # "PNCK"
    movl $1,          PN_CLOCK_EVIDENCE+4
    movl $783,        PN_CLOCK_EVIDENCE+8
    movl $100,        PN_CLOCK_EVIDENCE+12
    movl $1,          PN_CLOCK_EVIDENCE+16  # rational self-test passed
    movl %r9d,       PN_CLOCK_EVIDENCE+20  # hw exact source admitted
    movl $1,          PN_CLOCK_EVIDENCE+24  # absolute phase-index policy
    movl $1,          PN_CLOCK_EVIDENCE+28  # missed windows skip
    movl $0,          PN_CLOCK_EVIDENCE+32  # catch-up forbidden
    movl $PN_CLOCK_HW_STATE, PN_CLOCK_EVIDENCE+36
    movl $PN_SCHED_POLICY_STATE, PN_CLOCK_EVIDENCE+40

    OUTC 'S'
    OUTC 'I'
    OUTC 'G'
    OUTC 'M'
    OUTC 'A'
    OUTC '0'
    OUTC 0x0a

pncore_halt:
    hlt
    jmp pncore_halt

pncore_fail:
    movw $0x00e9, %dx
    OUTC 'X'
    OUTC 0x0a
pncore_fail_halt:
    hlt
    jmp pncore_fail_halt

.section .rodata.pncore.expected,"a"
.align 16
expected_genesis_program_digest:
    .byte 0x4d, 0xd5, 0x96, 0x0a, 0xad, 0x4a, 0xde, 0x90, 0x29, 0x85, 0x91, 0x47, 0xc9, 0x0d, 0xb5, 0xb2, 0xf4, 0xfc, 0x83, 0x35, 0x34, 0x07, 0x78, 0x6e, 0x66, 0xe6, 0x47, 0x62, 0x79, 0xca, 0x89, 0x74
expected_genesis_schedule_digest:
    .byte 0xbd, 0x6e, 0x79, 0xf1, 0x14, 0x68, 0xa3, 0xd5, 0xe2, 0x44, 0xb8, 0xdf, 0x4a, 0xda, 0x6e, 0x3b, 0x74, 0x94, 0x18, 0x7c, 0xaa, 0x97, 0x1c, 0xad, 0x0a, 0x26, 0xea, 0x16, 0xca, 0xd3, 0x8c, 0x34

.section .note.GNU-stack,"",@progbits
