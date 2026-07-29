/* Simplest possible x86-64 Linux program: exit(42) via syscall, no libc. */
.global _start

.section .text
_start:
    mov $60, %rax   /* syscall: exit */
    mov $42, %rdi   /* exit code */
    syscall
