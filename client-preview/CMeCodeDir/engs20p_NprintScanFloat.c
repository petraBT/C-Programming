#include <stdio.h>

int main(void) 
{
    float height;
    
    printf("How tall are you? Enter your height in meters: ");
    scanf("%f", &height);
    printf("You are %f meters tall.\n", height);
    printf("You are %.1f meters tall.\n", height);

    return(0);
}
