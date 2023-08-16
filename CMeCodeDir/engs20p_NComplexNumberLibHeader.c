/*
 * complexlib.h
 *
 */

typedef struct {
    float real;
    float imag;
} complex_t;

complex_t complex(float x, float y);
complex_t polar(float R, float phi);
complex_t add_c(complex_t z1, complex_t z2);
complex_t subtract_c(complex_t z1, complex_t z2);
complex_t multiply_c(complex_t z1, complex_t z2);
complex_t divide_c(complex_t z1, complex_t z2);
complex_t c_conjugate(complex_t z);
complex_t exp_c(complex_t z);
complex_t log_c(complex_t z);
complex_t sqrt_c(complex_t z);

float abs_c(complex_t z);
float phase_c(complex_t z);
float real(complex_t z);
float imaginary(complex_t z);

void display_c(complex_t z);
