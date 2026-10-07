.section .rodata.pncore.vector_native_qhtri_replay,"a"
.global vector_native_qhtri_replay_payload
.global vector_native_qhtri_replay_payload_end
.align 8
vector_native_qhtri_replay_payload:
    .incbin "build/x86_64/vector_native_qhtri_replay_v01.bin"
vector_native_qhtri_replay_payload_end:
.section .note.GNU-stack,"",@progbits
