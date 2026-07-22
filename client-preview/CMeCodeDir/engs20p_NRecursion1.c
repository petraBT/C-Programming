#include <stdio.h>

/* prototypes */

int main(void) {
    int input, answer;
    printf("Please enter n: ");    
    scanf("%d", &input);
    answer = sum(input);
    printf("The sum of the numbers from 1 through %d equals %d.", input, answer);
    return(0);
}

/* Please write your function here */
