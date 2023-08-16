#include <stdio.h>

int main(void) 
{
    char letter;
    
    printf("Please enter your favorite letter: ");
    scanf("%c", &letter);
    printf("You entered %c.\n", letter);
    
    return(0);
}
