.code64
.section .text.pncore.store,"ax"
.global pnstore_crc32c
.global pnstore_format
.global pnstore_verify_super
.global pnstore_validate_extent
.global pnstore_validate_head
.global pnstore_recover
.global pnstore_prepare_commit
.global pnstore_publish_head
.type pnstore_crc32c,@function
.type pnstore_format,@function
.type pnstore_verify_super,@function
.type pnstore_validate_extent,@function
.type pnstore_validate_head,@function
.type pnstore_recover,@function
.type pnstore_prepare_commit,@function
.type pnstore_publish_head,@function

# PNStore Media Core v0.1
# Exact media geometry for the first bounded realization.
.equ PNS_MEDIA_BYTES,       65536
.equ PNS_SECTOR_BYTES,        512
.equ PNS_EXTENT_BYTES,       4096
.equ PNS_LOG_OFF,            4096
.equ PNS_MAX_GENERATIONS,      15
.equ PNS_HEAD_A_OFF,          512
.equ PNS_HEAD_B_OFF,         1024
.equ PNS_HEAD_BYTES,          512
.equ PNS_HEAD_CRC_OFF,        508
.equ PNS_SUPER_CRC_OFF,       508
.equ PNS_EXTENT_SEAL_OFF,    4032
.equ PNS_EXTENT_DATA_BYTES,  4032
.equ PNS_EXTENT_PAYLOAD_OFF,   96
.equ PNS_EXTENT_PAYLOAD_MAX, 3936
.equ PNS_SEAL_CRC_OFF,         60

.equ PNS_MAGIC_SUPER,  0x31534e50  # PNS1
.equ PNS_MAGIC_HEAD,   0x31484e50  # PNH1
.equ PNS_MAGIC_EXTENT, 0x31474e50  # PNG1
.equ PNS_MAGIC_COMMIT, 0x31434e50  # PNC1

# uint32_t pnstore_crc32c(const void *ptr, uint64_t len)
# Bitwise Castagnoli CRC32C, polynomial 0x82f63b78, init/final XOR all ones.
pnstore_crc32c:
    movl $0xffffffff, %eax
    testq %rsi, %rsi
    jz .Lcrc_done
.Lcrc_byte:
    movzbl (%rdi), %edx
    xorl %edx, %eax
    movl $8, %ecx
.Lcrc_bit:
    movl %eax, %edx
    andl $1, %edx
    shrl $1, %eax
    testl %edx, %edx
    jz .Lcrc_no_poly
    xorl $0x82f63b78, %eax
.Lcrc_no_poly:
    decl %ecx
    jnz .Lcrc_bit
    incq %rdi
    decq %rsi
    jnz .Lcrc_byte
.Lcrc_done:
    xorl $0xffffffff, %eax
    ret

# int pnstore_format(void *media, uint64_t bytes)
# Initializes an empty medium. No HEAD is current until a generation is published.
pnstore_format:
    cmpq $PNS_MEDIA_BYTES, %rsi
    jb .Lformat_fail
    pushq %rbx
    movq %rdi, %rbx
    cld
    xorq %rax, %rax
    movq $(PNS_MEDIA_BYTES/8), %rcx
    rep stosq

    movl $PNS_MAGIC_SUPER, 0(%rbx)
    movl $1,               4(%rbx)
    movl $PNS_MEDIA_BYTES, 8(%rbx)
    movl $PNS_SECTOR_BYTES,12(%rbx)
    movl $PNS_EXTENT_BYTES,16(%rbx)
    movl $PNS_LOG_OFF,     20(%rbx)
    movl $PNS_MAX_GENERATIONS,24(%rbx)
    movl $1,               28(%rbx)   # flags: alternating dual HEAD
    movl $PNS_HEAD_A_OFF,  32(%rbx)
    movl $PNS_HEAD_B_OFF,  36(%rbx)

    movq %rbx, %rdi
    movq $PNS_SUPER_CRC_OFF, %rsi
    call pnstore_crc32c
    movl %eax, PNS_SUPER_CRC_OFF(%rbx)
    movl $1, %eax
    popq %rbx
    ret
.Lformat_fail:
    xorl %eax, %eax
    ret

