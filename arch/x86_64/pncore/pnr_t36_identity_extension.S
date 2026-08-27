.section .pnr.t36extension,"a"
.align 16
.global pnr_t36_identity_extension
.global pnr_t36_identity_extension_end

# Append-only PNR extension. Historical PNR1 bytes remain unchanged.
pnr_t36_identity_extension:
    .long 0x58363354                    # "T36X"
    .long 1                             # extension version
    .long 0x00005900                    # T36 identity working record address
    .long 256                           # exact record bytes
    .long t36_identity_boot_entry       # pre-PNCore identity admission
    .long t36_identity_validate         # PNVH binding validator
    .long t36_identity_spinor_sheet     # phase_index & 1
    .long t36_identity_advance_tick     # bounded live tick evolution
    .long t36_identity_four_pi_closed   # two-tick lifted closure predicate
    .long 0                             # persistent device continuation not yet bound
    .long 0                             # State Memory bare-metal binding not yet bound
    .long 0                             # reserved
pnr_t36_identity_extension_end:

.if (pnr_t36_identity_extension_end - pnr_t36_identity_extension) != 48
.error "PNR T36 identity extension must be exactly 48 bytes"
.endif
