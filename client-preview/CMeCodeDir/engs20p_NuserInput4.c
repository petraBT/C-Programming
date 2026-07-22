#include <stdio.h>

int main(void)
{
    int i; /* loop counter */
    int total; /* holds the sum */
    int num; /* individual numbers entered by the user */
    int count; /* hold number of numbers the user wishes to add */

    printf("How many numbers do you wish to add: ");
    scanf("%d", &count);

    /* Write your code here. */
    
    printf("The numbers you entered add up to %d.", total);
    return(0);
}
