#include <stdio.h>
int main(void)
{
    int N, i, sum;
    
    i = 1;
    N = 10;
    sum = 0;

    printf("BEFORE LOOP.\n");
    while (i <= N) {
	    printf("IN LOOP: i = %d\n", i);
	    sum += i;
    }
    printf("AFTER LOOP.\n");
    
    return(0);
}