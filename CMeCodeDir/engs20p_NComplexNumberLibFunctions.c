/*
 * Complex Number Library: complexlib.c
 *  
 *  Created by ENGS20!
 *
 *  compile to an object file using
 *  gcc -c -o complexlib.o complexlib.c
 */
 
#include "complexlib.h"
#include <stdio.h>
#include <math.h>

#define E 2.71828

/* Create a complex number from real and imaginary parts */
complex_t complex(float x, float y)
{

}

/* Create a complex number from polar coordinates */
complex_t polar(float R, float phi)
{
    
}

/* Extract the real part of a complex number */
float real(complex_t z)
{

}

/* Extract the imaginary part of a complex number */
float imaginary(complex_t z)
{
    
}

/* Finds the complex conjugate */
complex_t c_conjugate(complex_t z)
{

}

/* add two complex numbers */
complex_t add_c(complex_t z1, complex_t z2)
{

}

/* Subtract complex numbers */
complex_t subtract_c(complex_t z1, complex_t z2)
{

}

/* Multiply complex numbers */
complex_t multiply_c(complex_t z1, complex_t z2)
{

}

/* Divide complex numbers */
complex_t divide_c(complex_t z1, complex_t z2)
{

}

/* Complex exponential function, using e^(x+iy) = e^x(cos y + i sin y) */
complex_t exp_c(complex_t z)
{

}
    
/* Complex logarithm: log(z) = ln(|z|) + i arg(z) */   
complex_t log_c(complex_t z)
{

}

/* complex square root: take square root of length and half the angle */
complex_t sqrt_c(complex_t z)
{

}

/* Complex absolute value: |z| = (x*x + y*y)^(1/2) */
float abs_c(complex_t z)
{

}

/* argument of a complex number */
float phase_c(complex_t z)
{

}

/* display a complex number to the console */
void display_c(complex_t z)
{

}
