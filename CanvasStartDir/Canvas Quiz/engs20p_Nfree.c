#include <stdio.h>
#include <stdlib.h>
int main(void) {
    int * a, *b, *c;
    a = (int *) malloc(sizeof(int));
    *a = 1;
    printf("I stored %d at memory location %p.\n", *a, a);
    b = (int *) malloc(sizeof(int));
    *b = 2;
    printf("I stored %d at memory location %p.\n", *b, b);
    free(a);
    c = (int *) malloc(sizeof(int));
    *c = 3;
    printf("I stored %d at memory location %p.\n", *c, c);
    printf("Can I still access a?\n");
    printf("I stored %d at memory location %p.\n", *b, b);
    free(b);
    free(c);
    return 0;
}