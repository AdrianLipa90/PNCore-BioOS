.code64
.section .text.pncore.store_ata,"ax"
.global pnstore_ata_read_sector
.global pnstore_ata_write_sector
.global pnstore_ata_write_sectors
.global pnstore_ata_read_media
.global pnstore_ata_flush
.type pnstore_ata_read_sector,@function
.type pnstore_ata_write_sector,@function
.type pnstore_ata_write_sectors,@function
.type pnstore_ata_read_media,@function
.type pnstore_ata_flush,@function

# PNStore ATA PIO backend v0.1.
# Scope: primary IDE channel, master drive, LBA28, one-sector PIO transfers.
# This is a bounded x86/QEMU device realization for PNStore validation. It does
# not by itself establish physical power-loss durability.

.equ ATA_DATA,       0x1f0
.equ ATA_SECCOUNT,   0x1f2
.equ ATA_LBA0,       0x1f3
.equ ATA_LBA1,       0x1f4
.equ ATA_LBA2,       0x1f5
.equ ATA_DRIVE,      0x1f6
.equ ATA_STATUS,     0x1f7
.equ ATA_COMMAND,    0x1f7
.equ ATA_ALTSTATUS,  0x3f6
.equ ATA_CMD_READ,   0x20
.equ ATA_CMD_WRITE,  0x30
.equ ATA_CMD_FLUSH,  0xe7
.equ ATA_SR_BSY,     0x80
.equ ATA_SR_DF,      0x20
.equ ATA_SR_DRQ,     0x08
.equ ATA_SR_ERR,     0x01
.equ ATA_POLL_LIMIT, 1000000
.equ PNSTORE_SECTORS,128

# Internal: EAX=1 when BSY clears with no ERR/DF, else 0.
.Lata_wait_ready:
    movl $ATA_POLL_LIMIT, %ecx
    movw $ATA_STATUS, %dx
.Lata_ready_poll:
    inb %dx, %al
    cmpb $0xff, %al
    je .Lata_wait_fail
    testb $ATA_SR_BSY, %al
    jnz .Lata_ready_next
    testb $(ATA_SR_ERR|ATA_SR_DF), %al
    jnz .Lata_wait_fail
    movl $1, %eax
    ret
.Lata_ready_next:
    decl %ecx
    jnz .Lata_ready_poll
.Lata_wait_fail:
    xorl %eax, %eax
    ret

# Internal: EAX=1 when DRQ is asserted with BSY clear and no ERR/DF.
.Lata_wait_drq:
    movl $ATA_POLL_LIMIT, %ecx
    movw $ATA_STATUS, %dx
.Lata_drq_poll:
    inb %dx, %al
    cmpb $0xff, %al
    je .Lata_drq_fail
    testb $(ATA_SR_ERR|ATA_SR_DF), %al
    jnz .Lata_drq_fail
    testb $ATA_SR_BSY, %al
    jnz .Lata_drq_next
    testb $ATA_SR_DRQ, %al
    jnz .Lata_drq_ok
.Lata_drq_next:
    decl %ecx
    jnz .Lata_drq_poll
.Lata_drq_fail:
    xorl %eax, %eax
    ret
.Lata_drq_ok:
    movl $1, %eax
    ret

# Internal: program one-sector LBA28 transfer. LBA is in R12D.
# Returns EAX=1 if command registers may be programmed.
.Lata_program_lba:
    call .Lata_wait_ready
    testl %eax, %eax
    jz .Lata_program_fail

    movw $ATA_SECCOUNT, %dx
    movb $1, %al
    outb %al, %dx

    movl %r12d, %eax
    movw $ATA_LBA0, %dx
    outb %al, %dx
    shrl $8, %eax
    movw $ATA_LBA1, %dx
    outb %al, %dx
    shrl $8, %eax
    movw $ATA_LBA2, %dx
    outb %al, %dx

    movl %r12d, %eax
    shrl $24, %eax
    andb $0x0f, %al
    orb $0xe0, %al
    movw $ATA_DRIVE, %dx
    outb %al, %dx

    # ATA drive-select settling delay: four alternate-status reads.
    movw $ATA_ALTSTATUS, %dx
    inb %dx, %al
    inb %dx, %al
    inb %dx, %al
    inb %dx, %al
    movl $1, %eax
    ret
