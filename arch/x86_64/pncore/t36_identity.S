.code64
.section .text.pncore.t36identity,"ax"

.set T36I_MAGIC,       0x49363354      # "T36I"
.set T36I_MAJOR,       1
.set T36I_MINOR,       0
.set T36I_BYTES,       256
.set T36I_DIM,         36

.set T36I_OFF_MAGIC,   0
.set T36I_OFF_MAJOR,   4
.set T36I_OFF_MINOR,   6
.set T36I_OFF_BYTES,   8
.set T36I_OFF_DIM,     10
.set T36I_OFF_FLAGS,   12
.set T36I_OFF_CRYSTAL, 16
.set T36I_OFF_GENESIS, 48
.set T36I_OFF_ORIGIN,  80
.set T36I_OFF_PNV_SHA, 112
.set T36I_OFF_SOURCE,  144
.set T36I_OFF_BASIS,   176
.set T36I_OFF_CONFIG,  208
.set T36I_OFF_PHASE,   240
.set T36I_OFF_BOOT,    248

.set PNVH_OFF_BASIS,   32
.set PNVH_OFF_VEC_SHA, 64
.set PNVH_OFF_SOURCE,  96

# Copy an already host-derived exact 256-byte identity record into working RAM.
# Hash derivation is intentionally outside this routine; PNCore validates bindings
# and evolves only phase/boot counters.
.global t36_identity_materialize
.type t36_identity_materialize, @function
t36_identity_materialize:
    pushq %rdi
    pushq %rsi
    movl $32, %ecx
    cld
    rep movsq
    popq %rsi
    popq %rdi
    movl $1, %eax
    ret

# rdi = identity record, rsi = admitted PNVH.
# Returns eax=1 only when record geometry and PNVH basis/vector/source bindings match.
.global t36_identity_validate
.type t36_identity_validate, @function
t36_identity_validate:
    cmpl $T36I_MAGIC, T36I_OFF_MAGIC(%rdi)
    jne .Linvalid
    cmpw $T36I_MAJOR, T36I_OFF_MAJOR(%rdi)
    jne .Linvalid
    cmpw $T36I_MINOR, T36I_OFF_MINOR(%rdi)
    jne .Linvalid
    cmpw $T36I_BYTES, T36I_OFF_BYTES(%rdi)
    jne .Linvalid
    cmpw $T36I_DIM, T36I_OFF_DIM(%rdi)
    jne .Linvalid
    movl T36I_OFF_FLAGS(%rdi), %eax
    andl $0x7, %eax
    cmpl $0x7, %eax
    jne .Linvalid

    pushq %rdi
    pushq %rsi

    leaq T36I_OFF_PNV_SHA(%rdi), %rdi
    leaq PNVH_OFF_VEC_SHA(%rsi), %rsi
    movl $32, %ecx
    repe cmpsb
    jne .Lcmp_invalid

    popq %rsi
    popq %rdi
    pushq %rdi
    pushq %rsi
    leaq T36I_OFF_SOURCE(%rdi), %rdi
    leaq PNVH_OFF_SOURCE(%rsi), %rsi
    movl $32, %ecx
    repe cmpsb
    jne .Lcmp_invalid

    popq %rsi
    popq %rdi
    pushq %rdi
    pushq %rsi
    leaq T36I_OFF_BASIS(%rdi), %rdi
    leaq PNVH_OFF_BASIS(%rsi), %rsi
    movl $32, %ecx
    repe cmpsb
    jne .Lcmp_invalid

    popq %rsi
    popq %rdi
    movl $1, %eax
    ret

.Lcmp_invalid:
    popq %rsi
    popq %rdi
.Linvalid:
    xorl %eax, %eax
    ret

.global t36_identity_spinor_sheet
.type t36_identity_spinor_sheet, @function
t36_identity_spinor_sheet:
    movq T36I_OFF_PHASE(%rdi), %rax
    andq $1, %rax
    ret

.global t36_identity_advance_tick
.type t36_identity_advance_tick, @function
t36_identity_advance_tick:
    movq T36I_OFF_PHASE(%rdi), %rax
    incq %rax
    movq %rax, T36I_OFF_PHASE(%rdi)
    ret

.global t36_identity_increment_boot_epoch
.type t36_identity_increment_boot_epoch, @function
t36_identity_increment_boot_epoch:
    movq T36I_OFF_BOOT(%rdi), %rax
    incq %rax
    movq %rax, T36I_OFF_BOOT(%rdi)
    ret

# rdi=a, rsi=b. Compare invariant crystal identity only.
.global t36_identity_same_crystal
.type t36_identity_same_crystal, @function
t36_identity_same_crystal:
    pushq %rdi
    pushq %rsi
    leaq T36I_OFF_CRYSTAL(%rdi), %rdi
    leaq T36I_OFF_CRYSTAL(%rsi), %rsi
    movl $32, %ecx
    cld
    repe cmpsb
    popq %rsi
    popq %rdi
    jne .Lsame_no
    movl $1, %eax
    ret
.Lsame_no:
    xorl %eax, %eax
    ret

# rdi=a, rsi=b. A lifted 4*pi closure witness requires:
# same crystal, same configuration, same boot epoch, and b.phase=a.phase+2.
.global t36_identity_four_pi_closed
.type t36_identity_four_pi_closed, @function
t36_identity_four_pi_closed:
    pushq %rdi
    pushq %rsi
    call t36_identity_same_crystal
    popq %rsi
    popq %rdi
    testl %eax, %eax
    jz .Lclosed_no

    pushq %rdi
    pushq %rsi
    leaq T36I_OFF_CONFIG(%rdi), %rdi
    leaq T36I_OFF_CONFIG(%rsi), %rsi
    movl $32, %ecx
    cld
    repe cmpsb
    popq %rsi
    popq %rdi
    jne .Lclosed_no

    movq T36I_OFF_BOOT(%rdi), %rax
    cmpq T36I_OFF_BOOT(%rsi), %rax
    jne .Lclosed_no

    movq T36I_OFF_PHASE(%rdi), %rax
    addq $2, %rax
    cmpq T36I_OFF_PHASE(%rsi), %rax
    jne .Lclosed_no

    movl $1, %eax
    ret
.Lclosed_no:
    xorl %eax, %eax
    ret
