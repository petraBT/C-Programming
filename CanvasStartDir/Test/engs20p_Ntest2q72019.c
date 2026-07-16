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
void freeNumber(digit_t *start);

int main(void) {
    digit_t *start;
    int a = 5;
    int b = 1;
    printf("Please enter a number: ");
    start = readNumber();
    printf("You entered: ");
    printNumber(start);
    
/* Uncomment the following lines as you develop the code */
//    printf("The sum of the digits of your number is %d.\n", sumOfDigits(start));
//    printf("Deleting all digits %d... The new number is ...\n", b);
//    start = deleteDigits(start, b);
//    printNumber(start);
    freeNumber(start);
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

void freeNumber(digit_t *start) {
    digit_t * ptr = start;
    digit_t * tmp;
    while (ptr!=NULL) {
        tmp = ptr->next;
        free(ptr);
        ptr = tmp;
    }
}