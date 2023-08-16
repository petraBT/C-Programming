#include <stdio.h>
int main(void)
{
    int i;
    int p = 3;
    
    printf("Printing numbers divisible by %d: \n", p);
    
    for (i=0; i<p*10; i++){
        if (i%p==0)
            printf("\n%d\n", i);
        else
            printf("-");
    }
    return(0);
}
