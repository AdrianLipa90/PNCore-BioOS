.code64
.section .text.pncore.clock,"ax"
.global pn_clock_init_rational
.global pn_clock_probe_tsc_deadline_exact
.global pn_clock_deadline_for_tick
.global pn_clock_next_after_tsc
.type pn_clock_init_rational, @function
.type pn_clock_probe_tsc_deadline_exact, @function
.type pn_clock_deadline_for_tick, @function
.type pn_clock_next_after_tsc, @function

# PNClock state v0.1 (96 bytes)
.equ PNC_MAGIC,            0
.equ PNC_VERSION,          4
.equ PNC_SOURCE,           8
.equ PNC_FLAGS,           12
.equ PNC_BASE_TSC,        16
.equ PNC_INTERVAL_NUM,    24
.equ PNC_INTERVAL_DEN,    32
.equ PNC_CURRENT_TICK,    40
.equ PNC_CURRENT_DEADLINE,48
.equ PNC_MISSED_TOTAL,    56
.equ PNC_LAST_JITTER,     64
.equ PNC_MAX_ABS_JITTER,  72
.equ PNC_CPUID15_DEN,     80
.equ PNC_CPUID15_NUM,     84
.equ PNC_CRYSTAL_HZ,      88
.equ PNC_BYTES,           92
.equ PNC_STATE_BYTES,     96

.equ PNC_SOURCE_NONE,                  0
.equ PNC_SOURCE_TSC_DEADLINE_EXACT,    1
.equ PNC_FLAG_TSC,                     1
.equ PNC_FLAG_TSC_DEADLINE,            2
.equ PNC_FLAG_INVARIANT_TSC,           4
.equ PNC_FLAG_CPUID15_EXACT,           8

# int pn_clock_init_rational(state*, den, num, crystal_hz, base_tsc)
# SysV: RDI=state, ESI=CPUID.15 denominator, EDX=numerator,
#       ECX=crystal Hz, R8=base TSC.
# The 7.83 Hz interval is represented exactly as the rational:
#   interval_num = crystal_hz * num * 100
#   interval_den = den * 783
# deadline(n) = base_tsc + floor(n * interval_num / interval_den)
pn_clock_init_rational:
    testl %esi, %esi
    jz .Lratio_fail
    testl %edx, %edx
    jz .Lratio_fail
    testl %ecx, %ecx
    jz .Lratio_fail

    movl %esi, %r10d
    movl %edx, %r9d
    movl %ecx, %r11d

    movl $0x4c434e50, PNC_MAGIC(%rdi)       # "PNCL"
    movl $1, PNC_VERSION(%rdi)
    movl $PNC_SOURCE_TSC_DEADLINE_EXACT, PNC_SOURCE(%rdi)
    movl $(PNC_FLAG_TSC|PNC_FLAG_TSC_DEADLINE|PNC_FLAG_INVARIANT_TSC|PNC_FLAG_CPUID15_EXACT), PNC_FLAGS(%rdi)
    movq %r8, PNC_BASE_TSC(%rdi)

    movq %r11, %rax
    imulq %r9, %rax
    imulq $100, %rax
    testq %rax, %rax
    jz .Lratio_fail
    movq %rax, PNC_INTERVAL_NUM(%rdi)

    movq %r10, %rax
    imulq $783, %rax
    testq %rax, %rax
    jz .Lratio_fail
    movq %rax, PNC_INTERVAL_DEN(%rdi)

    movq $0, PNC_CURRENT_TICK(%rdi)
    movq %r8, PNC_CURRENT_DEADLINE(%rdi)
    movq $0, PNC_MISSED_TOTAL(%rdi)
    movq $0, PNC_LAST_JITTER(%rdi)
    movq $0, PNC_MAX_ABS_JITTER(%rdi)
    movl %r10d, PNC_CPUID15_DEN(%rdi)
    movl %r9d, PNC_CPUID15_NUM(%rdi)
    movl %r11d, PNC_CRYSTAL_HZ(%rdi)
    movl $PNC_STATE_BYTES, PNC_BYTES(%rdi)
    movl $1, %eax
    ret

.Lratio_fail:
    xorl %eax, %eax
    ret

# int pn_clock_probe_tsc_deadline_exact(state*)
# Admits this source only when hardware exposes:
# - TSC and TSC-deadline
# - invariant TSC
# - CPUID.15 exact denominator/numerator/crystal frequency
# Missing exact frequency is not approximated from CPU base MHz.
pn_clock_probe_tsc_deadline_exact:
    pushq %rbx
    pushq %r12
    movq %rdi, %r12

    # Clear the state first; failure remains SOURCE_NONE.
    xorq %rax, %rax
    movq %rdi, %r10
    movl $12, %ecx
