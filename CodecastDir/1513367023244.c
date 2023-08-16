#include <stdio.h>

/* prototypes */
int sum(int x, int y);
int difference(int x, int y);
int binomial(int m, int n);

/* main function */
int main(void) {
    int a = 5;
    int b = 8;
    int c;
    
    c = sum(a,b);
    printf("\n%d + %d = %d\n", a, b, c);
    printf("\n%d - %d = %d\n", a, b, difference(a,b));
    printf("\n%d^2-%d^2 = %d\n", a, b, binomial(a,b));
    return(0);
}

/* function definitions */
int sum(int x, int y) {
    int result;
    result = x + y;
    return(result);
}

int difference(int x, int y) {
    return(x-y);
}

/* a^2 - b^2 = (a+b)(a-b) */
int binomial(int m, int n) {
    return(sum(m,n)*difference(m,n));
}
