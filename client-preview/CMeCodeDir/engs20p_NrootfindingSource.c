#include <stdio.h>
#include <math.h>
#include "rootfinding.h"

void newton( void (* func) (double, double *, double *), double x0, double *root){
	int iter = 0;
	double fn, dfn, xn;
	double eps = 0.001;

	func(x0, &fn, &dfn);

	while(fn > eps || fn < -eps){
		xn = xn - fn/dfn;
		func(xn, &fn, &dfn);
		printf("iter %d: xn = %f and f(xn) = %f\n", iter, xn, fn);
		iter ++;
	}

	*root = xn;
}