.Lclear_state:
    movq %rax, (%r10)
    addq $8, %r10
    decl %ecx
    jnz .Lclear_state
    movl $0x4c434e50, PNC_MAGIC(%r12)
    movl $1, PNC_VERSION(%r12)
    movl $PNC_STATE_BYTES, PNC_BYTES(%r12)

    xorl %eax, %eax
    cpuid
    cmpl $0x15, %eax
    jb .Lprobe_fail
    movl %eax, %r8d                         # max basic leaf

    movl $1, %eax
    xorl %ecx, %ecx
    cpuid
    btl $4, %edx                            # TSC
    jnc .Lprobe_fail
    btl $24, %ecx                           # TSC deadline
    jnc .Lprobe_fail

    movl $0x80000000, %eax
    cpuid
    cmpl $0x80000007, %eax
    jb .Lprobe_fail
    movl $0x80000007, %eax
    xorl %ecx, %ecx
    cpuid
    btl $8, %edx                            # invariant TSC
    jnc .Lprobe_fail

    cmpl $0x15, %r8d
    jb .Lprobe_fail
    movl $0x15, %eax
    xorl %ecx, %ecx
    cpuid
    testl %eax, %eax                        # denominator
    jz .Lprobe_fail
    testl %ebx, %ebx                        # numerator
    jz .Lprobe_fail
    testl %ecx, %ecx                        # crystal Hz
    jz .Lprobe_fail

    movl %eax, %esi
    movl %ebx, %edx
    # ECX already crystal Hz.
    rdtsc
    shlq $32, %rdx
    orq %rdx, %rax
    movq %rax, %r8
    movq %r12, %rdi
    call pn_clock_init_rational
    jmp .Lprobe_done

.Lprobe_fail:
    xorl %eax, %eax
.Lprobe_done:
    popq %r12
    popq %rbx
    ret

# uint64_t pn_clock_deadline_for_tick(state*, tick)
# RDI=state, RSI=tick. Returns absolute TSC deadline in RAX.
pn_clock_deadline_for_tick:
    movq %rsi, %rax
    mulq PNC_INTERVAL_NUM(%rdi)             # RDX:RAX = tick * N
    divq PNC_INTERVAL_DEN(%rdi)             # RAX = floor(tick*N/D)
    addq PNC_BASE_TSC(%rdi), %rax
    ret

# uint64_t pn_clock_next_after_tsc(state*, now_tsc)
# Returns the first absolute phase-grid deadline strictly after now.
# Updates current tick and skip/jitter evidence in state.
# This is O(1) and never emits catch-up deadlines.
pn_clock_next_after_tsc:
    movq %rsi, %r11                         # now
    movq PNC_BASE_TSC(%rdi), %r8            # base

    # Jitter of the event that brought us here, if a deadline was armed.
    movq PNC_CURRENT_TICK(%rdi), %r10
    testq %r10, %r10
    jz .Lno_jitter
    movq %r11, %rax
    subq PNC_CURRENT_DEADLINE(%rdi), %rax
    movq %rax, PNC_LAST_JITTER(%rdi)
    movq %rax, %rdx
    sarq $63, %rdx
    xorq %rdx, %rax
    subq %rdx, %rax                         # abs(jitter)
    cmpq PNC_MAX_ABS_JITTER(%rdi), %rax
    jbe .Lno_jitter
    movq %rax, PNC_MAX_ABS_JITTER(%rdi)
.Lno_jitter:

    # If now <= base, the first tick is n=1.
    cmpq %r8, %r11
    jbe .Lm_ready_one

    # m = floor((now-base) * D / N) + 1
    movq %r11, %rax
    subq %r8, %rax
    mulq PNC_INTERVAL_DEN(%rdi)
    divq PNC_INTERVAL_NUM(%rdi)
    incq %rax
    movq %rax, %r9                          # candidate m
    jmp .Lcompute_deadline

.Lm_ready_one:
    movq $1, %r9

.Lcompute_deadline:
    movq %r9, %rax
    mulq PNC_INTERVAL_NUM(%rdi)
    divq PNC_INTERVAL_DEN(%rdi)
    addq %r8, %rax                          # candidate deadline
    cmpq %r11, %rax
    ja .Ldeadline_future

    # Integer flooring can land exactly on now; advance one phase slot once.
    incq %r9
    movq %r9, %rax
    mulq PNC_INTERVAL_NUM(%rdi)
    divq PNC_INTERVAL_DEN(%rdi)
    addq %r8, %rax

.Ldeadline_future:
    # skipped = max(new_tick - old_tick - 1, 0)
    movq PNC_CURRENT_TICK(%rdi), %r10
    movq %r9, %rdx
    subq %r10, %rdx
    cmpq $1, %rdx
    jbe .Lno_skip_add
    decq %rdx
    addq %rdx, PNC_MISSED_TOTAL(%rdi)
.Lno_skip_add:
    movq %r9, PNC_CURRENT_TICK(%rdi)
    movq %rax, PNC_CURRENT_DEADLINE(%rdi)
    ret

.section .note.GNU-stack,"",@progbits
