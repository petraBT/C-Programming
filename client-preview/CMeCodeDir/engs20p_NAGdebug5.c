#include <stdio.h>

int main(void) {
   int i, n;
   int sum = -1;

   printf("Please enter a positive integer: ");
   scanf("%d", &n);
   printf("You entered %d.\n", n);

   for(i=1; i<=n; i++)
          sum += i;
          
    printf("The sum from 1 to %d equals %d.", n, sum);
    
    return(0);
}
