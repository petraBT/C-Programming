#include <stdio.h>
int main(void)
{
    // If it's true do something.
    // If it's not true, don't do it.
    // false: 0
    // true: anything not zero (1, 23, 99, ...)
    int sunny = 1;
    
    if (sunny) {
        printf("It is sunny outside.\n");
        printf("Time to go outside!\n");
    }
    return(0);
}