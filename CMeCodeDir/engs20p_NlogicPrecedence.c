#include <stdio.h>
int main(void) {
    int a, b, c, d;
    a = 5;
    b = 5;
    c = 5;
    d = 5;
    
    if (a == b == c == d)
        printf("True!\n");
    else
        printf("Huh??? False???\n");
        
    return(0);
}
