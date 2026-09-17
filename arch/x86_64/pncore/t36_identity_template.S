.section .pnr.t36identity,"a"
.align 16
.global t36_identity_template
.global t36_identity_template_end

t36_identity_template:
    .incbin "build/x86_64/t36_identity_test.bin"
t36_identity_template_end:

.if (t36_identity_template_end - t36_identity_template) != 256
.error "T36 identity template must be exactly 256 bytes"
.endif

.section .note.GNU-stack,"",@progbits
