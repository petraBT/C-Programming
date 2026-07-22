#include <stdio.h>

int main(void) {
    int num;
    
    printf("Enter a positive number: ");
    scanf("%d", &num);
    while (num < 0) {
       printf("Negative number, try again: ");
       scanf("%d", &num);
    }   
    
    printf("You entered %d.\n", num);
    return(0);
}
