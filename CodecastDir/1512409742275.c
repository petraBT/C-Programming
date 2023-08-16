#include <stdio.h>
int main(void)
{
    // false: 0
    // true: 1 (or anything non-zero)
    // if true, do this, otherwise do that
    
    int sunny = 0;
    
    if (sunny) {
        printf("It is sunny!\n");
        printf("Time to go outside!\n");
    } else {
        printf("It's not sunny :-( \n");
        printf("I need to stay inside. \n");
    }
    
    return(0);
}