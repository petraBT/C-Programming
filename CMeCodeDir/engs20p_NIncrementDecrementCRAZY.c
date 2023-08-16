#include <stdio.h>

int main(void)
{
   int i;
   
   i  = 10;   
   printf("i = %d, ", i);
   printf("%d, ", i++);
   printf("%d\n\n", ++i);

/*
   i = 10;   
   printf("i = %d, %d, %d\n\n", i, i++, ++i);
*/   
   
   return(0);
}
