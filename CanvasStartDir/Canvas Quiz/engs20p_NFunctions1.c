#include <stdio.h>

/* prototypes */
int sum(int x, int y);

/* main function */
int main(void)
{
    int a = 5;
    int b = 8;
    int c;
    
    c = sum(a,b);
    printf("\n%d + %d = %d\n", a, b, c);
    
    return(0);
}

/* function definitions */
int sum(int x, int y) 
{
    int result;
    
    printf("Starting computation!\n");
    result = x + y;
    printf("Completed computation, result found!\n");
    return(result);
}