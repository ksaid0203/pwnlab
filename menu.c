
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char name[64];
    char choice[16];

    while (1) {
        printf("\n1. Set name\n");
        printf("2. Show name\n");
        printf("3. Exit\n");
        printf("Choice: ");
        fflush(stdout);

        if (!fgets(choice, sizeof(choice), stdin))
            break;

        switch (atoi(choice)) {
            case 1:
                printf("Name: ");
                fflush(stdout);

                if (!fgets(name, sizeof(name), stdin))
                    return 1;

                name[strcspn(name, "\n")] = '\0';
                break;

            case 2:
                printf("Your name: %s\n", name);
                break;

            case 3:
                puts("Bye!");
                return 0;

            default:
                puts("Invalid choice");
        }
    }

    return 0;
}
