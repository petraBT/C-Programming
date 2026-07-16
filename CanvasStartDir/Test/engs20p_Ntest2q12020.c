/******************************************************************************
Please do not modify this section, except to put in your magic number.
Replace the sample number on the line below with your magic number. 
1234
Replace the sample number on the line above with your magic number. 
*******************************************************************************/

#include <stdio.h>
#include <stdlib.h>

struct digit {
    int num;
    struct digit *next;
};

typedef struct digit digit_t;

digit_t * createDigit(int dig);
void printNumber(digit_t *start);
void freeNumber(digit_t *start);
digit_t * readNumber(void);

// add your prototypes here

/* Please do not modify this main function. */
int main(void) {
    digit_t *num1, *num2, *sum;
    int num;
    printf("Please enter first number: ");
    num1 = readNumber();
    printf("Please enter second number: ");
    num2 = readNumber();
    sum = add(num1,num2);
    printNumber(num1);
    printf(" + ");
    printNumber(num2);
    printf(" = ");
    printNumber(sum);
    printf("\n");
        
    freeNumber(num1);
    freeNumber(num2);
    freeNumber(sum); 
    return 0;
}

/* createDigit() reserves space in memory for one digit, copies the number
   passed in into this space and returns a pointer to the object. */ 
digit_t *createDigit(int dig) {
    struct digit *ptr;
    ptr = (struct digit *) malloc(sizeof(struct digit));
    ptr->num = dig;
    ptr->next = NULL;
    return ptr;
}

/* printNumber() prints the number stored in the linked list of digits,
   most sigificant digit first, least significant digit last, 
   using recursion. */
void printNumber(digit_t *start) {
	struct digit *ptr = start;
	if (start != NULL) {
		printNumber(start->next);
		printf("%d", start->num);
	}
}

/* freeNumber frees the space allocated for each digit of a linked list
   of digits. */
void freeNumber(digit_t *start) {
    digit_t * ptr = start;
    digit_t * tmp;
    while (ptr!=NULL) {
        tmp = ptr->next;
        free(ptr);
        ptr = tmp;
    }
}

/* readNumber() reads an arbitrarily long integer from the user input and
   creates a linked list of digits from this input, with the head of the 
   list representing the least significant digit and the tail representing
   the most significant digit. */
digit_t *readNumber(void) {
    char c;
    int d;
    digit_t *start, *newptr;
    start = NULL;
    scanf("%c", &c);
    while (c != '\n') {
        d = c-48;
        newptr = createDigit(d);
        newptr->next = start;
        start = newptr;
        scanf("%c", &c);
    }
    return(start);
}