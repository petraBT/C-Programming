#include <stdio.h>

int main(void) {
    int myNumber = 3;
    int yourNumber = 5;
    
    if (myNumber>yourNumber)
        printf("I win!\n");
    else if (myNumber<yourNumber)
        printf("You win!\n");
    else
        printf("It's a tie.\n");
    
    return(0);
}