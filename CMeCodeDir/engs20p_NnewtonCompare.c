#include <stdio.h>
#include <math.h>
#include "newton.h"

void myfunction(double x, double *f, double *df);

int main(void){
	double root;

	double x0 = 10.0;
	if (newton(myfunction, x0, &root)) {
		printf("Newton converged: root = %.15e\n", root);
	} else {
		printf("Newton failed\n");
		return 1;
	}

	return 0;
}

/* User-defined function for Newton's method (need derivative)*/
void myfunction(double x, double *f, double *df){
	/* Case 1: f = x^3 - 8  =>  solution = 8^(1/3) = 2 */
	*f  = x * x * x - 8.0;
	*df = 3.0 * x * x;

	/* Case 2: f = exp(x) - 10  =>  solution = log(10) */
	/* *f  = exp(x) - 10.0; */
	/* *df = exp(x);        */
}

