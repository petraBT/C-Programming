#include <stdio.h>
#include <math.h>
#include "rootfinding.h"

void poly(double x, double *f, double *df);

int main(void){
	double x0 = 10;
	double f, df, xf;

	poly(x0, &f, &df);
	printf("Initial values: x0 = %f, f(x0)= %f and f'(x0) = %f\n", x0, f, df);

	newton(poly, x0, &xf);
	poly(xf, &f, &df);
	printf("Final values: xf = %f and f(xf)= %f \n", xf, f);

	return 0;
}

void poly(double x, double *f, double *df){
	*f = x*x*x -9; //x^3 - 9
	*df = 3*x*x; //3x^2
}
