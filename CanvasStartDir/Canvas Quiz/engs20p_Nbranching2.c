#include <stdio.h>
int main(void)
{
    int sunny = 1;
    
    if (sunny) {
        printf("It is sunny!\n");
        printf("Time to go outside!\n");
    }
    else {
        printf("It\'s not sunny :-(\n");
        printf("I need to stay inside.\n");
    }
    
    return 0;
}