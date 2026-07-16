#include <stdlib.h>
int main(void){
    int * intptr;
    double * doubleptr;
    intptr = (int *) malloc(sizeof(int));
    * intptr = 5;
    doubleptr = (double *) malloc(sizeof(double));
    * doubleptr = 9.0;
    // Need to still learn how to release (free) the reserved memory.
    return 0;
}