.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry,@function

.set PNVQ_EVIDENCE, 0x5b00
.set PNVQ_EXPECTED_TICK, 20215
.set PNVQ_EXPECTED_I, 24
.set PNVQ_EXPECTED_J, 26

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

pncore_entry:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'V'
    OUTC 'Q'
    OUTC 0x0a

    movl $vector_native_qhtri_replay_payload, %esi

    # Fixed binary ABI admission.
    cmpl $0x51564e50, 0(%rsi)      # PNVQ
    jne pnvq_fail
    cmpl $0x31525448, 4(%rsi)      # HTR1
    jne pnvq_fail
    cmpl $1, 8(%rsi)
    jne pnvq_fail
    cmpl $36, 12(%rsi)
    jne pnvq_fail

    # This ROM is bound to one exact replay event, not merely a valid ABI.
    cmpq $PNVQ_EXPECTED_TICK, 16(%rsi)
    jne pnvq_fail
    cmpl $PNVQ_EXPECTED_I, 24(%rsi)
    jne pnvq_fail
    cmpl $PNVQ_EXPECTED_J, 28(%rsi)
    jne pnvq_fail
    movq 32(%rsi), %rax
    movabsq $0x3ff0000000000000, %r10   # exact IEEE-754 +1.0 coupling
    cmpq %r10, %rax
    jne pnvq_fail

    # Selected edge must still satisfy the generic geometry constraints.
    movl 24(%rsi), %r8d
    movl 28(%rsi), %r9d
    cmpl $35, %r8d
    ja pnvq_fail
    cmpl $35, %r9d
    ja pnvq_fail
    cmpl %r9d, %r8d
    je pnvq_fail

    # Coupling must be finite and non-zero.
    movq 32(%rsi), %rax
    movabsq $0x7ff0000000000000, %r11
    movq %rax, %r10
    andq %r11, %r10
    cmpq %r11, %r10
    je pnvq_fail
    movabsq $0x7fffffffffffffff, %r12
    andq %r12, %rax
    jz pnvq_fail

    # Validate all 36 phi + 36 omega float64 lanes and produce a deterministic
    # 64-bit fold over their exact IEEE-754 bit patterns.
    leaq 40(%rsi), %rdi
    movl $72, %ecx
    xorq %rax, %rax
.Llane_loop:
    movq (%rdi), %r8
    movq %r8, %r9
    andq %r11, %r9
    cmpq %r11, %r9
    je pnvq_fail
    xorq %r8, %rax
    rolq $1, %rax
    addq $8, %rdi
    decl %ecx
    jnz .Llane_loop

    # The exact snapshot fold is admitted in-guest. A finite but modified lane
    # is rejected instead of being silently accepted as a different state.
    movabsq $0x687aac2ca5b6feb3, %r10
    cmpq %r10, %rax
    jne pnvq_fail

    # Exact source-lineage commitments. This closes the previous gap where an
    # arbitrary non-zero 256-bit value could pass the guest gate.
    movabsq $0xb03d0528b2c48096, %r10
    cmpq %r10, 616(%rsi)
    jne pnvq_fail
    movabsq $0xd2e477949a68f250, %r10
    cmpq %r10, 624(%rsi)
    jne pnvq_fail
    movabsq $0x8a8080fbc7d1f8b2, %r10
    cmpq %r10, 632(%rsi)
    jne pnvq_fail
    movabsq $0x92743432c21cbcdb, %r10
    cmpq %r10, 640(%rsi)
    jne pnvq_fail

    movabsq $0xd45800af48405ff0, %r10
    cmpq %r10, 648(%rsi)
    jne pnvq_fail
    movabsq $0xf69b5103a5c5ef0f, %r10
    cmpq %r10, 656(%rsi)
    jne pnvq_fail
    movabsq $0x867afd00a66d8a6d, %r10
    cmpq %r10, 664(%rsi)
    jne pnvq_fail
    movabsq $0xdbd5c1a046f54083, %r10
    cmpq %r10, 672(%rsi)
    jne pnvq_fail

    # Bounded in-guest evidence record.
    movq %rax, PNVQ_EVIDENCE+0
    movq 16(%rsi), %r10
    movq %r10, PNVQ_EVIDENCE+8
    movl 24(%rsi), %r10d
    movl %r10d, PNVQ_EVIDENCE+16
    movl 28(%rsi), %r10d
    movl %r10d, PNVQ_EVIDENCE+20
    movl $0x31565150, PNVQ_EVIDENCE+24  # PQV1 marker

    # Emit the exact fold so host conformance can compare guest computation
    # against an independently reconstructed expected value.
    movq %rax, %rbx
    OUTC 'P'
    OUTC 'N'
    OUTC 'V'
    OUTC 'Q'
    OUTC '.'
    OUTC 'F'
    OUTC 'O'
    OUTC 'L'
    OUTC 'D'
    OUTC '='
    movl $16, %ecx
.Lhex_loop:
    movq %rbx, %rax
    shrq $60, %rax
    andl $0x0f, %eax
    cmpl $9, %eax
    jbe .Lhex_digit
    addl $87, %eax
    jmp .Lhex_emit
.Lhex_digit:
    addl $48, %eax
.Lhex_emit:
    outb %al, %dx
    shlq $4, %rbx
    decl %ecx
    jnz .Lhex_loop
    OUTC 0x0a

    OUTC 'P'
    OUTC 'N'
    OUTC 'V'
    OUTC 'Q'
    OUTC '.'
    OUTC 'O'
    OUTC 'K'
    OUTC 0x0a
.Lhalt:
    hlt
    jmp .Lhalt

pnvq_fail:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'V'
    OUTC 'Q'
    OUTC '.'
    OUTC 'X'
    OUTC 0x0a
.Lfail_halt:
    hlt
    jmp .Lfail_halt

.section .note.GNU-stack,"",@progbits
