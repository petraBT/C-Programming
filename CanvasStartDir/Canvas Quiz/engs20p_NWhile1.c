#include <stdio.h>
int main(void) {
    int N=5;
    int i, fac;
    
    i = 1;
    fac = 1;
    
    while (i<=N) {
        fac = fac * i;
        i = i+1;
    }
    
    printf("\n%d! = %d. \n", N, fac);
    return(0);
}