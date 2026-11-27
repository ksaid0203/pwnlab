#include <stdio.h>

int main(void) {
    char name[64];
    printf("Name: ");
    fflush(stdout);

    fgets(name, sizeof(name), stdin);
    printf("Hello, %s", name);
    return 0;
}