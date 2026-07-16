#include <stdio.h>
int main(void)
{
    int sunnyEnough;
    int threshhold = 6;
    int howSunny;
    
    printf("On a scale of 1-10, how sunny is it today? ");
    scanf("%d", &howSunny);
    printf("You entered %d.\n", howSunny);
    
    sunnyEnough = (howSunny>threshhold);
    
    if (sunnyEnough) {
        printf("It is really sunny!\n");
        printf("Time to go outside!\n");
    }
    else {
        printf("It\'s not sunny enough :-(\n");
        printf("I need to stay inside.\n");
    }
    
    return 0;
}