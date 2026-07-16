#include <stdio.h>
int findFirstAndSecond(int N, int array[], int *first, int *second);

int main(void) {
   int numbers[] = {4, 6, 2, 8, 6, -4, 6, 0, 6, 3, 1, 100, 2};
   int n = 13;
   int first, second, same;
   
   same = findFirstAndSecond(n, numbers, &first, &second);
   
   if (same) {
       printf("All elements of the array have the value %d.\n", first);
   } else {
       printf("The largest number in the array is %d and the ", first);
       printf("second largest number is %d.\n", second);
   }
   return 0;
} 

/* Write your function findFirstAndSecond() here. */