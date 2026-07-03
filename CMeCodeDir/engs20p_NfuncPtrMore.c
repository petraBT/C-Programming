#include <stdio.h>
int add(int, int);
int mult(int, int);

/* Main function*/
int main(void) {
    int a, b, result, op;
    int (*fptr)(int, int);
    a = 5;
    b = 4;
    printf("What operation? 1 for addition, 2 for multiplication ");
    scanf("%d",&op);
    if(op==1){
        fptr = &add;
    }
    else if(op==2){
        fptr = &mult;
    }
    result = (*fptr)(a,b);
    printf("Result of operation is %d\n", result);
    /*
    fptr = &add;
    result = (*fptr)(a,b);
    printf("Results of addition: %d\n", result);
    fptr = &mult;
    result = (*fptr)(a,b);
    printf("Results of multiplication: %d\n", result);
    */
    return(0);
}
int mult(int num1, int num2){
    return num1 * num2;
}
int add(int num1, int num2){
    return num1 + num2;
}
