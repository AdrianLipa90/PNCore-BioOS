.code16
.section .text
.global pnrom_entry
.type pnrom_entry, @function
pnrom_entry:
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
pnrom_halt:
    hlt
    jmp pnrom_halt

.section .reset,"ax"
.global reset_vector
.type reset_vector, @function
reset_vector:
    ljmp $0xf000, $0x0000
    .fill 11,1,0x90
