#include <stdio.h>

int main(void) {
    printf("Let\'s do some math!\n");
    printf("5+3 = %d, 5-3 = %d, 5*3 = %d.\n", 5+3, 5-3, 5*3);
    printf("(5+3)*(5-3) = %d, 5+3*5-3 = %d.\n", (5+3)*(5-3), 5+3*5-3);
    printf("(5+3)*(5-3)*2 = %d.\n", (5+3)*(5-3)*2);
    
    return(0);
}