# int pnstore_verify_super(void *media, uint64_t bytes)
pnstore_verify_super:
    cmpq $PNS_MEDIA_BYTES, %rsi
    jb .Lsuper_fail
    pushq %rbx
    movq %rdi, %rbx
    cmpl $PNS_MAGIC_SUPER, 0(%rbx)
    jne .Lsuper_fail_pop
    cmpl $1, 4(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_MEDIA_BYTES, 8(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_SECTOR_BYTES, 12(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_EXTENT_BYTES, 16(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_LOG_OFF, 20(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_MAX_GENERATIONS, 24(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_HEAD_A_OFF, 32(%rbx)
    jne .Lsuper_fail_pop
    cmpl $PNS_HEAD_B_OFF, 36(%rbx)
    jne .Lsuper_fail_pop
    movl PNS_SUPER_CRC_OFF(%rbx), %r8d
    movq %rbx, %rdi
    movq $PNS_SUPER_CRC_OFF, %rsi
    call pnstore_crc32c
    cmpl %r8d, %eax
    jne .Lsuper_fail_pop
    movl $1, %eax
    popq %rbx
    ret
.Lsuper_fail_pop:
    xorl %eax, %eax
    popq %rbx
    ret
.Lsuper_fail:
    xorl %eax, %eax
    ret

# int pnstore_validate_extent(void *media, uint32_t extent_off)
pnstore_validate_extent:
    pushq %rbx
    pushq %r12
    movq %rdi, %rbx
    movl %esi, %r12d
    cmpl $PNS_LOG_OFF, %r12d
    jb .Lextent_fail
    cmpl $(PNS_MEDIA_BYTES-PNS_EXTENT_BYTES), %r12d
    ja .Lextent_fail
    testl $(PNS_EXTENT_BYTES-1), %r12d
    jnz .Lextent_fail
    leaq (%rbx,%r12), %r10
    cmpl $PNS_MAGIC_EXTENT, 0(%r10)
    jne .Lextent_fail
    cmpl $1, 4(%r10)
    jne .Lextent_fail
    movl 88(%r10), %eax
    cmpl $PNS_EXTENT_PAYLOAD_MAX, %eax
    ja .Lextent_fail

    leaq PNS_EXTENT_SEAL_OFF(%r10), %r11
    cmpl $PNS_MAGIC_COMMIT, 0(%r11)
    jne .Lextent_fail
    cmpl $1, 4(%r11)
    jne .Lextent_fail
    movq 8(%r10), %rax
    cmpq 8(%r11), %rax
    jne .Lextent_fail
    cmpl $1, 20(%r11)
    jne .Lextent_fail

    # Validate data CRC over bytes [0, 4032).
    movl 16(%r11), %r8d
    movq %r10, %rdi
    movq $PNS_EXTENT_DATA_BYTES, %rsi
    call pnstore_crc32c
    cmpl %r8d, %eax
    jne .Lextent_fail

    # Validate seal CRC over first 60 seal bytes.
    movl PNS_SEAL_CRC_OFF(%r11), %r8d
    movq %r11, %rdi
    movq $PNS_SEAL_CRC_OFF, %rsi
    call pnstore_crc32c
    cmpl %r8d, %eax
    jne .Lextent_fail
    movl $1, %eax
    popq %r12
    popq %rbx
    ret
.Lextent_fail:
    xorl %eax, %eax
    popq %r12
    popq %rbx
    ret

# int pnstore_validate_head(void *media, uint32_t head_off)
pnstore_validate_head:
    pushq %rbx
    pushq %r12
    movq %rdi, %rbx
    movl %esi, %r12d
    cmpl $PNS_HEAD_A_OFF, %r12d
    je .Lhead_off_ok
    cmpl $PNS_HEAD_B_OFF, %r12d
    jne .Lhead_fail
.Lhead_off_ok:
    leaq (%rbx,%r12), %r10
    cmpl $PNS_MAGIC_HEAD, 0(%r10)
    jne .Lhead_fail
    cmpl $1, 4(%r10)
    jne .Lhead_fail
    movl PNS_HEAD_CRC_OFF(%r10), %r8d
    movq %r10, %rdi
    movq $PNS_HEAD_CRC_OFF, %rsi
    call pnstore_crc32c
    cmpl %r8d, %eax
    jne .Lhead_fail

    movl 24(%r10), %esi
    movq %rbx, %rdi
    call pnstore_validate_extent
    testl %eax, %eax
    jz .Lhead_fail

    # Head generation and stored extent CRC must agree with the extent.
    leaq (%rbx,%r12), %r10
    movl 24(%r10), %eax
    leaq (%rbx,%rax), %r11
    movq 16(%r10), %rax
    cmpq 8(%r11), %rax
    jne .Lhead_fail
    movl PNS_EXTENT_SEAL_OFF+16(%r11), %eax
    cmpl 28(%r10), %eax
    jne .Lhead_fail
    movl $1, %eax
    popq %r12
    popq %rbx
    ret
.Lhead_fail:
    xorl %eax, %eax
    popq %r12
    popq %rbx
    ret

# uint64_t pnstore_recover(void *media)
# Returns generation in RAX and selected HEAD offset in RDX (0 for empty).
pnstore_recover:
    pushq %rbx
    pushq %r12
    pushq %r13
    movq %rdi, %rbx
    movq %rbx, %rdi
    movq $PNS_MEDIA_BYTES, %rsi
    call pnstore_verify_super
    testl %eax, %eax
    jz .Lrecover_empty

    movq %rbx, %rdi
    movl $PNS_HEAD_A_OFF, %esi
    call pnstore_validate_head
    movl %eax, %r12d
    movq %rbx, %rdi
    movl $PNS_HEAD_B_OFF, %esi
    call pnstore_validate_head
    movl %eax, %r13d

    testl %r12d, %r12d
    jz .Lrecover_only_b_or_empty
    testl %r13d, %r13d
    jz .Lrecover_a
    movq PNS_HEAD_A_OFF+8(%rbx), %rax
    cmpq PNS_HEAD_B_OFF+8(%rbx), %rax
    jb .Lrecover_b
.Lrecover_a:
    movq PNS_HEAD_A_OFF+16(%rbx), %rax
    movq $PNS_HEAD_A_OFF, %rdx
    jmp .Lrecover_done
.Lrecover_only_b_or_empty:
    testl %r13d, %r13d
    jz .Lrecover_empty
.Lrecover_b:
    movq PNS_HEAD_B_OFF+16(%rbx), %rax
    movq $PNS_HEAD_B_OFF, %rdx
    jmp .Lrecover_done
.Lrecover_empty:
    xorq %rax, %rax
    xorq %rdx, %rdx
.Lrecover_done:
    popq %r13
    popq %r12
    popq %rbx
    ret

# uint64_t pnstore_prepare_commit(media, transition_id32, object_digest32,
#                                 payload, payload_len)
# RAX=generation (0 fail), RDX=extent offset, RCX=status (1 NEW_PREPARED, 2 ALREADY_COMMITTED).
# This function prepares the extent only; durability authority belongs to the external backend barrier.
pnstore_prepare_commit:
    pushq %rbx
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    subq $16, %rsp
    movq %rdi, %rbx
    movq %rsi, %r12
    movq %rdx, %r13
    movq %rcx, %r14
    movq %r8, %r15
    cmpq $PNS_EXTENT_PAYLOAD_MAX, %r15
    ja .Lprepare_fail

    movq %rbx, %rdi
    call pnstore_recover
    movq %rax, 0(%rsp)                       # current generation

    # Exactly-once is bounded but historical: scan every committed immutable
    # generation, not merely the current HEAD, for the stable transition id.
    testq %rax, %rax
    jz .Lprepare_new
    movq $1, %r9
.Lprepare_scan:
    cmpq 0(%rsp), %r9
    ja .Lprepare_new
    movq %r9, %r11
    shlq $12, %r11                           # extent offset
    movq %rbx, %rdi
    movl %r11d, %esi
    call pnstore_validate_extent
    testl %eax, %eax
    jz .Lprepare_fail
    movq %r9, %r11
    shlq $12, %r11                           # recompute caller-saved extent offset
    leaq 24(%rbx,%r11), %rdi
    movq %r12, %rsi
    movl $32, %ecx
    cld
    repe cmpsb
    je .Lprepare_existing
    incq %r9
    jmp .Lprepare_scan
.Lprepare_existing:
    movq %r9, %rax
    movq %r11, %rdx
    movq $2, %rcx
    jmp .Lprepare_done

.Lprepare_new:
    movq 0(%rsp), %r10                       # current generation
    cmpq $PNS_MAX_GENERATIONS, %r10
    jae .Lprepare_fail
    leaq 1(%r10), %r9                        # new generation
    movq %r9, %rax
    shlq $12, %rax                           # extent offset = generation * 4096
    movq %rax, %r11                          # extent offset
    leaq (%rbx,%r11), %rdi
    cld
    xorq %rax, %rax
    movq $(PNS_EXTENT_BYTES/8), %rcx
    rep stosq
    leaq (%rbx,%r11), %r8                    # extent base

    movl $PNS_MAGIC_EXTENT, 0(%r8)
    movl $1, 4(%r8)
    movq %r9, 8(%r8)
    movq %r10, 16(%r8)
    leaq 24(%r8), %rdi
    movq %r12, %rsi
    movl $32, %ecx
    rep movsb
    leaq 56(%r8), %rdi
    movq %r13, %rsi
    movl $32, %ecx
    rep movsb
    movl %r15d, 88(%r8)
    movl $1, 92(%r8)                         # generation candidate flag
    leaq PNS_EXTENT_PAYLOAD_OFF(%r8), %rdi
    movq %r14, %rsi
    movq %r15, %rcx
    rep movsb

    # Data CRC and commit seal.
    movq %r8, %rdi
    movq $PNS_EXTENT_DATA_BYTES, %rsi
    call pnstore_crc32c
    movl %eax, %r12d                         # data CRC temporary
    leaq (%rbx,%r11), %r8
    leaq PNS_EXTENT_SEAL_OFF(%r8), %r10
    movl $PNS_MAGIC_COMMIT, 0(%r10)
    movl $1, 4(%r10)
    movq %r9, 8(%r10)
    movl %r12d, 16(%r10)
    movl $1, 20(%r10)                        # seal committed/prepared
    movq %r10, %rdi
    movq $PNS_SEAL_CRC_OFF, %rsi
    call pnstore_crc32c
    movl %eax, PNS_SEAL_CRC_OFF(%r10)

    movq %r9, %rax
    movq %r11, %rdx
    movq $1, %rcx
    jmp .Lprepare_done
.Lprepare_fail:
    xorq %rax, %rax
    xorq %rdx, %rdx
    xorq %rcx, %rcx
.Lprepare_done:
    addq $16, %rsp
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %rbx
    ret

# uint64_t pnstore_publish_head(media, generation, extent_off)
# Must be called only AFTER an external durable barrier made the prepared extent durable.
# Returns generation on success, 0 on failure. A second external barrier is required after this write.
pnstore_publish_head:
    pushq %rbx
    pushq %r12
    pushq %r13
    movq %rdi, %rbx
    movq %rsi, %r12                          # requested generation
    movl %edx, %r13d                         # extent offset

    movq %rbx, %rdi
    movl %r13d, %esi
    call pnstore_validate_extent
    testl %eax, %eax
    jz .Lpublish_fail
    leaq (%rbx,%r13), %r10
    cmpq 8(%r10), %r12
    jne .Lpublish_fail

    movq %rbx, %rdi
    call pnstore_recover
    movq %rax, %r11                          # current generation
    leaq 1(%r11), %rax
    cmpq %rax, %r12
    jne .Lpublish_fail

    # Odd generation -> HEAD_A, even -> HEAD_B.
    movl $PNS_HEAD_A_OFF, %r9d
    testb $1, %r12b
    jnz .Lpublish_slot_ready
    movl $PNS_HEAD_B_OFF, %r9d
.Lpublish_slot_ready:
    leaq (%rbx,%r9), %rdi
    cld
    xorq %rax, %rax
    movq $(PNS_HEAD_BYTES/8), %rcx
    rep stosq
    leaq (%rbx,%r9), %r8
    leaq (%rbx,%r13), %r10
    movl $PNS_MAGIC_HEAD, 0(%r8)
    movl $1, 4(%r8)
    movq %r12, 8(%r8)                        # sequence
    movq %r12, 16(%r8)                       # generation
    movl %r13d, 24(%r8)
    movl PNS_EXTENT_SEAL_OFF+16(%r10), %eax
    movl %eax, 28(%r8)
    leaq 32(%r8), %rdi
    leaq 24(%r10), %rsi
    movl $64, %ecx                           # transition id + object digest
    rep movsb
    movq %r8, %rdi
    movq $PNS_HEAD_CRC_OFF, %rsi
    call pnstore_crc32c
    movl %eax, PNS_HEAD_CRC_OFF(%r8)
    movq %r12, %rax
    popq %r13
    popq %r12
    popq %rbx
    ret
.Lpublish_fail:
    xorq %rax, %rax
    popq %r13
    popq %r12
    popq %rbx
    ret

.section .note.GNU-stack,"",@progbits
