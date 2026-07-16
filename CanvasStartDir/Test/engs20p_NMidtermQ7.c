#include <stdio.h>
#include <stdlib.h>

struct digit {
    int num;
    struct digit *next;
};

typedef struct digit digit_t;

digit_t * createDigit(int);
digit_t * append(digit_t * end, digit_t * newDigptr);
void printNumber(digit_t *);
digit_t * readNumber(void); 
void makeCircular(digit_t * start);
void printCircular(digit_t *start);
digit_t * deleteDigit(digit_t *start, int n);
int countOff(digit_t *start, int n);

int main(void) {
    digit_t *start;
    int winner;
    printf("Please enter a number: ");
    start = readNumber();
    printf("You entered: ");
    printNumber(start);
    makeCircular(start);
    printCircular(start);
    winner = countOff(start, 3);
    printf("\nThe winner is %d.\n", winner);
    return 0;
}

digit_t *createDigit(int dig) {
    digit_t *ptr;
    ptr = (digit_t *) malloc(sizeof(digit_t));
    ptr->num = dig;
    ptr->next = NULL;
    return ptr;
}

digit_t * append(digit_t * end, digit_t * newDigptr) {
    end->next = newDigptr;
    return(end->next);
}

void printNumber(digit_t *start) {
    digit_t * ptr = start;
    while (ptr!=NULL) {
        printf("%d", ptr->num);
        ptr = ptr->next;
    }
    printf("\n");
}

void printCircular(digit_t *start) {
    digit_t *ptr = start;
    do {
        printf("%d", ptr->num);
        ptr = ptr->next;
    } while (ptr!=start);
    printf("\n");
}

digit_t * readNumber(void) {
    char c;
    int d;
    digit_t *start, *end, *newptr;
    start = NULL;
    scanf("%c", &c);
    while (c != '\n') {
        d = c-48;
        newptr = createDigit(d);
        if (start == NULL) {
            start = newptr;
            end = start;
        } else {
            end = append(end, newptr);
        }
        scanf("%c", &c);
    }
    return(start);
}

void makeCircular(digit_t * start) {
/* your code goes here */
    
}

digit_t * deleteDigit(digit_t *start, int n) {
/* your code goes here */

}

int countOff(digit_t *start, int n) {
/* your code goes here */

}