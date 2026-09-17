.section .pnvh.template,"a"
.align 16
.global pnvh_template
.global pnvh_template_end
pnvh_template:
    .incbin "build/x86_64/pnstore_ide_pnvh.bin"
pnvh_template_end:
