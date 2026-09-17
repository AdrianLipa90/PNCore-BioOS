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

# Dedicated PNStore device-semantics entrypoint for QEMU/PIIX IDE validation.
# It intentionally replaces the normal PNCore entry only in the dedicated test
# ROM. The normal full-BioOS QEMU gate remains a separate, independently passing
# path.
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

    # Load the complete 64 KiB PNStore medium from primary-master IDE.
    movl $PN_STORE_MEDIA, %edi
    call pnstore_ata_read_media
    cmpl $1, %eax
    jne pncore_fail

    # Existing valid medium -> verify durable continuation semantics.
    movl $PN_STORE_MEDIA, %edi
    movl $65536, %esi
    call pnstore_verify_super
    cmpl $1, %eax
    je .Lexisting_medium

    # Invalid super is admitted as first-use only when every byte is zero.
    # Corrupted/non-zero media fails closed instead of being reformatted.
    movl $PN_STORE_MEDIA, %edi
    movl $8192, %ecx
    xorq %rax, %rax
    cld
    repe scasq
    jne pncore_fail

    # First use: format in RAM, persist the superblock sector, then flush.
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

    # Prepare generation 1 in the immutable extent.
    movl $PN_STORE_MEDIA, %edi
    movl $pnstore_ide_transition_id, %esi
    movl $pnstore_ide_object_digest, %edx
    movl $pnstore_ide_payload, %ecx
    movl $32, %r8d
    call pnstore_prepare_commit
    cmpq $1, %rax
    jne pncore_fail
    cmpq $4096, %rdx
    jne pncore_fail
    cmpq $1, %rcx
    jne pncore_fail

    # Durability order gate 1: write prepared extent sectors 8..15, then FLUSH.
    movl $8, %edi
    movl $(PN_STORE_MEDIA+4096), %esi
    movl $8, %edx
    call pnstore_ata_write_sectors
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    # Publish HEAD_A only after the prepared extent flush has completed.
    movl $PN_STORE_MEDIA, %edi
    movl $1, %esi
    movl $4096, %edx
    call pnstore_publish_head
    cmpq $1, %eax
    jne pncore_fail

    # Durability order gate 2: persist HEAD_A sector 1, then FLUSH again.
    movl $1, %edi
    movl $(PN_STORE_MEDIA+512), %esi
    call pnstore_ata_write_sector
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    # Destroy the RAM copy, re-read device bytes, and require exact recovery.
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
    # A valid superblock is not enough: generation 1 and HEAD_A must recover.
    movl $PN_STORE_MEDIA, %edi
    call pnstore_recover
    cmpq $1, %rax
    jne pncore_fail
    cmpq $512, %rdx
    jne pncore_fail

    # The stable transition id must resolve to ALREADY_COMMITTED and must not
    # allocate a new generation during the second boot.
    movl $PN_STORE_MEDIA, %edi
    movl $pnstore_ide_transition_id, %esi
    movl $pnstore_ide_object_digest, %edx
    movl $pnstore_ide_payload, %ecx
    movl $32, %r8d
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
    # Record the bounded evidence class in RAM. This is QEMU IDE device
    # semantics, not a physical-device/power-loss claim.
    movl $0x444e5050, PN_STORE_EVIDENCE+0   # "PPND" little-endian marker
    movl $1,          PN_STORE_EVIDENCE+4
    movl $65536,      PN_STORE_EVIDENCE+8
    movl $128,        PN_STORE_EVIDENCE+12
    movl $1,          PN_STORE_EVIDENCE+16  # primary-master ATA PIO
    movl $1,          PN_STORE_EVIDENCE+20  # extent flush observed
    movl $1,          PN_STORE_EVIDENCE+24  # head flush observed
    movl $1,          PN_STORE_EVIDENCE+28  # device reread/recovery PASS
    movl $0,          PN_STORE_EVIDENCE+32  # physical power-loss claim FALSE

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
pnstore_ide_transition_id:
    .byte 0x5d,0x12,0xb1,0x5d,0x52,0x31,0x48,0xd8,0x8d,0x1a,0x70,0x03,0x7e,0x9b,0x6a,0x02
    .byte 0x0f,0xa1,0x5f,0x50,0x77,0x6d,0xb2,0xe5,0x95,0x6c,0xe0,0x0d,0x11,0x44,0x49,0x01
pnstore_ide_object_digest:
    .byte 0xf8,0x8b,0x59,0x3a,0xa7,0x40,0xdf,0x32,0xe2,0xa0,0x9d,0x5e,0x88,0x2f,0xd1,0x6c
    .byte 0xc4,0xd4,0x88,0x5b,0xa4,0x8b,0xd0,0x75,0x95,0xf7,0x63,0x3f,0xa0,0x95,0x94,0xd2
pnstore_ide_payload:
    .ascii "PNSTORE-IDE-QEMU-V01-PERSISTENCE!"

.section .note.GNU-stack,"",@progbits
