#include <stdio.h>
int main(void)
{
    int N, i, sum;
    i = 1;
    N = 10;
    sum = 0;
    
    printf("BEFORE LOOP.\n");
    while (i <= N) {
        #ifdef DEBUG
            printf("IN LOOP: i = %d, sum = %d.\n", i, sum);
        #else 
            printf("ALL GOOD!\n");
        #endif
	    sum += i;
	    i++;
    }
    printf("AFTER LOOP.\n");
    printf("The sum from 1 to %d equals %d.\n", N, sum);
    return(0);
}