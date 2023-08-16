#include <stdio.h>
#define NROWS 2      /* number of rows */
#define NCOLS 3      /* number of columns */

/* Don't forget your prototype! */

int main(void) {
   /* Feel free to change the array, just be sure to update NROWS and NCOLS, if necessary. */ 
   int temperature[NROWS][NCOLS] = {12, 56, 88, 34, 8, -3};
   int maximum;
   
   /* Function call here. */
   
   printf("The maximal temperature is %d.", maximum);

    return(0);
}

int maxTemp(int array[][NCOLS]) 
{
   int max;
   
/* Your code here to find the maximum in array. */
/* Be sure to declare any needed additional variables. */

   return(max);
}
