.code64
.section .text.pncore.t36boot,"ax"
.global t36_identity_boot_entry
.type t36_identity_boot_entry, @function

.set PN_PNVH,         0x5000
.set PN_T36_IDENTITY, 0x5900
.set PN_T36_SCRATCH,  0x5a00

.macro OUTC ch
    movb $\ch, %al
    outb %al, %dx
.endm

# Pre-PNCore identity admission gate.
# The exact record is host/provisioning-derived and copied from ROM by PNROM.
# This gate validates binding to the admitted PNVH and proves the two-tick
# lifted 4*pi closure on an isolated scratch copy before entering pncore_entry.
t36_identity_boot_entry:
    movw $0x00e9, %dx

    movl $PN_T36_IDENTITY, %edi
    movl $PN_PNVH, %esi
    call t36_identity_validate
    cmpl $1, %eax
    jne t36_identity_boot_fail

    movl $PN_T36_SCRATCH, %edi
    movl $PN_T36_IDENTITY, %esi
    call t36_identity_materialize

    movl $PN_T36_SCRATCH, %edi
    call t36_identity_spinor_sheet
    testq %rax, %rax
    jne t36_identity_boot_fail

    movl $PN_T36_SCRATCH, %edi
    call t36_identity_advance_tick
    movl $PN_T36_SCRATCH, %edi
    call t36_identity_spinor_sheet
    cmpq $1, %rax
    jne t36_identity_boot_fail

    movl $PN_T36_SCRATCH, %edi
    call t36_identity_advance_tick
    movl $PN_T36_SCRATCH, %edi
    call t36_identity_spinor_sheet
    testq %rax, %rax
    jne t36_identity_boot_fail

    movl $PN_T36_IDENTITY, %edi
    movl $PN_T36_SCRATCH, %esi
    call t36_identity_four_pi_closed
    cmpl $1, %eax
    jne t36_identity_boot_fail

    OUTC 'T'
    OUTC '3'
    OUTC '6'
    OUTC 'I'
    OUTC 'D'
    OUTC 0x0a
    jmp pncore_entry

t36_identity_boot_fail:
    movw $0x00e9, %dx
    OUTC 'I'
    OUTC '!'
    OUTC 0x0a
.Lhalt:
    hlt
    jmp .Lhalt
