#include <stdio.h>
void function1(int a);
void function2(int b[]);

int main(void) {
    int i = 3;
    int array[] = {5, 6};
    
    printf("Before function calls:\n");
    printf("i = %d, array[0] = %d, array[1] = %d\n", i, array[0], array[1]);
    
    printf("After function calls:\n");
    printf("i = %d, array[0] = %d, array[1] = %d\n", i, array[0], array[1]);
    
    return 0;
}

void function1(int a) {
    printf("Inside function1: \n");
    printf("a = %d.\n", a);
    a = -7;
    printf("Inside function1, after change: \n");
    printf("a = %d.\n", a);
}

void function2(int b[]) {
    printf("Inside function2: \n");
    printf("b[0] = %d, b[1] = %d.\n", b[0], b[1]);
    b[0] = -12;
    printf("Inside function2, after change: \n");
    printf("b[0] = %d, b[1] = %d.\n", b[0], b[1]);
}
