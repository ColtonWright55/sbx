#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <time.h>

typedef unsigned __int128 u128;

u128 fibonacci(unsigned int n) {
    u128 a = 0;
    u128 b = 1;
    for (unsigned int i = 0; i < n; i++) {
        u128 c = a + b;
        a = b;
        b = c;
    }
    return b;
}

static long elapsed_nanos(struct timespec start, struct timespec end) {
    return (end.tv_sec - start.tv_sec) * 1000000000L + (end.tv_nsec - start.tv_nsec);
}

static double elapsed_secs(struct timespec start, struct timespec end) {
    return (double)elapsed_nanos(start, end) / 1e9;
}

static u128 upow(u128 base, unsigned int exp) {
    u128 result = 1;
    for (unsigned int i = 0; i < exp; i++) {
        result *= base;
    }
    return result;
}

static void print_u128(u128 x) {
    if (x == 0) { printf("0"); return; }
    char buf[41];
    int i = 40;
    buf[i] = '\0';
    while (x > 0 && i > 0) {
        buf[--i] = '0' + (int)(x % 10);
        x /= 10;
    }
    printf("%s", &buf[i]);
}

int main(void) {
    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);
    printf("Hello, world!\n");
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("Time elapsed in %ld ns\n", elapsed_nanos(start, end));
    printf("Time elapsed in %f seconds\n", elapsed_secs(start, end));

    unsigned int x = 186;
    clock_gettime(CLOCK_MONOTONIC, &start);
    u128 y = fibonacci(x);
    clock_gettime(CLOCK_MONOTONIC, &end);
    printf("Fibonacci of %u is ", x);
    print_u128(y);
    printf("\n");
    printf("Time elapsed in %ld ns\n", elapsed_nanos(start, end));

    u128 z = upow(2, 128) + 1;
    printf("2^128 + 1 (wrapped) = ");
    print_u128(z);
    printf("\n");

    return 0;
}
