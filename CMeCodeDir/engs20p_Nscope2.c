#include <stdio.h>
void doSomething(int);
int main(void){
    int a = 10;
    int b = 11;
    
    doSomething(b);
    printf("In main: a = %d, b = %d\n", a, b);
    return 0;
}

void doSomething(int a) {
    int b = 21;
    printf("In function: a = %d, b = %d\n", a, b);
}
