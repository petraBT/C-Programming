#include <stdio.h>

int main(void) 
{
    int aint, bint, cint;
    float afloat, bfloat, cfloat;
    
    aint = 5;
    bint = 3;
    
    cint = aint/bint;
    printf("%d / %d = %d.\n", aint, bint, cint);
    
    cfloat = aint/bint;
    printf("%d / %d = %f.\n", aint, bint, cfloat);
    
    afloat = (float) aint;
    bfloat = (float) bint;
    cfloat = afloat/bfloat;
    printf("%f / %f = %f.\n", afloat, bfloat, cfloat);

    return(0);
}
