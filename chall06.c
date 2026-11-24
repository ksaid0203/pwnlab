# gcc -O0 -g -no-pie chall.c -o chall
#include <stdio.h>

int global_value = 1234;
int empty_value;

void hello(void) {
    puts("Hello, pwntools!");
}

void secret(void) {
    puts("Secret function!");
}

int main(void) {
    hello();
    printf("Value: %d\n", global_value);
    return 0;
}
