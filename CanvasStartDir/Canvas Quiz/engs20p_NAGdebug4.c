#include <stdio.h>

int main(void) {
	int i, n, sum;

	printf("Please enter a positive integer: ");
	scanf("%d", &n);
    sum = 0;

	for(i=1; i<=n; i++);
          sum += i;
          
    printf("The sum from 1 to %d equals %d.", n, sum);
   
    return(0);
}