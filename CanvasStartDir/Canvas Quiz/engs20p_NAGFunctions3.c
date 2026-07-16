#include <stdio.h>

/* insert prototype here */


/* Do not change anything below this point  */

int main(void) {
  float x;
  float result;

  printf("Please enter a number to be squared: ");
  scanf("%f", &x);
  result = square(x);
  printf("The square of %.2f is %.2f.", x, result);

  return(0);
}

float square(float x) {
  return(x*x);
}