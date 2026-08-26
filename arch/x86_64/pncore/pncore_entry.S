.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry, @function

.set PN_PNVH,          0x5000
.set PN_SIGMA0,        0x5200
.set PN_EVIDENCE,      0x5300
.set PN_MAP_EVIDENCE,  0x5400
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
    cmpl $0x48564e50, PN_PNVH+0
    jne pncore_fail
    cmpl $0x00003633, PN_PNVH+4
    jne pncore_fail
    cmpw $1, PN_PNVH+8
    jne pncore_fail
    cmpw $0, PN_PNVH+10
    jne pncore_fail
    cmpl $128, PN_PNVH+12
    jne pncore_fail
    cmpl $416, PN_PNVH+16
    jne pncore_fail
    cmpw $36, PN_PNVH+20
    jne pncore_fail
    cmpw $8, PN_PNVH+22
    jne pncore_fail
    cmpl $0x01020304, PN_PNVH+24
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

    movl $0x304d4e50, PN_MAP_EVIDENCE+0
    movl $1, PN_MAP_EVIDENCE+4
    movl $PN_PML4, PN_MAP_EVIDENCE+8
    movl $0x000f0000, PN_MAP_EVIDENCE+12
    movl $0x00000000, PN_MAP_EVIDENCE+16
    movl $0x00000083, PN_MAP_EVIDENCE+20
    movl $1, PN_MAP_EVIDENCE+24

    # Validate PNR header and exact program/schedule identity bindings.
    movl $pnr_genesis_header, %ebx
    cmpl $0x31524e50, 0(%rbx)
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

    movl $0x30534e50, PN_SIGMA0+0
    movl $1, PN_SIGMA0+4
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
    movl $PN_PNVH+64, %esi
    movl $PN_SIGMA0+88, %edi
    movl $64, %ecx
    rep movsb

    movl $0x30454e50, PN_EVIDENCE+0
    movl $1, PN_EVIDENCE+4
    movl $pnr_genesis_header, PN_EVIDENCE+8
    movl $PN_SIGMA0, PN_EVIDENCE+12
    movl $PN_MAP_EVIDENCE, PN_EVIDENCE+16
    movl $PN_PNVH, PN_EVIDENCE+20
    movl $1, PN_EVIDENCE+24

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
