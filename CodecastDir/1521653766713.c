#include <stdio.h>
int main(void) {
    int array[3];
    int i;
    for (i=0; i<3; i++) {
        printf("Enter an integer: ");
        scanf("%d", &array[i]);
        printf("I put %d at index %d of the array.\n", array[i], i);
    }
    return 0;
}