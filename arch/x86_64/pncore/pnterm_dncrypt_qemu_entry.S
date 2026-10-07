.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry,@function

.set PN_STORE_MEDIA,       0x10000
.set PN_STORE_EVIDENCE,    0x5800
.set PNTERM_LINE_BUF,      0x6000
.set PNTERM_LINE_LEN,      0x6100
.set PNTERM_IGNORE_LF,     0x6104
.set PNTERM_RX_SEQ,        0x6108
.set PNTERM_MAX_LINE,      255
.set PNTERM_UART_BASE,     0x03f8
.set PNTERM_SPIN_BUDGET,   1000000

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

# Interactive QEMU vertical slice:
#   PNROM/T36 -> PNStore ATA-PIO exact DNCrypt envelope -> UART16550 PNTERM.
# It intentionally implements a narrow ASCII read-only realization subset of
# PNTERM v0.1. The full UTF-8/token/envelope/PNCAP semantic path remains a
# separate higher-level conformance surface and is not claimed by this ROM.
pncore_entry:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'C'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'T'
    OUTC 'E'
    OUTC 'R'
    OUTC 'M'
    OUTC 0x0a

    # Load complete PNStore medium from primary-master IDE.
    movl $PN_STORE_MEDIA, %edi
    call pnstore_ata_read_media
    cmpl $1, %eax
    jne pncore_fail

    movl $PN_STORE_MEDIA, %edi
    movl $65536, %esi
    call pnstore_verify_super
    cmpl $1, %eax
    je .Lexisting_medium

    # First-use is admitted only for an all-zero device image.
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

    # Persist superblock first, then FLUSH.
    movl $0, %edi
    movl $PN_STORE_MEDIA, %esi
    call pnstore_ata_write_sector
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    # Prepare generation 1 with the complete pinned DNCrypt binary envelope.
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

    # Durable order gate 1: extent -> FLUSH.
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

    # Durable order gate 2: HEAD_A -> FLUSH.
    movl $1, %edi
    movl $(PN_STORE_MEDIA+512), %esi
    call pnstore_ata_write_sector
    cmpl $1, %eax
    jne pncore_fail
    call pnstore_ata_flush
    cmpl $1, %eax
    jne pncore_fail

    # Destroy RAM state and require recovery from device bytes.
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
    call pnterm_verify_exact_dncrypt_extent
    cmpl $1, %eax
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
    jmp .Lstore_ready

.Lexisting_medium:
    movl $PN_STORE_MEDIA, %edi
    call pnstore_recover
    cmpq $1, %rax
    jne pncore_fail
    cmpq $512, %rdx
    jne pncore_fail
    call pnterm_verify_exact_dncrypt_extent
    cmpl $1, %eax
    jne pncore_fail

    # Stable transition must resolve as ALREADY_COMMITTED without mutation.
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

.Lstore_ready:
    movl $0x544e5050, PN_STORE_EVIDENCE+0   # "PPNT" witness marker
    movl $1, PN_STORE_EVIDENCE+4
    movl $PNSTORE_DNCRYPT_PAYLOAD_LEN, PN_STORE_EVIDENCE+8
    movl $1, PN_STORE_EVIDENCE+12           # exact payload verified
    movl $1, PN_STORE_EVIDENCE+16           # PNStore recovery verified
    movl $0, PN_STORE_EVIDENCE+20           # physical machine claim FALSE

    # Bind the existing UART16550 physical adapter primitive to this QEMU slice.
    movl $PNTERM_UART_BASE, %edi
    call pnterm_uart16550_probe
    cmpl $1, %eax
    jne pncore_fail
    movl $PNTERM_UART_BASE, %edi
    call pnterm_uart16550_init_115200_8n1
    cmpl $1, %eax
    jne pncore_fail

    movl $0, PNTERM_LINE_LEN
    movl $0, PNTERM_IGNORE_LF
    movq $0, PNTERM_RX_SEQ
    movb $0, PNTERM_LINE_BUF

    movl $pnterm_banner, %edi
    call pnterm_puts
    movl $pnterm_scope, %edi
    call pnterm_puts
    call pnterm_prompt

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
    movl $PNTERM_UART_BASE, %edi
    movl $PNTERM_SPIN_BUDGET, %esi
    call pnterm_uart16550_getc_poll
    cmpl $-1, %eax
    je .Lrx_loop
    movb %al, %r12b

    # CRLF collapses to one line ending.
    cmpb $0x0a, %r12b
    jne .Lnot_lf
    cmpl $1, PNTERM_IGNORE_LF
    jne .Lline_end_lf
    movl $0, PNTERM_IGNORE_LF
    jmp .Lrx_loop
.Lline_end_lf:
    movl $0, PNTERM_IGNORE_LF
    jmp .Lline_end
.Lnot_lf:
    cmpb $0x0d, %r12b
    jne .Lnot_cr
    movl $1, PNTERM_IGNORE_LF
    jmp .Lline_end
