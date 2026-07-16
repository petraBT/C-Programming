#include <stdio.h>

int main(void)
{
    int i;
    
    printf("+");
	for (i = 0; i < 31; i++)
		printf("-");
	printf("+");

	for (i = 0; i < 4; i++) 
		printf("| o | X | o | X | o | X | o | X |");
		printf("\n");
		printf("| X | o | X | o | X | o |");
		printf("\n");
	
	printf("+");
	for (i = 0; i < 31; i++)
		printf("-");
	printf("+");
	
    return(0);
}