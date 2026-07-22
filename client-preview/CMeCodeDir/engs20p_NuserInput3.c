#include <stdio.h>
int main(void) 
{
    int i;
    int mult;
    
    printf("Which multiplication table would you like to print?\n");
    printf("Please enter a number: ");
    scanf("%d", &mult);
    printf("Here is the x%d multiplication table:\n", mult);
    
    for (i=1; i<=10; i++) {
        printf("%d x %d = %d\n", i, mult, i*mult);
    }
    
    return(0);
}
