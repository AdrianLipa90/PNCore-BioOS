.code16
.section .text.pnrom.entry,"ax"
.global pnrom_lm_entry
.type pnrom_lm_entry, @function

.set PN_PNVH,          0x5000
.set PN_SIGMA0,        0x5200
.set PN_EVIDENCE,      0x5300
.set PN_MAP_EVIDENCE,  0x5400
.set PN_T36_IDENTITY,  0x5900
.set PN_PML4,          0x7000
.set PN_PDPT,          0x8000
.set PN_PD,            0x9000

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

pnrom_lm_entry:
    cli
    cld
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'R'
    OUTC 'O'
    OUTC 'M'
    OUTC 0x0a

    # x86_64 domain admission: extended CPUID + Long Mode bit.
    movl $0x80000000, %eax
    cpuid
    cmpl $0x80000001, %eax
    jb pnrom_lm_unsupported
    movl $0x80000001, %eax
    cpuid
    testl $0x20000000, %edx
    jz pnrom_lm_unsupported

    # Load GDT while CS still anchors the ROM segment.
    movw %cs, %ax
    movw %ax, %ds
    lgdt gdt_descriptor - pnrom_lm_entry

    # PNMap physical substrate: one deterministic 2 MiB identity window.
    xorw %ax, %ax
    movw %ax, %ds
    movw %ax, %es
    movw $PN_PML4, %di
    movw $0x1800, %cx
    xorw %ax, %ax
    rep stosw

    movl $0x00008003, PN_PML4
    movl $0x00000000, PN_PML4+4
    movl $0x00009003, PN_PDPT
    movl $0x00000000, PN_PDPT+4
    movl $0x00000083, PN_PD
    movl $0x00000000, PN_PD+4

    # Enter protected mode.
    movl %cr0, %eax
    orl $0x00000001, %eax
    movl %eax, %cr0
    ljmpl $0x0008, $pnrom_protected32

pnrom_lm_unsupported:
    movw $0x00e9, %dx
    OUTC '!'
pnrom_lm_unsupported_halt:
    hlt
    jmp pnrom_lm_unsupported_halt

.code32
pnrom_protected32:
    movw $0x0010, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %ss

    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC '3'
    OUTC '2'
    OUTC 0x0a

    # PAE + exact PNMap root.
    movl %cr4, %eax
    orl $0x00000020, %eax
    movl %eax, %cr4
    movl $PN_PML4, %eax
    movl %eax, %cr3

    # IA32_EFER.LME = 1.
    movl $0xc0000080, %ecx
    rdmsr
    orl $0x00000100, %eax
    wrmsr

    # Paging + PE -> long mode activation.
    movl %cr0, %eax
    orl $0x80000000, %eax
    movl %eax, %cr0
    ljmp $0x0018, $pnrom_long64

.code64
pnrom_long64:
    movw $0x0010, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %ss
    movq $0x6ff0, %rsp

    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC '6'
    OUTC '4'
    OUTC 0x0a

    # Firmware -> PNCore state carriers.
    # PNVH remains the exact 36D bootstrap state carrier.
    movl $pnvh_template, %esi
    movl $PN_PNVH, %edi
    movl $416, %ecx
    cld
    rep movsb

    # T36 identity is a separately provisioned exact 256-byte identity/configuration
    # record. It does not duplicate the 288-byte PNVH phase vector.
    movl $t36_identity_template, %esi
    movl $PN_T36_IDENTITY, %edi
    movl $256, %ecx
    cld
    rep movsb

    # Identity admission executes before the existing PNCore transition spine.
    jmp t36_identity_boot_entry

.align 8
gdt:
    .quad 0x0000000000000000
    .quad 0x00cf9a000000ffff
    .quad 0x00cf92000000ffff
    .quad 0x00af9a000000ffff
gdt_end:

gdt_descriptor:
    .word gdt_end - gdt - 1
    .long gdt
