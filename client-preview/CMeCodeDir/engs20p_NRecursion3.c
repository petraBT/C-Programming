#include <stdio.h>

/* prototypes */

int main(void) {
    int input, answer;
    printf("Which Fibonacci number would you like? ");
    scanf("%d", &input);
    answer = fib(input);
    printf("The %dth Fibonacci number is %d.\n", input, answer);
    return(0);
}

/* functions go here */
