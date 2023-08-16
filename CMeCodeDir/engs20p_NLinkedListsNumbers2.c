#include <stdio.h>
#include <stdlib.h>

struct digit {
    int num;
    struct digit *next;
};

typedef struct digit digit_t;

digit_t *createDigit(int);
void append(digit_t * start, digit_t * newDigptr);

int main(void) {
    digit_t *start, *newDigptr, *end;
    start = createDigit(5);
    newDigptr = createDigit(3);
    append(start, newDigptr);
    newDigptr = createDigit(7);
    append(start, newDigptr);

/* print the number */

/* free all allocted space */

    return 0;
}

digit_t *createDigit(int dig) {
    digit_t *ptr;
    ptr = (digit_t *) malloc(sizeof(digit_t));
    ptr->num = dig;
    ptr->next = NULL;
    return(ptr);
}

void append(digit_t * end, digit_t * newDigptr) {


}
