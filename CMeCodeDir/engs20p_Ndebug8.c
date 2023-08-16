#include <stdio.h>

int main (void)
{
    int total = 0;
    int i = 0;
     
    while (i<=100) {
        total +=i;
    }
    printf("The sum of the numbers from 0 to 100 equals %d.\n", total);

    return (0);
}
