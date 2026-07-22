#include <stdio.h>

int main(void){
	unsigned int num;

	printf("Please enter a positive integer: ");
	scanf("%d", &num);

	printf("Decimal numnber: %d \n", num);

	printf("binary number: ");
	printBinary(num);
	printf("\n");

	return 0;
}

//Write your function here
