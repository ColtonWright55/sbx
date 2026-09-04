#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "memtests.h"

// use-after-free: read/write through freed memory. rust: value moved/dropped, won't compile. cpp: unique_ptr is null after move.
void use_after_free(void) {
    int *p = malloc(sizeof(int));
    *p = 1;
    free(p);
    *p = 2;
}

// double-free: free() called twice on the same pointer, corrupts heap metadata. rust: ownership makes this uncompilable. cpp: shared_ptr/unique_ptr free once.
void double_free(void) {
    int *p = malloc(sizeof(int));
    free(p);
    free(p);
}

// memory leak: allocation with no matching free, only reclaimed at process exit. rust: Box<T> frees on drop. cpp: RAII / unique_ptr frees on scope exit.
void memory_leak(void) {
    int *p = malloc(sizeof(int));
    *p = 1;
}

// dangling pointer: address of a stack local outlives its frame. rust: borrow checker rejects this. cpp: never return &local; compilers warn (-Wreturn-local-addr).
int *dangling_pointer(void) {
    int local = 42;
    return &local;
}

// stack buffer overflow: write past a fixed-size array on the stack, smashes adjacent frame data. rust: slice indexing panics. cpp: std::array::at() bounds-checks, operator[] doesn't.
void stack_buffer_overflow(void) {
    char buf[8];
    memset(buf, 'A', 16);
}

// heap buffer overflow: write past a malloc'd block's end, corrupts heap metadata/adjacent allocation. rust: Vec panics out-of-bounds. cpp: vector::at() bounds-checks, operator[] doesn't.
void heap_buffer_overflow(void) {
    char *buf = malloc(8);
    buf[8] = 'A';
    free(buf);
}

// null pointer dereference: segfault reading/writing through NULL. rust: Option<T> forces an explicit check. cpp: still segfaults unless checked.
void null_deref(void) {
    int *p = NULL;
    *p = 1;
}

// uninitialized read: using a variable before it's assigned reads garbage (UB). rust: won't compile, must initialize. cpp: no default init for primitives either.
void uninitialized_read(void) {
    int x;
    if (x == 0) {
        printf("zero\n");
    }
}

// stack overflow: unbounded recursion exhausts the call stack. rust: same risk, no guard by default. cpp: same, tail-call elision isn't guaranteed.
void stack_overflow_bug(void) {
    volatile char pad[64];
    pad[0] = 0;
    stack_overflow_bug();
}

// integer overflow -> undersized malloc -> heap overflow: classic combo, size_t multiply wraps small. rust: checked_mul/Vec::with_capacity would panic. cpp: same risk unless you check.
void integer_overflow_heap(void) {
    size_t n = (size_t)-1 / 2 + 2;
    int *buf = malloc(n * sizeof(int));
    buf[0] = 1;
}

// format string bug: user-controlled data passed as the format itself leaks the stack or crashes. rust: format! is compile-time checked. cpp: no printf-family without a literal format, or use std::format.
void format_string_bug(void) {
    char *user_input = "%s%s%s%s";
    printf(user_input);
}
