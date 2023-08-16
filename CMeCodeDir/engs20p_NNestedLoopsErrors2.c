#include <stdio.h>
int main(void)
{
    int i;
    
    for (i=0; i<3; i++) {
        for (i=0; i<8; i++)
            printf("*");
        printf("\n");
    }
    printf("\n");
    return(0);
}
