.code64
.section .text.pncore.scheduler,"ax"
.global pn_sched_classify_tick
.global pn_sched_admit_band
.type pn_sched_classify_tick, @function
.type pn_sched_admit_band, @function

# uint32_t pn_sched_classify_tick(uint64_t n)
# 0 -> invalid/unstarted
# n>=1 -> 1 + v2(n). No table and no independent band timers.
pn_sched_classify_tick:
    testq %rdi, %rdi
    jz .Lclass_zero
    bsfq %rdi, %rcx
    leal 1(%rcx), %eax
    ret
.Lclass_zero:
    xorl %eax, %eax
    ret

# uint32_t pn_sched_admit_band(uint64_t n)
# 1..7 -> current admitted band
# 0     -> no current v0.1 admission (invalid or RESERVED_QUIET)
pn_sched_admit_band:
    call pn_sched_classify_tick
    testl %eax, %eax
    jz .Ladmit_none
    cmpl $7, %eax
    ja .Ladmit_none
    ret
.Ladmit_none:
    xorl %eax, %eax
    ret

.global pn_sched_jitter_demote
.type pn_sched_jitter_demote, @function

# uint32_t pn_sched_jitter_demote(state*, abs_jitter, threshold)
# state layout: +0 current_band u32, +4 consecutive_over u32, +8 last_abs_jitter u64
# Three consecutive threshold violations demote one band. No automatic promotion.
pn_sched_jitter_demote:
    movq %rsi, 8(%rdi)
    cmpq %rdx, %rsi
    jbe .Ljitter_clear
    movl 4(%rdi), %eax
    incl %eax
    movl %eax, 4(%rdi)
    cmpl $3, %eax
    jb .Ljitter_return
    movl $0, 4(%rdi)
    movl 0(%rdi), %eax
    cmpl $7, %eax
    jae .Ljitter_return
    incl %eax
    movl %eax, 0(%rdi)
    ret
.Ljitter_clear:
    movl $0, 4(%rdi)
.Ljitter_return:
    movl 0(%rdi), %eax
    ret

.section .note.GNU-stack,"",@progbits
