#include <stdio.h>
int main(void) {
    float array[3];
    int i;
    for (i=0; i<3; i++) {
        printf("Enter a decimal: ");
        scanf("%f", &array[i]);
        printf("I put %f at index %d of the array.\n", array[i], i);
    }
    return 0;
}