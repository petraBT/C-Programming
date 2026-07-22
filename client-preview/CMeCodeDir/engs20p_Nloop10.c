#include <stdio.h>

int main(void) {
    int num;
    
    printf("Enter a positive number: ");
    do {
       scanf("%d", &num);
       if (num < 0)
          printf("Negative number, try again: ");
    } while (num < 0);
   
    printf("You entered %d.\n", num);
    return(0);
}
