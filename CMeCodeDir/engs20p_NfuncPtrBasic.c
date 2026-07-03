#include <stdio.h>
/* Prototypes */
void printNumber(int);

/* Main function*/
int main(void) {
    int my_number = 5;
    //int *numberptr = &my_number;
    void (*functionptr)(int) = &printNumber; //explicit address of the function
    (*functionptr)(my_number);

    void (*functionptr2)(int); 
    functionptr2 = printNumber; //implicit conversion
    functionptr2(10);

    //printNumber(my_number);
    
    return(0);
}

void printNumber (int number){
    printf("My number is %d.\n", number);
}
