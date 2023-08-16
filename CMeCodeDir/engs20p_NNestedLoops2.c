#include <stdio.h>
int main(void)
{
    int N, i, fact;
    
    N = 5;
    fact = 1;
    
    for (i=1; i<=N; i++)
        fact = fact*i;
    
    printf("%d! = %d\n", N, fact);

    return(0);
}
