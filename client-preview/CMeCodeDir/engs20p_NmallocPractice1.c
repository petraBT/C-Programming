#include <stdio.h>
#include <stdlib.h>
   
/* prototypes here... */
   
int main (void) {   
   int *numbers;   
   int size;
   
   /* Have user enter size... */

   numbers = (int *) malloc(...);   
   userInput(size, numbers);
   printArray(size, numbers);

   free(numbers);
   return(0);   
}
