.code64
.section .text.pncore.pnterm_uart16550,"ax"

# PNTERM x86_64 16550 polling adapter candidate.
# All entry points are physical adapter primitives below AUX admission.

.global pnterm_uart16550_probe
.global pnterm_uart16550_init_115200_8n1
.global pnterm_uart16550_tx_ready
.global pnterm_uart16550_rx_ready
.global pnterm_uart16550_putc_poll
.global pnterm_uart16550_getc_poll

.type pnterm_uart16550_probe, @function
.type pnterm_uart16550_init_115200_8n1, @function
.type pnterm_uart16550_tx_ready, @function
.type pnterm_uart16550_rx_ready, @function
.type pnterm_uart16550_putc_poll, @function
.type pnterm_uart16550_getc_poll, @function

# int pnterm_uart16550_probe(uint16_t base)
# Scratch-register reversible probe. Returns 1 on match, 0 on mismatch.
pnterm_uart16550_probe:
    movw %di, %dx
    addw $7, %dx
    inb %dx, %al
    movb %al, %r8b
    movb $0x5a, %al
    outb %al, %dx
    inb %dx, %al
    movb %al, %r9b
    movb %r8b, %al
    outb %al, %dx
    xorl %eax, %eax
    cmpb $0x5a, %r9b
    sete %al
    ret

# int pnterm_uart16550_init_115200_8n1(uint16_t base)
# Reference clock assumption belongs to admitted adapter resource metadata.
# divisor=1; 8N1; FIFO enabled/cleared; DTR/RTS/OUT2 asserted.
pnterm_uart16550_init_115200_8n1:
    movw %di, %dx
    # IER = 0
    incw %dx
    xorl %eax, %eax
    outb %al, %dx
    # LCR = DLAB
    addw $2, %dx
    movb $0x80, %al
    outb %al, %dx
    # DLL = 1
    subw $3, %dx
    movb $0x01, %al
    outb %al, %dx
    # DLM = 0
    incw %dx
    xorl %eax, %eax
    outb %al, %dx
    # LCR = 8N1
    addw $2, %dx
    movb $0x03, %al
    outb %al, %dx
    # FCR = enable + clear RX/TX + 14-byte trigger
    decw %dx
    movb $0xc7, %al
    outb %al, %dx
    # MCR = DTR | RTS | OUT2
    addw $2, %dx
    movb $0x0b, %al
    outb %al, %dx
    movl $1, %eax
    ret

# int pnterm_uart16550_tx_ready(uint16_t base)
pnterm_uart16550_tx_ready:
    movw %di, %dx
    addw $5, %dx
    inb %dx, %al
    shrb $5, %al
    andl $1, %eax
    ret

# int pnterm_uart16550_rx_ready(uint16_t base)
pnterm_uart16550_rx_ready:
    movw %di, %dx
    addw $5, %dx
    inb %dx, %al
    andl $1, %eax
    ret

# int pnterm_uart16550_putc_poll(uint16_t base, uint8_t ch, uint32_t spin_budget)
# Returns 1 after THR write, 0 on bounded timeout.
pnterm_uart16550_putc_poll:
    movl %edx, %ecx
    testl %ecx, %ecx
    jz .Lput_timeout
    movw %di, %r8w
.Lput_wait:
    movw %r8w, %dx
    addw $5, %dx
    inb %dx, %al
    testb $0x20, %al
    jnz .Lput_write
    decl %ecx
    jnz .Lput_wait
.Lput_timeout:
    xorl %eax, %eax
    ret
.Lput_write:
    movw %r8w, %dx
    movb %sil, %al
    outb %al, %dx
    movl $1, %eax
    ret

# int pnterm_uart16550_getc_poll(uint16_t base, uint32_t spin_budget)
# Returns [0,255] on byte read, -1 on bounded timeout.
pnterm_uart16550_getc_poll:
    movl %esi, %ecx
    testl %ecx, %ecx
    jz .Lget_timeout
    movw %di, %r8w
.Lget_wait:
    movw %r8w, %dx
    addw $5, %dx
    inb %dx, %al
    testb $0x01, %al
    jnz .Lget_read
    decl %ecx
    jnz .Lget_wait
.Lget_timeout:
    movl $-1, %eax
    ret
.Lget_read:
    movw %r8w, %dx
    inb %dx, %al
    movzbl %al, %eax
    ret

.section .note.GNU-stack,"",@progbits
