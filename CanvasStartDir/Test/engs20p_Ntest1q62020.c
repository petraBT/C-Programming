/******************************************************************************
Please do not modify this section, except to put in your magic number.
Replace the sample number on the line below with your magic number. 
1234
Replace the sample number on the line above with your magic number. 
*******************************************************************************/

#include <stdio.h>

// add your prototype(s) here

int main(void) {
	float x;
	int n;
	printf("Please enter an x-value: ");
	scanf("%f", &x);
	printf("Please enter an approximation level: ");
	scanf("%d", &n);
	printf("sin(%.4f) = %.4f\n", x, sine(x, n));
	return(0);
}

// add your function definition(s) here