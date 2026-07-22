#include <stdio.h>

/* prototypes here */

int main(void) {
    
    int usertemp;
    char unit;
    float convertedtemp;
    
    printf("Please enter a temperature: ");
    scanf("%d %c", &usertemp, &unit);
    
    /* complete the code */
    
    if (unit=='C'){
        printf("%d degrees Celsius corresponds to approximately %.1f degrees Fahrenheit.\n", usertemp, convertedtemp);
    }else if (unit=='F'){
        printf("%d degrees Fahrenheit corresponds to approximately %.1f degrees Celsius.\n", usertemp, convertedtemp);
    }
    
    return(0);
}

/* functions here */
