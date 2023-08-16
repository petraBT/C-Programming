#include <stdio.h>

/* prototypes */

int main(void) {
    int input, answer;
    printf("Please enter n: ");    
    scanf("%d", &input);
    answer = sumOfDigits(input);
    printf("The sum of the digits of the number %d equals %d.", input, answer);
    return(0);
}

/* functions go here */
