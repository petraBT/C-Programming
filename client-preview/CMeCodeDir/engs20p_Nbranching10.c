#include <stdio.h>
int main(void) {
    int month = 8; /* month of the year*/
    
    if ( !((month>=6) && (month<=9)) ) {
        printf("It's not summer unfortunately.\n");
    } else {
        printf("Look's like summer to me!\n");
    }
    
    return(0);
}
