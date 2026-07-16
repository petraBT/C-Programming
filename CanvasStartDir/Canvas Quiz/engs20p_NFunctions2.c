#include <stdio.h>

/* prototypes */
int sum(int x, int y);
int difference(int x, int y);

/* main function */
int main(void)
{
    int a = 5;
    int b = 8;
    int c;
    
    c = sum(a,b);
    printf("\n%d + %d = %d\n", a, b, c);
    
    printf("\n%d - %d = %d\n", a, b, difference(a,b));
    
    return(0);
}

/* function definitions */
int sum(int x, int y) 
{
    int result;
    
    result = x + y;
    return(result);
}

int difference(int x, int y)
{
    return(x-y);
}