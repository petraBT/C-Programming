#include <stdio.h>
#include <stdlib.h>

struct digit     /* structure to hold digits in linked list */
{
	int num;
	struct digit *next;
};

typedef struct digit digit_t;

digit_t *readNumber(void);                   /* prototypes */
void displayNumber(digit_t *number);
void destroyNumber(digit_t *number);
void statistics (digit_t *number);
     
int main(void)
{
	digit_t *number;
	
	printf("Please enter an integer of any length: ");
	number = readNumber();
	if (number != NULL) {
		printf("Thank you!\n");
    	printf("You entered the following number: \n");
		displayNumber(number);
		statistics(number);
		destroyNumber(number);
	}
	else printf("You didn't enter anything.\n");
	
    return(0);
}


/*Function to create linked list of digits of number*/

digit_t *readNumber(void)
{
    char c = '\n';  /* character read from user input */
    int d;          /* digit corresponding to the character */  
    digit_t *start, *end, *new; /* pointers to keep track of */
					            /* start, end, current digit */

    start = NULL;     /* no list yet */
    scanf("%c", &c);  /* read first digit as a character */

    while (c != '\n') {
		d = c-48;   /* make character into corresp. number */

        new = (digit_t *)malloc(sizeof(digit_t));
		new->num = d;      /* create digit, store number */
		new->next = NULL;  /* nothing follows the digit yet */
        
        if (start == NULL) {  /* new digit is start of number */
			start = new;
			end = start;            
		}
        else {                /* new digit added on to number */
			end->next = new;
			end = end->next;
        }
	  scanf("%c", &c);    /* read next digit from user input */
    }
    return(start);        /* return pointer to start of number */
}

/*Function to display the number*/

void displayNumber (digit_t *number)
{
	/* Please enter your code here. */

    printf("\n");
}
   

/*Function to free the number (all of its digits)*/

void destroyNumber (digit_t *number)
{
	/* Please enter your code here. */
}

/* Function to print statistics about the number */

void statistics (digit_t *number)
{
	/* Please enter your code here. */
}
