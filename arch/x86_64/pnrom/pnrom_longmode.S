.code16
.section .text
.global pnrom_lm_entry
.type pnrom_lm_entry, @function
pnrom_lm_entry:
    cli
    movw $0x00e9, %dx
    movb $'P', %al
    outb %al, %dx
    movb $'N', %al
    outb %al, %dx
    movb $'R', %al
    outb %al, %dx
    movb $'O', %al
    outb %al, %dx
    movb $'M', %al
    outb %al, %dx
    movb $0x0a, %al
    outb %al, %dx

    movl $0x80000000, %eax
    cpuid
    cmpl $0x80000001, %eax
    jb pnrom_lm_unsupported
    movl $0x80000001, %eax
    cpuid
    testl $0x20000000, %edx
    jz pnrom_lm_unsupported

    movw %cs, %ax
    movw %ax, %ds
    lgdt gdt_descriptor - pnrom_lm_entry

    xorw %ax, %ax
    movw %ax, %ds
    movw %ax, %es
    movw $0x7000, %di
    movw $0x1800, %cx
    xorw %ax, %ax
    rep stosw

    movl $0x00008003, 0x7000
    movl $0x00000000, 0x7004
    movl $0x00009003, 0x8000
    movl $0x00000000, 0x8004
    movl $0x00000083, 0x9000
    movl $0x00000000, 0x9004

    movl %cr0, %eax
    orl $0x00000001, %eax
    movl %eax, %cr0
    ljmpl $0x0008, $pnrom_protected32

pnrom_lm_unsupported:
    movw $0x00e9, %dx
    movb $'!', %al
    outb %al, %dx
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
    movb $'P', %al
    outb %al, %dx
    movb $'N', %al
    outb %al, %dx
    movb $'3', %al
    outb %al, %dx
    movb $'2', %al
    outb %al, %dx
    movb $0x0a, %al
    outb %al, %dx

    movl %cr4, %eax
    orl $0x00000020, %eax
    movl %eax, %cr4
    movl $0x00007000, %eax
    movl %eax, %cr3

    movl $0xc0000080, %ecx
    rdmsr
    orl $0x00000100, %eax
    wrmsr

    movl %cr0, %eax
    orl $0x80000000, %eax
    movl %eax, %cr0
    ljmp $0x0018, $pnrom_long64

.code64
pnrom_long64:
    movw $0x00e9, %dx
    movb $'P', %al
    outb %al, %dx
    movb $'N', %al
    outb %al, %dx
    movb $'6', %al
    outb %al, %dx
    movb $'4', %al
    outb %al, %dx
    movb $0x0a, %al
    outb %al, %dx
pnrom_long64_halt:
    hlt
    jmp pnrom_long64_halt

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

.code16
.section .reset,"ax"
.global reset_vector
.type reset_vector, @function
reset_vector:
    ljmp $0xf000, $0x0000
    .fill 11,1,0x90
