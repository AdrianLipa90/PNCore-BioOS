.code64
.section .text.pncore.entry,"ax"
.global pncore_entry
.type pncore_entry,@function

.set PN_STORE_MEDIA,       0x10000
.set PN_STORE_MODE,        0x5b00
.set PNTERM_UART,          0x03f8
.set PNTERM_BUF,           0x5c00
.set PNTERM_LEN,           0x5d00
.set PNTERM_DISCARD,       0x5d04
.set PNTERM_LAST_CR,       0x5d08
.set PNTERM_LINE_MAX,      128
.set PNTERM_SPIN,          1000000

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

# First integrated live-system vertical slice:
# PNROM -> T36 -> PNStore ATA-PIO persistent system state -> PNTERM UART console.
# The console remains read-only; storage initialization is an internal boot
# transition bound to the pinned DNCrypt fixture and exactly-once transition id.
pncore_entry:
    movw $0x00e9, %dx
    OUTC 'P'
    OUTC 'N'
    OUTC 'C'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'L'
    OUTC 'I'
    OUTC 'V'
    OUTC 'E'
    OUTC 0x0a

    movl $0, PN_STORE_MODE

    # Read the complete persistent medium from QEMU primary-master IDE.
    movl $PN_STORE_MEDIA, %edi
    call pnstore_ata_read_media
    cmpl $1, %eax
    jne pncore_fail

    movl $PN_STORE_MEDIA, %edi
    movl $65536, %esi
    call pnstore_verify_super
    cmpl $1, %eax
    je .Lstore_existing

    # First-use formatting is allowed only on a completely zero medium.
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

    # Prepared extent -> FLUSH -> HEAD_A -> FLUSH.
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

    # Erase RAM copy and prove the state comes back from the IDE medium.
    movl $PN_STORE_MEDIA, %edi
    xorq %rax, %rax
    movl $8192, %ecx
    cld
    rep stosq
    movl $PN_STORE_MEDIA, %edi
    call pnstore_ata_read_media
    cmpl $1, %eax
    jne pncore_fail
    movl $1, PN_STORE_MODE
    jmp .Lstore_verify_exact

.Lstore_existing:
    movl $2, PN_STORE_MODE

.Lstore_verify_exact:
    # Recover generation 1 and HEAD_A.
    movl $PN_STORE_MEDIA, %edi
    call pnstore_recover
    cmpq $1, %rax
    jne pncore_fail
    cmpq $512, %rdx
    jne pncore_fail

    # Verify the current immutable extent carries exactly the pinned transition,
    # object digest, payload length, and complete DNCrypt binary bytes.
    cmpl $PNSTORE_DNCRYPT_PAYLOAD_LEN, PN_STORE_MEDIA+4096+88
    jne pncore_fail
    movl $(PN_STORE_MEDIA+4096+24), %esi
    movl $pnstore_dncrypt_transition_id, %edi
    movl $32, %ecx
    cld
    repe cmpsb
    jne pncore_fail
    movl $(PN_STORE_MEDIA+4096+56), %esi
    movl $pnstore_dncrypt_object_digest, %edi
    movl $32, %ecx
    repe cmpsb
    jne pncore_fail
    movl $(PN_STORE_MEDIA+4096+96), %esi
    movl $pnstore_dncrypt_payload, %edi
    movl $PNSTORE_DNCRYPT_PAYLOAD_LEN, %ecx
    repe cmpsb
    jne pncore_fail

    # Same stable transition must be historical ALREADY_COMMITTED.
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
    cmpl $1, PN_STORE_MODE
    jne .Ldebug_store_recover
    OUTC 'P'
    OUTC 'N'
    OUTC 'S'
    OUTC 'T'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'N'
    OUTC 'E'
    OUTC 'W'
    OUTC 0x0a
    jmp .Ldebug_store_ok
.Ldebug_store_recover:
    OUTC 'P'
    OUTC 'N'
    OUTC 'S'
    OUTC 'T'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'R'
    OUTC 'E'
    OUTC 'C'
    OUTC 'O'
    OUTC 'V'
    OUTC 'E'
    OUTC 'R'
    OUTC 0x0a
