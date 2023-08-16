#include <stdio.h>
int main(void) 
{
    int num1;
    int num2;
    int num3;
    
    printf("Please enter three numbers:");
    scanf("%d %d %d", &num1, &num2, &num3);
    printf("You entered the following: \n%d\n%d\n%d\n", num1, num2, num3);
    
    return(0);
}
