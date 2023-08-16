#include <stdio.h>
int main(void)
{
    int i,j;

    for (i = 1; i <= 4; i++) {
        for (j = 1; j <= i; j++) {
            printf("%d", i);
        }
        printf("\n");
    }
    return(0);
}
