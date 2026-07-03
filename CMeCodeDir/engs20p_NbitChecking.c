#include <stdio.h>

int main(void){
	unsigned int num;
	int bit;

	printf("Please enter a positive integer and the bit you would like to check: (0 is the right most bit) ");
	scanf("%d %d", &num, &bit);

	checkBit(num,bit);

	//Print out the result here

	return 0;
}

//Write your function here
