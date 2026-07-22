#include <stdio.h>

/* prototype here */
int factorial(int);

int main(void) {
    
    int num;
    int result;
    
    printf("Please enter an integer: ");
    scanf("%d", &num);
    
    result = factorial(num);
    
    printf("\n%d! = %d. \n", num, result);
    
    return(0);
}

/* function here */
int factorial(int N) {
    if (N>1) return(N*factorial(N-1));
    else if ((N==0) || (N==1)) return 1;
    else return(-1);
}
