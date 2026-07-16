#include <stdio.h>

int main(void) {
    int cash = 30;
    
    printf("I have %d dollars in my wallet.\n", cash);
    /* I just spent 3 dollars. */
    cash = cash - 3;
    printf("Now I have %d dollars left.\n", cash);
    
    return(0);
}