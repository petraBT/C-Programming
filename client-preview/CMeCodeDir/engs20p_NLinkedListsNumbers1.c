#include <stdio.h>
#include <stdlib.h>

struct digit {
    int num;
    struct digit *next;
};

typedef struct digit digit_t;

digit_t *createDigit(int);

int main(void) {
    digit_t *numberptr;
    numberptr = createDigit(5);
    printf("We are storing the digit %d.\n", numberptr->num);
    free(numberptr);
    return 0;
}

digit_t *createDigit(int dig) {


}
