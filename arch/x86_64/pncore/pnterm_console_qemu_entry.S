.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry,@function

.set PNTERM_UART,       0x03f8
.set PNTERM_BUF,        0x5c00
.set PNTERM_LEN,        0x5d00
.set PNTERM_DISCARD,    0x5d04
.set PNTERM_LAST_CR,    0x5d08
.set PNTERM_LINE_MAX,   128
.set PNTERM_SPIN,       1000000

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

# Dedicated interactive QEMU realization. It deliberately does not replace the
# normal PNCore entrypoint. It exercises the already-defined UART16550 adapter
# with a bounded read-only PNTERM subset while the normal full-boot and PNStore
# gates remain independent.
pncore_entry:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'C'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'C'
    OUTC 'O'
    OUTC 'N'
    OUTC 'S'
    OUTC 'O'
    OUTC 'L'
    OUTC 'E'
    OUTC 0x0a

    movl $0, PNTERM_LEN
    movl $0, PNTERM_DISCARD
    movl $0, PNTERM_LAST_CR

    movl $PNTERM_UART, %edi
    call pnterm_uart16550_probe
    cmpl $1, %eax
    jne pncore_fail

    movl $PNTERM_UART, %edi
    call pnterm_uart16550_init_115200_8n1
    cmpl $1, %eax
    jne pncore_fail

    movw $0x00e9, %dx
    OUTC 'U'
    OUTC 'A'
    OUTC 'R'
    OUTC 'T'
    OUTC '.'
    OUTC 'O'
    OUTC 'K'
    OUTC 0x0a

    movl $pnterm_banner, %esi
    call pnterm_console_puts
    call pnterm_console_prompt

    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'T'
    OUTC 'E'
    OUTC 'R'
    OUTC 'M'
    OUTC '.'
    OUTC 'R'
    OUTC 'E'
    OUTC 'A'
    OUTC 'D'
    OUTC 'Y'
    OUTC 0x0a

.Lrx_loop:
    movl $PNTERM_UART, %edi
    movl $PNTERM_SPIN, %esi
    call pnterm_uart16550_getc_poll
    cmpl $-1, %eax
    je .Lrx_loop
    movzbl %al, %r10d

    # CRLF is one terminator: LF directly following a consumed CR is ignored.
    cmpl $10, %r10d
    jne .Lnot_lf
    cmpl $1, PNTERM_LAST_CR
    jne .Llf_normal
    movl $0, PNTERM_LAST_CR
    jmp .Lrx_loop
.Llf_normal:
    # If this LF closes a line already failed closed, reset the discipline
    # instance and do not dispatch the discarded bytes.
    cmpl $0, PNTERM_DISCARD
    je .Lline_end
    movl $0, PNTERM_DISCARD
    movl $0, PNTERM_LEN
    call pnterm_console_prompt
    jmp .Lrx_loop
.Lnot_lf:
    movl $0, PNTERM_LAST_CR

    # After a discipline error, discard the remainder of that line and reset
    # only at the next canonical terminator.
    cmpl $0, PNTERM_DISCARD
    je .Lnot_discard
    cmpl $13, %r10d
    je .Ldiscard_cr
    jmp .Lrx_loop
.Ldiscard_cr:
    movl $1, PNTERM_LAST_CR
    movl $0, PNTERM_DISCARD
    movl $0, PNTERM_LEN
    call pnterm_console_prompt
    jmp .Lrx_loop

.Lnot_discard:
    cmpl $13, %r10d
    je .Lline_end_cr
    cmpl $8, %r10d
    je .Lbackspace
    cmpl $127, %r10d
    je .Lbackspace
    cmpl $9, %r10d
    je .Lstore_byte
    cmpl $32, %r10d
    jb .Lcontrol_error
    cmpl $126, %r10d
    ja .Lnonascii_error
    jmp .Lstore_byte

.Lbackspace:
    movl PNTERM_LEN, %eax
    testl %eax, %eax
    jz .Lrx_loop
    decl %eax
    movl %eax, PNTERM_LEN
    jmp .Lrx_loop

.Lstore_byte:
    movl PNTERM_LEN, %eax
    cmpl $PNTERM_LINE_MAX, %eax
    jae .Loverflow_error
    movb %r10b, PNTERM_BUF(%rax)
    incl %eax
    movl %eax, PNTERM_LEN
    jmp .Lrx_loop

.Lline_end_cr:
    movl $1, PNTERM_LAST_CR
.Lline_end:
    movl $pnterm_crlf, %esi
    call pnterm_console_puts
    cmpl $0, PNTERM_LEN
    je .Lline_done
    call pnterm_console_dispatch
