#include <stdio.h>

int main(void) {
    
    int age = 5;
    
    if (age<1)
        printf("Infant\n");
    else if (age<3)
        printf("Toddler\n");
    else if (age<13)
        printf("Child\n");
    else if (age<18)
        printf("Teen\n");
    else
        printf("Adult\n");
    
    return(0);
}
