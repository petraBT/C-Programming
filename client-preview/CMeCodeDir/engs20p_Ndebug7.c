#include <stdio.h>

int main (void)
{
   int i;
   int total = 0;
    
   for (i=0; i<=100; i--) {
          total +=i;
   }
   printf("The sum of the numbers from 0 to 100 equals %d.\n", total);

   return (0);
}
