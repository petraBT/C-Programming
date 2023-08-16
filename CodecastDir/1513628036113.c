#define DEBUG 1
#include <stdio.h>
int main(void)
{
    int N, i, sum;
    i = 1;
    N = 10;
    sum = 0;
    #if (DEBUG >=1)
        printf("BEFORE LOOP.\n");
    #endif
    while (i <= N) {
	    #if (DEBUG>=2)
            printf("IN LOOP: i = %d, sum = %d.\n", i, sum);
        #endif
	    sum += i;
	    i++;
    }
    #if (DEBUG >=1)
        printf("AFTER LOOP.\n");
    #endif
    printf("The sum from 1 to %d equals %d.\n", N, sum);
    return(0);
}