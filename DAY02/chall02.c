
#include <stdio.h>
#include <unistd.h>

int main(void) {
    char buf[32];

    printf("MENU> ");
    fflush(stdout);

    if (fgets(buf, sizeof(buf), stdin) == NULL)
        return 1;

    write(1, "ABCDEFGH", 8);
    write(1, "\nDONE\n", 6);

    return 0;
}
