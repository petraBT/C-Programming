#include <stdio.h>

int main(void) {
    int cash;
    
    cash = 20;
    printf("I have %d dollars in my wallet.\n", cash);

    /* I just spent 3 dollars. */
    cash = cash - 3;
    printf("Now I have %d dollars left.\n", cash);

    /* I just spent 5 dollars. */    
    cash = cash - 5;
    printf("Now I have %d dollars left.\n", cash);
    
    /* I just earned 15 dollars. */
    cash = cash + 15;
    printf("Now I have %d dollars left.\n", cash);
   
    return(0);
}