.Lata_program_fail:
    xorl %eax, %eax
    ret

# int pnstore_ata_read_sector(uint32_t lba, void *dst)
pnstore_ata_read_sector:
    pushq %r12
    pushq %r13
    movl %edi, %r12d
    movq %rsi, %r13
    cmpl $0x0fffffff, %r12d
    ja .Lread_fail
    call .Lata_program_lba
    testl %eax, %eax
    jz .Lread_fail
    movw $ATA_COMMAND, %dx
    movb $ATA_CMD_READ, %al
    outb %al, %dx
    call .Lata_wait_drq
    testl %eax, %eax
    jz .Lread_fail
    movq %r13, %rdi
    movl $256, %ecx
    movw $ATA_DATA, %dx
    cld
    rep insw
    call .Lata_wait_ready
    testl %eax, %eax
    jz .Lread_fail
    movl $1, %eax
    popq %r13
    popq %r12
    ret
.Lread_fail:
    xorl %eax, %eax
    popq %r13
    popq %r12
    ret

# int pnstore_ata_write_sector(uint32_t lba, const void *src)
pnstore_ata_write_sector:
    pushq %r12
    pushq %r13
    movl %edi, %r12d
    movq %rsi, %r13
    cmpl $0x0fffffff, %r12d
    ja .Lwrite_fail
    call .Lata_program_lba
    testl %eax, %eax
    jz .Lwrite_fail
    movw $ATA_COMMAND, %dx
    movb $ATA_CMD_WRITE, %al
    outb %al, %dx
    call .Lata_wait_drq
    testl %eax, %eax
    jz .Lwrite_fail
    movq %r13, %rsi
    movl $256, %ecx
    movw $ATA_DATA, %dx
    cld
    rep outsw
    call .Lata_wait_ready
    testl %eax, %eax
    jz .Lwrite_fail
    movl $1, %eax
    popq %r13
    popq %r12
    ret
.Lwrite_fail:
    xorl %eax, %eax
    popq %r13
    popq %r12
    ret

# int pnstore_ata_write_sectors(uint32_t first_lba, const void *src, uint32_t count)
pnstore_ata_write_sectors:
    pushq %r12
    pushq %r13
    pushq %r14
    movl %edi, %r12d
    movq %rsi, %r13
    movl %edx, %r14d
    testl %r14d, %r14d
    jz .Lwrite_many_ok
.Lwrite_many_loop:
    movl %r12d, %edi
    movq %r13, %rsi
    call pnstore_ata_write_sector
    testl %eax, %eax
    jz .Lwrite_many_fail
    incl %r12d
    addq $512, %r13
    decl %r14d
    jnz .Lwrite_many_loop
.Lwrite_many_ok:
    movl $1, %eax
    popq %r14
    popq %r13
    popq %r12
    ret
.Lwrite_many_fail:
    xorl %eax, %eax
    popq %r14
    popq %r13
    popq %r12
    ret

# int pnstore_ata_read_media(void *dst)
# Reads exactly the first 64 KiB (128 sectors) into the PNStore media buffer.
pnstore_ata_read_media:
    pushq %r12
    pushq %r13
    movq %rdi, %r13
    xorl %r12d, %r12d
.Lread_media_loop:
    movl %r12d, %edi
    movq %r13, %rsi
    call pnstore_ata_read_sector
    testl %eax, %eax
    jz .Lread_media_fail
    incl %r12d
    addq $512, %r13
    cmpl $PNSTORE_SECTORS, %r12d
    jb .Lread_media_loop
    movl $1, %eax
    popq %r13
    popq %r12
    ret
.Lread_media_fail:
    xorl %eax, %eax
    popq %r13
    popq %r12
    ret

# int pnstore_ata_flush(void)
# Issues ATA FLUSH CACHE (0xE7) and waits for completion.
pnstore_ata_flush:
    call .Lata_wait_ready
    testl %eax, %eax
    jz .Lflush_fail
    movw $ATA_COMMAND, %dx
    movb $ATA_CMD_FLUSH, %al
    outb %al, %dx
    call .Lata_wait_ready
    ret
.Lflush_fail:
    xorl %eax, %eax
    ret

.section .note.GNU-stack,"",@progbits
