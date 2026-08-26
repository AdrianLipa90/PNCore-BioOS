.code16
.section .reset,"ax"
.global reset_vector
.type reset_vector, @function
reset_vector:
    # x86 reset vector -> PNROM entry at physical 0x000F0000.
    ljmp $0xf000, $0x0000
    .fill 11,1,0x90
