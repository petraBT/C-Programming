#include <stdio.h>
//prototypes
void printBinary(unsigned number);
     
int main (void){
    unsigned number, number_neg, number_shift;
    
    printf("Please enter a positive integer: ");
    scanf("%d", &number);
    printf("The number you entered is: %d\n", number);
    printBinary(number);
    //bitwise negation: ~
    printf("Bitwise negation of number:\n");
    number_neg = ~number;
    printBinary(number_neg);
    //left shift: <<
    printf("Shifting to the left:\n");
    number_shift = number << 4;
    printBinary(number_shift);
    //right shift: >>
    printf("Shifting to the right\n");
    printBinary(number_neg >> 3);
    
    return 0;
}
void printBinary(unsigned number){
    int i;
    int array[sizeof(unsigned)*8];
    for(i=0; i<sizeof(unsigned)*8; i++){
        array[i] = number%2;
        number = number/2;
    }
    for(i=sizeof(unsigned)*8-1; i>=0; i--){
        printf("%d", array[i]);
        if(i%8 == 0){
            printf(" ");
        }
    }
    printf("\n");
}