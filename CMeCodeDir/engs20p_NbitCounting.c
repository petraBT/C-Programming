#include <stdio.h>

int main(void){
	unsigned int number;
	int numbits;

	printf("Please enter a positive integer: " );
	scanf("%d", &number);

	numbits = countBits(number);

	//Print out the result here

	return 0;
}

//Write your function here
