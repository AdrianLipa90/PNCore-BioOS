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