.Lline_done:
    movl $0, PNTERM_LEN
    call pnterm_console_prompt
    jmp .Lrx_loop

.Lcontrol_error:
    movl $pnterm_err_control, %esi
    jmp .Ldiscipline_error
.Lnonascii_error:
    movl $pnterm_err_nonascii, %esi
    jmp .Ldiscipline_error
.Loverflow_error:
    movl $pnterm_err_overflow, %esi
.Ldiscipline_error:
    movl $0, PNTERM_LEN
    movl $1, PNTERM_DISCARD
    call pnterm_console_puts
    jmp .Lrx_loop

# Bounded read-only dispatch subset: help, status, echo.
# No write verb, arbitrary shell, address access, or physical effect is admitted.
pnterm_console_dispatch:
    pushq %rbx
    movl PNTERM_LEN, %ebx

    cmpl $4, %ebx
    jne .Ltry_status
    cmpl $0x706c6568, PNTERM_BUF          # "help"
    jne .Ltry_echo
    movl $pnterm_help, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done

.Ltry_status:
    cmpl $6, %ebx
    jne .Ltry_echo
    cmpl $0x74617473, PNTERM_BUF          # "stat"
    jne .Ltry_echo
    cmpw $0x7375, PNTERM_BUF+4            # "us"
    jne .Ltry_echo
    movl $pnterm_status, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done

.Ltry_echo:
    cmpl $4, %ebx
    jb .Lunknown
    cmpl $0x6f686365, PNTERM_BUF          # "echo"
    jne .Lunknown
    cmpl $4, %ebx
    je .Lecho_empty
    movzbl PNTERM_BUF+4, %eax
    cmpl $32, %eax
    je .Lecho_args
    cmpl $9, %eax
    jne .Lunknown
.Lecho_args:
    movl $PNTERM_BUF+5, %esi
    movl %ebx, %ecx
    subl $5, %ecx
    call pnterm_console_write_n
.Lecho_empty:
    movl $pnterm_crlf, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done

.Lunknown:
    movl $pnterm_err_unknown, %esi
    call pnterm_console_puts
.Ldispatch_done:
    popq %rbx
    ret

pnterm_console_prompt:
    pushq %rsi
    movl $pnterm_prompt, %esi
    call pnterm_console_puts
    popq %rsi
    ret

# RSI -> NUL-terminated ASCII string.
pnterm_console_puts:
    pushq %rbx
    movq %rsi, %rbx
.Lputs_loop:
    movzbl (%rbx), %esi
    testb %sil, %sil
    jz .Lputs_done
    movl $PNTERM_UART, %edi
    movl $PNTERM_SPIN, %edx
    call pnterm_uart16550_putc_poll
    cmpl $1, %eax
    jne pncore_fail
    incq %rbx
    jmp .Lputs_loop
.Lputs_done:
    popq %rbx
    ret

# RSI -> bytes, ECX -> exact byte count.
pnterm_console_write_n:
    pushq %rbx
    pushq %r12
    movq %rsi, %rbx
    movl %ecx, %r12d
.Lwrite_n_loop:
    testl %r12d, %r12d
    jz .Lwrite_n_done
    movzbl (%rbx), %esi
    movl $PNTERM_UART, %edi
    movl $PNTERM_SPIN, %edx
    call pnterm_uart16550_putc_poll
    cmpl $1, %eax
    jne pncore_fail
    incq %rbx
    decl %r12d
    jmp .Lwrite_n_loop
.Lwrite_n_done:
    popq %r12
    popq %rbx
    ret

pncore_fail:
    movw $0x00e9, %dx
    OUTC 'X'
    OUTC 0x0a
.Lfail_halt:
    hlt
    jmp .Lfail_halt

.section .rodata.pncore.console,"a"
pnterm_banner:
    .asciz "BioOS PNTERM QEMU v0.1\r\n"
pnterm_prompt:
    .asciz "bioos> "
pnterm_crlf:
    .asciz "\r\n"
pnterm_help:
    .asciz "help status echo\r\n"
pnterm_status:
    .asciz "console=READY authority=READ_ONLY canon=false\r\n"
pnterm_err_unknown:
    .asciz "ERR UNKNOWN\r\n"
pnterm_err_control:
    .asciz "ERR CONTROL\r\n"
pnterm_err_nonascii:
    .asciz "ERR NONASCII\r\n"
pnterm_err_overflow:
    .asciz "ERR OVERFLOW\r\n"

.section .note.GNU-stack,"",@progbits