.Ldebug_store_ok:
    OUTC 'P'
    OUTC 'N'
    OUTC 'S'
    OUTC 'T'
    OUTC 'O'
    OUTC 'R'
    OUTC 'E'
    OUTC '.'
    OUTC 'O'
    OUTC 'K'
    OUTC 0x0a

    # Bring up the existing bounded UART16550 physical adapter.
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

    movl $0, PNTERM_LEN
    movl $0, PNTERM_DISCARD
    movl $0, PNTERM_LAST_CR
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

    cmpl $10, %r10d
    jne .Lnot_lf
    cmpl $1, PNTERM_LAST_CR
    jne .Llf_normal
    movl $0, PNTERM_LAST_CR
    jmp .Lrx_loop
.Llf_normal:
    cmpl $0, PNTERM_DISCARD
    je .Lline_end
    movl $0, PNTERM_DISCARD
    movl $0, PNTERM_LEN
    call pnterm_console_prompt
    jmp .Lrx_loop
.Lnot_lf:
    movl $0, PNTERM_LAST_CR

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

pnterm_console_dispatch:
    pushq %rbx
    movl PNTERM_LEN, %ebx

    cmpl $4, %ebx
    jne .Ltry_status
    cmpl $0x706c6568, PNTERM_BUF          # help
    jne .Ltry_store_show
    movl $pnterm_help, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done

.Ltry_status:
    cmpl $6, %ebx
    jne .Ltry_store_show
    cmpl $0x74617473, PNTERM_BUF          # stat
    jne .Ltry_store_show
    cmpw $0x7375, PNTERM_BUF+4            # us
    jne .Ltry_store_show
    movl $pnterm_status, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done

.Ltry_store_show:
    cmpl $10, %ebx
    jne .Ltry_echo
    cmpl $0x726f7473, PNTERM_BUF          # stor
    jne .Ltry_echo
    cmpl $0x68732e65, PNTERM_BUF+4        # e.sh
    jne .Ltry_echo
    cmpw $0x776f, PNTERM_BUF+8            # ow
    jne .Ltry_echo
    cmpl $1, PN_STORE_MODE
    jne .Lstore_show_recover
    movl $pnterm_store_new, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done
.Lstore_show_recover:
    movl $pnterm_store_recover, %esi
    call pnterm_console_puts
    jmp .Ldispatch_done

.Ltry_echo:
    cmpl $4, %ebx
    jb .Lunknown
    cmpl $0x6f686365, PNTERM_BUF          # echo
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

.section .rodata.pncore.live,"a"
.align 16
pnstore_dncrypt_transition_id:
    .incbin "build/x86_64/pnstore_dncrypt_transition_id.bin"
pnstore_dncrypt_object_digest:
    .incbin "build/x86_64/pnstore_dncrypt_object_digest.bin"
pnstore_dncrypt_payload:
    .incbin "build/x86_64/pnstore_dncrypt_payload.bin"
pnstore_dncrypt_payload_end:
.set PNSTORE_DNCRYPT_PAYLOAD_LEN, pnstore_dncrypt_payload_end-pnstore_dncrypt_payload

pnterm_banner:
    .asciz "BioOS Live QEMU v0.1\r\n"
pnterm_prompt:
    .asciz "bioos> "
pnterm_crlf:
    .asciz "\r\n"
pnterm_help:
    .asciz "help status store.show echo\r\n"
pnterm_status:
    .asciz "console=READY store=READY authority=READ_ONLY canon=false\r\n"
pnterm_store_new:
    .asciz "store=READY generation=1 boot=NEW payload=DNCB persisted=true\r\n"
pnterm_store_recover:
    .asciz "store=READY generation=1 boot=RECOVER payload=DNCB persisted=true\r\n"
pnterm_err_unknown:
    .asciz "ERR UNKNOWN\r\n"
pnterm_err_control:
    .asciz "ERR CONTROL\r\n"
pnterm_err_nonascii:
    .asciz "ERR NONASCII\r\n"
pnterm_err_overflow:
    .asciz "ERR OVERFLOW\r\n"

.section .note.GNU-stack,"",@progbits
