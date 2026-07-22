#include <stdio.h>

int main(void) {
    int a = 10;
    int b = 3;
    int c;
    int okay = 1;
    
    char op = '+';
    
    switch(op) {
        case '+': 
            c = a+b;
        case '-':
            c = a-b;
        case '*':
            c = a*b;
        case '%':
            c = a%b;
        case '/':
            c = a/b;
        default:
            printf("Unknown operator.\n");
            okay = 0;
            c = 0;
    }
    
    if (okay) printf("\n%d %c %d = %d\n", a, op, b, c);
    return(0);
}
