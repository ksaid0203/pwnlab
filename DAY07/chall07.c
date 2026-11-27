// gcc -O0 -g -no-pie -Wl,-z,lazy chall07.c -o chall07
#include <stdio.h>
#include <unistd.h>

int main(void) {
    char buf[32];

    puts("Welcome to Day 7!");

    printf("PID: %d\n", getpid());

    write(1, "Input: ", 7);
    read(0, buf, sizeof(buf));

    puts("Done!");

    return 0;
}