.Lnot_cr:
    movl $0, PNTERM_IGNORE_LF

    # Editing: BS and DEL remove one byte in this ASCII realization.
    cmpb $0x08, %r12b
    je .Lbackspace
    cmpb $0x7f, %r12b
    je .Lbackspace

    # TAB is retained as a token separator but normalized to one ASCII space in
    # this narrow realization. All other controls and non-ASCII bytes reject.
    cmpb $0x09, %r12b
    je .Ltab
    cmpb $0x20, %r12b
    jb .Lcontrol_reject
    cmpb $0x7e, %r12b
    ja .Lcontrol_reject
    jmp .Lappend_char
.Ltab:
    movb $0x20, %r12b

.Lappend_char:
    movl PNTERM_LINE_LEN, %ecx
    cmpl $PNTERM_MAX_LINE, %ecx
    jae .Loverflow
    movb %r12b, PNTERM_LINE_BUF(%rcx)
    incl %ecx
    movl %ecx, PNTERM_LINE_LEN
    movb $0, PNTERM_LINE_BUF(%rcx)
    movzbl %r12b, %edi
    call pnterm_putc
    jmp .Lrx_loop

.Lbackspace:
    movl PNTERM_LINE_LEN, %ecx
    testl %ecx, %ecx
    jz .Lrx_loop
    decl %ecx
    movl %ecx, PNTERM_LINE_LEN
    movb $0, PNTERM_LINE_BUF(%ecx)
    movl $pnterm_backspace_echo, %edi
    call pnterm_puts
    jmp .Lrx_loop

.Lcontrol_reject:
    call pnterm_newline
    movl $pnterm_err_control, %edi
    call pnterm_puts
    call pnterm_reset_line
    call pnterm_prompt
    jmp .Lrx_loop

.Loverflow:
    call pnterm_newline
    movl $pnterm_err_overflow, %edi
    call pnterm_puts
    call pnterm_reset_line
    call pnterm_prompt
    jmp .Lrx_loop

.Lline_end:
    call pnterm_newline
    movl PNTERM_LINE_LEN, %eax
    testl %eax, %eax
    jz .Ldispatch_done
    incq PNTERM_RX_SEQ
    call pnterm_dispatch_readonly
.Ldispatch_done:
    call pnterm_reset_line
    call pnterm_prompt
    jmp .Lrx_loop

# Exact current extent binding: transition, object digest, payload length and all
# payload bytes must match the pinned DNCrypt fixture.
pnterm_verify_exact_dncrypt_extent:
    pushq %rbx
    movl $(PN_STORE_MEDIA+4096), %ebx
    cmpl $PNSTORE_DNCRYPT_PAYLOAD_LEN, 88(%rbx)
    jne .Lverify_fail
    leaq 24(%rbx), %rdi
    movl $pnstore_dncrypt_transition_id, %esi
    movl $32, %ecx
    cld
    repe cmpsb
    jne .Lverify_fail
    leaq 56(%rbx), %rdi
    movl $pnstore_dncrypt_object_digest, %esi
    movl $32, %ecx
    repe cmpsb
    jne .Lverify_fail
    leaq 96(%rbx), %rdi
    movl $pnstore_dncrypt_payload, %esi
    movl $PNSTORE_DNCRYPT_PAYLOAD_LEN, %ecx
    repe cmpsb
    jne .Lverify_fail
    movl $1, %eax
    popq %rbx
    ret
.Lverify_fail:
    xorl %eax, %eax
    popq %rbx
    ret

pnterm_reset_line:
    movl $0, PNTERM_LINE_LEN
    movb $0, PNTERM_LINE_BUF
    ret

pnterm_prompt:
    movl $pnterm_prompt_text, %edi
    jmp pnterm_puts

pnterm_newline:
    movl $pnterm_newline_text, %edi
    jmp pnterm_puts

# void pnterm_putc(uint8_t ch in DIL); fatal fail-closed on UART timeout.
pnterm_putc:
    pushq %rbx
    movzbl %dil, %ebx
    movl $PNTERM_UART_BASE, %edi
    movl %ebx, %esi
    movl $PNTERM_SPIN_BUDGET, %edx
    call pnterm_uart16550_putc_poll
    cmpl $1, %eax
    jne .Lputc_fail
    popq %rbx
    ret
.Lputc_fail:
    popq %rbx
    jmp pncore_fail

# void pnterm_puts(const char *p in EDI)
pnterm_puts:
    pushq %rbx
    movl %edi, %ebx
.Lputs_loop:
    movzbl (%rbx), %eax
    testb %al, %al
    jz .Lputs_done
    movzbl %al, %edi
    call pnterm_putc
    incl %ebx
    jmp .Lputs_loop
.Lputs_done:
    popq %rbx
    ret

# int pnterm_streq(buf in EDI, literal in ESI)
pnterm_streq:
.Lstreq_loop:
    movb (%rdi), %al
    movb (%rsi), %dl
    cmpb %dl, %al
    jne .Lstreq_no
    testb %al, %al
    je .Lstreq_yes
    incq %rdi
    incq %rsi
    jmp .Lstreq_loop
