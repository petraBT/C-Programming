#include <stdio.h>

int main (void)
{
   float sum;
   int i = 0;
    
   sum = 0.0;
   while (sum != 1.0) {
            sum = sum + 0.1;
            i++;
   }
   printf("At the end of the loop the value of i equals %d.\n", i);

   return (0);
}
