.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry,@function

.set PNVQ_EVIDENCE, 0x5b00

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

    # Selected edge must be two distinct in-range 36D indices.
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

    # Both source lineage commitments must be non-zero 256-bit values.
    movq 616(%rsi), %r8
    orq 624(%rsi), %r8
    orq 632(%rsi), %r8
    orq 640(%rsi), %r8
    jz pnvq_fail
    movq 648(%rsi), %r9
    orq 656(%rsi), %r9
    orq 664(%rsi), %r9
    orq 672(%rsi), %r9
    jz pnvq_fail

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
