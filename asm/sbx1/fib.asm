/* fib.asm - GAS x86-64 Linux, raw syscalls only, no libc.
   Usage: ./fib N   -> prints fib(N) followed by a newline. */

.global _start

.section .text
_start:
    mov 16(%rsp), %rsi     /* argv[1]: pointer to decimal string for n */

    /* --- parse decimal string at rsi into rdi (n) --- */
    xor %rdi, %rdi
.parse_loop:
    movzbl (%rsi), %eax
    cmp $'0', %al
    jb .parse_done
    cmp $'9', %al
    ja .parse_done
    sub $'0', %al
    movzbl %al, %eax
    imul $10, %rdi, %rdi
    add %rax, %rdi
    inc %rsi
    jmp .parse_loop
.parse_done:
    /* rdi = n */

    /* --- compute fib(n) iteratively; fib(0)=0, fib(1)=1 --- */
    xor %rax, %rax         /* a = fib(0) */
    mov $1, %rbx            /* b = fib(1) */
    test %rdi, %rdi
    jz .fib_done
.fib_loop:
    lea (%rax,%rbx), %rcx
    mov %rbx, %rax
    mov %rcx, %rbx
    dec %rdi
    jnz .fib_loop
.fib_done:
    /* rax = fib(n) */

    /* --- convert rax to a decimal string, built backwards into buffer --- */
    lea buffer+20(%rip), %rsi
    movb $10, (%rsi)        /* trailing newline */
    mov $10, %rcx
.conv_loop:
    xor %rdx, %rdx
    div %rcx
    add $'0', %dl
    dec %rsi
    mov %dl, (%rsi)
    test %rax, %rax
    jnz .conv_loop

    /* --- write(1, rsi, buffer+21 - rsi) --- */
    lea buffer+21(%rip), %rdx
    sub %rsi, %rdx
    mov $1, %rax
    mov $1, %rdi
    syscall

    /* --- exit(0) --- */
    mov $60, %rax
    xor %rdi, %rdi
    syscall

.section .bss
buffer:
    .skip 21
