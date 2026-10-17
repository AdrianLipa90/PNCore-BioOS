/* PNCore native PNAML 36D + exact typed-state exchange; x86-64 System V.
 * Slot +0 version, +8 payload capacity, +16 length, +24 generation,
 * +32 source_sequence, +40 published, +48 phase36 [288], +336 opaque state.
 * Intact typed RDSS/PNCS bytes travel separately from phase; no admission
 * or semantic retyping; no C/Python/Rust runtime and no phase collapse.
 * ABI:
 * int pncore_pnaml_init(void *slot, uint64_t capacity)
 * int pncore_pnaml_publish(void *slot,const void*phi36,const void*typed,
 *                         uint64_t len,uint64_t generation,uint64_t sequence)
 * int pncore_pnaml_consume(const void*slot,void*phi36,void*typed,
 *                         uint64_t typed_capacity,uint64_t meta[3])
 * codes: 0=ok,1=null,2=capacity,3=writer busy or changed,5=not published
 */
.intel_syntax noprefix
.text
.p2align 4
.globl pncore_pnaml_init
.type pncore_pnaml_init,@function
pncore_pnaml_init:
  test rdi,rdi
  jz .Li_null
  mov qword ptr [rdi],0
  mov qword ptr [rdi+8],rsi
  mov qword ptr [rdi+16],0
  mov qword ptr [rdi+24],0
  mov qword ptr [rdi+32],0
  mov qword ptr [rdi+40],0
  xor eax,eax
  ret
.Li_null:
  mov eax,1
  ret
.size pncore_pnaml_init,.-pncore_pnaml_init

.p2align 4
.globl pncore_pnaml_publish
.type pncore_pnaml_publish,@function
pncore_pnaml_publish:
  test rdi,rdi
  jz .Lp_null
  test rsi,rsi
  jz .Lp_null
  test rcx,rcx
  jz .Lp_len_ok
  test rdx,rdx
  jz .Lp_null
.Lp_len_ok:
  cmp rcx,qword ptr [rdi+8]
  ja .Lp_capacity
  lock bts qword ptr [rdi],0
  jc .Lp_busy
  push rbx
  push r12
  push r13
  push r14
  push r15
  mov rbx,rdi
  mov r12,rsi
  mov r13,rdx
  mov r14,rcx
  mov r15,r8
  mov qword ptr [rbx+16],r14
  mov qword ptr [rbx+24],r15
  mov qword ptr [rbx+32],r9
  lea rdi,[rbx+48]
  mov rsi,r12
  mov ecx,288
  cld
  rep movsb
  lea rdi,[rbx+336]
  mov rsi,r13
  mov rcx,r14
  rep movsb
  mov qword ptr [rbx+40],1
  lock inc qword ptr [rbx]
  pop r15
  pop r14
  pop r13
  pop r12
  pop rbx
  xor eax,eax
  ret
.Lp_null:
  mov eax,1
  ret
.Lp_capacity:
  mov eax,2
  ret
.Lp_busy:
  mov eax,3
  ret
.size pncore_pnaml_publish,.-pncore_pnaml_publish

.p2align 4
.globl pncore_pnaml_consume
.type pncore_pnaml_consume,@function
pncore_pnaml_consume:
  test rdi,rdi
  jz .Lc_null
  test rsi,rsi
  jz .Lc_null
  test r8,r8
  jz .Lc_null
  push rbx
  push rbp
  push r12
  push r13
  push r14
  push r15
  mov rbx,rdi
  mov r12,rsi
  mov r13,rdx
  mov r14,rcx
  mov r15,r8
  mov ebp,64
.Lc_retry:
  mov r10,qword ptr [rbx]
  test r10,1
  jnz .Lc_again
  cmp qword ptr [rbx+40],0
  je .Lc_nopub
  mov r11,qword ptr [rbx+16]
  cmp r11,r14
  ja .Lc_cap_verify
  test r11,r11
  jz .Lc_data_ok
  test r13,r13
  jz .Lc_null_ret
.Lc_data_ok:
  mov r8,qword ptr [rbx+24]
  mov r9,qword ptr [rbx+32]
  lea rsi,[rbx+48]
  mov rdi,r12
  mov ecx,288
  cld
  rep movsb
  lea rsi,[rbx+336]
  mov rdi,r13
  mov rcx,r11
  rep movsb
  lfence
  cmp r10,qword ptr [rbx]
  jne .Lc_again
  mov qword ptr [r15],r11
  mov qword ptr [r15+8],r8
  mov qword ptr [r15+16],r9
  xor eax,eax
  jmp .Lc_done
.Lc_cap_verify:
  lfence
  cmp r10,qword ptr [rbx]
  jne .Lc_again
  mov eax,2
  jmp .Lc_done
.Lc_nopub:
  lfence
  cmp r10,qword ptr [rbx]
  jne .Lc_again
  mov eax,5
  jmp .Lc_done
.Lc_again:
  dec ebp
  jnz .Lc_retry
  mov eax,3
  jmp .Lc_done
.Lc_null_ret:
  mov eax,1
.Lc_done:
  pop r15
  pop r14
  pop r13
  pop r12
  pop rbp
  pop rbx
  ret
.Lc_null:
  mov eax,1
  ret
.size pncore_pnaml_consume,.-pncore_pnaml_consume
.section .note.GNU-stack,"",@progbits
