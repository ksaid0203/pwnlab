// gcc -O0 -g -no-pie -fno-omit-frame-pointer \
    -fstack-protector-all chall09_safe.c -o chall09_safe

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <unistd.h>
#include <inttypes.h>

struct Frame {
    char buf[16];
    uint64_t marker;
};

_Static_assert(
    offsetof(struct Frame, marker) == 16,
    "Unexpected structure layout"
);

int main(void) {
    struct Frame frame = {
        .buf = {0},
        .marker = 0x1122334455667788
    };

    printf("BUF: %p\n", (void *)frame.buf);
    printf("MARKER: %p\n", (void *)&frame.marker);

    printf("BEFORE: 0x%016" PRIx64 "\n", frame.marker);

    printf("Input: ");
    fflush(stdout);

    // 수정 전
    // ssize_t n = read(0, frame.buf, 24);

    // 수정 후
    ssize_t n = read(0, frame.buf, sizeof(frame.buf));

    printf("READ: %zd\n", n);
    printf("AFTER: 0x%016" PRIx64 "\n", frame.marker);

    printf("Inspect: ");
    fflush(stdout);

    getchar();

    return 0;
}
