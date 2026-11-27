// gcc -O0 -g -no-pie -fno-omit-frame-pointer chall08.c -o chall08

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

__attribute__((noinline))
void inspect_stack(void) {
    volatile uint64_t marker = 0x1122334455667788;
    char buf[32] = "STACK_TEST";

    void *rbp = __builtin_frame_address(0);
    void *ret = __builtin_return_address(0);

    printf("RBP: %p\n", rbp);
    printf("BUF: %p\n", (void *)buf);
    printf("MARKER: %p\n", (void *)&marker);
    printf("RET: %p\n", ret);

    printf("Input: ");
    fflush(stdout);

    read(0, buf, sizeof(buf));
}

int main(void) {
    inspect_stack();
    puts("Returned to main!");
    return 0;
}
