#include <stdio.h>
int main(void)
{
    int N, i, fact;
    
    
    for (N=1; N<=10; N++) 
        fact = 1;
        for (i=1; i<=N; i++)
            fact = fact*i;
    
        printf("%d! = %d\n", N, fact);
    
    return(0);
}