.Lstreq_yes:
    movl $1, %eax
    ret
.Lstreq_no:
    xorl %eax, %eax
    ret

pnterm_dispatch_readonly:
    movl $PNTERM_LINE_BUF, %edi
    movl $cmd_help, %esi
    call pnterm_streq
    testl %eax, %eax
    jnz .Lcmd_help

    movl $PNTERM_LINE_BUF, %edi
    movl $cmd_status, %esi
    call pnterm_streq
    testl %eax, %eax
    jnz .Lcmd_status

    movl $PNTERM_LINE_BUF, %edi
    movl $cmd_store_show, %esi
    call pnterm_streq
    testl %eax, %eax
    jnz .Lcmd_store

    movl $PNTERM_LINE_BUF, %edi
    movl $cmd_selftest, %esi
    call pnterm_streq
    testl %eax, %eax
    jnz .Lcmd_selftest

    # echo or echo <opaque ASCII argument bytes>
    cmpl $0x6f686365, PNTERM_LINE_BUF        # "echo" little-endian
    jne .Lcmd_unknown
    movzbl PNTERM_LINE_BUF+4, %eax
    testb %al, %al
    je .Lcmd_echo_empty
    cmpb $0x20, %al
    jne .Lcmd_unknown
    movl $pnterm_echo_prefix, %edi
    call pnterm_puts
    movl $(PNTERM_LINE_BUF+5), %edi
    call pnterm_puts
    call pnterm_newline
    ret
.Lcmd_echo_empty:
    movl $pnterm_echo_prefix, %edi
    call pnterm_puts
    call pnterm_newline
    ret

.Lcmd_help:
    movl $resp_help, %edi
    call pnterm_puts
    ret
.Lcmd_status:
    call pnterm_verify_exact_dncrypt_extent
    cmpl $1, %eax
    jne .Lcmd_store_invalid
    movl $resp_status, %edi
    call pnterm_puts
    ret
.Lcmd_store:
    movl $PN_STORE_MEDIA, %edi
    call pnstore_recover
    cmpq $1, %rax
    jne .Lcmd_store_invalid
    cmpq $512, %rdx
    jne .Lcmd_store_invalid
    call pnterm_verify_exact_dncrypt_extent
    cmpl $1, %eax
    jne .Lcmd_store_invalid
    movl $resp_store, %edi
    call pnterm_puts
    ret
.Lcmd_store_invalid:
    movl $pnterm_err_store, %edi
    call pnterm_puts
    ret
.Lcmd_selftest:
    movl $PNTERM_UART_BASE, %edi
    call pnterm_uart16550_probe
    cmpl $1, %eax
    jne .Lcmd_selftest_fail
    call pnterm_verify_exact_dncrypt_extent
    cmpl $1, %eax
    jne .Lcmd_selftest_fail
    movl $resp_selftest, %edi
    call pnterm_puts
    ret
.Lcmd_selftest_fail:
    movl $pnterm_err_selftest, %edi
    call pnterm_puts
    ret
.Lcmd_unknown:
    movl $pnterm_err_unknown, %edi
    call pnterm_puts
    ret

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

pnterm_banner:          .asciz "BioOS PNTERM QEMU v0.1\r\n"
pnterm_scope:           .asciz "READONLY ASCII VERTICAL-SLICE / no shell / no write commands\r\n"
pnterm_prompt_text:     .asciz "bioos> "
pnterm_newline_text:    .asciz "\r\n"
pnterm_backspace_echo:  .asciz "\b \b"
pnterm_echo_prefix:     .asciz "ECHO "
pnterm_err_control:     .asciz "ERR CONTROL_CHAR_REJECTED\r\n"
pnterm_err_overflow:    .asciz "ERR LINE_BYTES_OVERFLOW\r\n"
pnterm_err_unknown:     .asciz "ERR UNKNOWN_COMMAND\r\n"
pnterm_err_store:       .asciz "ERR STORE_STATE_INVALID\r\n"
pnterm_err_selftest:    .asciz "ERR SELFTEST_FAILED\r\n"
cmd_help:               .asciz "help"
cmd_status:             .asciz "status"
cmd_store_show:         .asciz "store.show"
cmd_selftest:           .asciz "terminal.selftest"
resp_help:              .asciz "CMDS help status store.show terminal.selftest echo\r\n"
resp_status:            .asciz "STATUS PASS READONLY UART16550 PNSTORE_DNCRYPT=EXACT\r\n"
resp_store:             .asciz "STORE GEN=1 HEAD=A PAYLOAD=2552 MAGIC=DNCB EXACT=1\r\n"
resp_selftest:          .asciz "SELFTEST PASS UART16550 PNSTORE EXACT_DNCRYPT\r\n"

.section .note.GNU-stack,"",@progbits
