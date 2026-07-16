#include <stdio.h>
#include <stdlib.h>

struct digit {
    int num;
    struct digit *next;
};

typedef struct digit digit_t;

digit_t *createDigit(int);
void append(digit_t * start, digit_t * newDigptr);
void printNumber(digit_t *start);
void freeNumber(digit_t *start);
digit_t *readNumber(void);
digit_t *searchNumber(digit_t *start, int number);
digit_t * insertAtFront(digit_t * start, digit_t * newptr);
digit_t * reverseNumber(digit_t * start);

int main(void) {
    digit_t *start, *backwards;
    printf("Please enter a number: ");
    start = readNumber();
    printf("You entered: ");
    printNumber(start);
    printf("Backwards: ");
    backwards = reverseNumber(start);
    printNumber(backwards);
    freeNumber(start);
    freeNumber(backwards);
    return 0;
}

digit_t *createDigit(int dig) {
    digit_t *ptr;
    ptr = (digit_t *) malloc(sizeof(digit_t));
    ptr->num = dig;
    ptr->next = NULL;
    return(ptr);
}

void append(digit_t * start, digit_t * newDigptr) {
    digit_t *end = start;
    while(end->next != NULL) {
        end = end->next;
    }
    end->next = newDigptr;
}

void printNumber(digit_t *start) {
    digit_t * ptr = start;
    while (ptr!=NULL) {
        printf("%d", ptr->num);
        ptr = ptr->next;
    }
    printf("\n");
}

void freeNumber(digit_t *start) {
    struct digit * ptr = start;
    struct digit * tmp;
    while (ptr!=NULL) {
        tmp = ptr->next;
        free(ptr);
        ptr = tmp;
    }
}

digit_t *readNumber(void) {
    char c;
    int d;
    struct digit *start, *newptr;
    start = NULL;
    scanf("%c", &c);
    while (c != '\n') {
        d = c-48;
        newptr = createDigit(d);
        if (start == NULL) {
            start = newptr;
        } else {
            append(start, newptr);
        }
        scanf("%c", &c);
    }
    return(start);
}

digit_t * searchNumber(digit_t * start, int number) {
    digit_t * ptr = start;
    while ((ptr!=NULL) && (ptr->num!=number)) {
        ptr = ptr->next;
    }
    return(ptr);
}

digit_t * insertAtFront(digit_t * start, digit_t * newptr) {
    newptr->next = start;
    return(newptr);
}

digit_t * reverseNumber(digit_t * start) {
    digit_t *ptr = start;
    digit_t *bstart = start;
    digit_t *newdigit;
    
    if (start!=NULL) {
        bstart = createDigit(start->num);
        ptr = ptr->next;
    }
    while (ptr != NULL) {
        newdigit = createDigit(ptr->num);
        bstart = insertAtFront(bstart, newdigit);
        ptr = ptr->next;
    }
    return(bstart);
}