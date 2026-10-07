.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry,@function

.set PN_STORE_MEDIA,    0x10000
.set PN_STORE_EVIDENCE, 0x5800

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

# Dedicated bridge witness: persist one exact, externally pinned DNCrypt binary
# envelope through the existing PNStore ATA-PIO durability ordering. The payload
# is generated from a checked-in hex fixture before assembly and included below.
pncore_entry:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'C'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'I'
    OUTC 'D'
    OUTC 'E'
    OUTC 0x0a

    movl $PN_STORE_MEDIA, %edi
    call pnstore_ata_read_media
    cmpl $1, %eax
    jne pncore_fail

    movl $PN_STORE_MEDIA, %edi
    movl $65536, %esi
    call pnstore_verify_super
    cmpl $1, %eax
    je .Lexisting_medium

    # First use is admitted only for an all-zero medium.
    movl $PN_STORE_MEDIA, %edi
    movl $8192, %ecx
    xorq %rax, %rax
    cld
    repe scasq
    jne pncore_fail

    movl $PN_STORE_MEDIA, %edi
    movl $65536, %esi
    call pnstore_format
    cmpl $1, %eax
    jne pncore_fail

    movl $0, %edi
    movl $PN_STORE_MEDIA, %esi
    call pnstore_ata_write_sector
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    # Generation 1 contains the complete DNCrypt binary envelope, not a digest
    # surrogate. PNStore's object digest is SHA-256(payload); the stable
    # transition id is separately domain-separated by the build witness.
    movl $PN_STORE_MEDIA, %edi
    movl $pnstore_dncrypt_transition_id, %esi
    movl $pnstore_dncrypt_object_digest, %edx
    movl $pnstore_dncrypt_payload, %ecx
    movl $PNSTORE_DNCRYPT_PAYLOAD_LEN, %r8d
    call pnstore_prepare_commit
    cmpq $1, %rax
    jne pncore_fail
    cmpq $4096, %rdx
    jne pncore_fail
    cmpq $1, %rcx
    jne pncore_fail

    movl $8, %edi
    movl $(PN_STORE_MEDIA+4096), %esi
    movl $8, %edx
    call pnstore_ata_write_sectors
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    movl $PN_STORE_MEDIA, %edi
    movl $1, %esi
    movl $4096, %edx
    call pnstore_publish_head
    cmpq $1, %rax
    jne pncore_fail

    movl $1, %edi
    movl $(PN_STORE_MEDIA+512), %esi
    call pnstore_ata_write_sector
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    # Destroy the RAM copy and prove recovery from device bytes.
    movl $PN_STORE_MEDIA, %edi
    xorq %rax, %rax
    movl $8192, %ecx
    cld
    rep stosq
    movl $PN_STORE_MEDIA, %edi
    call pnstore_ata_read_media
    cmpl $1, %eax
    jne pncore_fail
    movl $PN_STORE_MEDIA, %edi
    movl $65536, %esi
    call pnstore_verify_super
    cmpl $1, %eax
    jne pncore_fail
    movl $PN_STORE_MEDIA, %edi
    call pnstore_recover
    cmpq $1, %rax
    jne pncore_fail
    cmpq $512, %rdx
    jne pncore_fail

    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'D'
    OUTC 'E'
    OUTC 'V'
    OUTC '.'
    OUTC 'N'
    OUTC 'E'
    OUTC 'W'
    OUTC 0x0a
    jmp .Ldevice_ok

.Lexisting_medium:
    movl $PN_STORE_MEDIA, %edi
    call pnstore_recover
    cmpq $1, %rax
    jne pncore_fail
    cmpq $512, %rdx
    jne pncore_fail

    # Same transition must resolve as already committed and leave the medium
    # unchanged on the second independent QEMU process.
    movl $PN_STORE_MEDIA, %edi
    movl $pnstore_dncrypt_transition_id, %esi
    movl $pnstore_dncrypt_object_digest, %edx
    movl $pnstore_dncrypt_payload, %ecx
    movl $PNSTORE_DNCRYPT_PAYLOAD_LEN, %r8d
    call pnstore_prepare_commit
    cmpq $1, %rax
    jne pncore_fail
    cmpq $4096, %rdx
    jne pncore_fail
    cmpq $2, %rcx
    jne pncore_fail

    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'D'
    OUTC 'E'
    OUTC 'V'
    OUTC '.'
    OUTC 'R'
    OUTC 'E'
    OUTC 'C'
    OUTC 'O'
    OUTC 'V'
    OUTC 'E'
    OUTC 'R'
    OUTC 0x0a

.Ldevice_ok:
    movl $0x444e5050, PN_STORE_EVIDENCE+0
    movl $1,          PN_STORE_EVIDENCE+4
    movl $65536,      PN_STORE_EVIDENCE+8
    movl $128,        PN_STORE_EVIDENCE+12
    movl $1,          PN_STORE_EVIDENCE+16
    movl $1,          PN_STORE_EVIDENCE+20
    movl $1,          PN_STORE_EVIDENCE+24
    movl $1,          PN_STORE_EVIDENCE+28
    movl $0,          PN_STORE_EVIDENCE+32
    movl $PNSTORE_DNCRYPT_PAYLOAD_LEN, PN_STORE_EVIDENCE+36

    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'D'
    OUTC 'E'
    OUTC 'V'
    OUTC '.'
    OUTC 'O'
    OUTC 'K'
    OUTC 0x0a
.Lhalt:
    hlt
    jmp .Lhalt

pncore_fail:
    movw $0x00e9, %dx
    OUTC 'X'
    OUTC 0x0a
.Lfail_halt:
    hlt
    jmp .Lfail_halt

.section .rodata.pncore.expected,"a"
.align 16
pnstore_dncrypt_transition_id:
    .incbin "build/x86_64/pnstore_dncrypt_transition_id.bin"
pnstore_dncrypt_object_digest:
    .incbin "build/x86_64/pnstore_dncrypt_object_digest.bin"
pnstore_dncrypt_payload:
    .incbin "build/x86_64/pnstore_dncrypt_payload.bin"
pnstore_dncrypt_payload_end:
.set PNSTORE_DNCRYPT_PAYLOAD_LEN, pnstore_dncrypt_payload_end-pnstore_dncrypt_payload

.section .note.GNU-stack,"",@progbits
