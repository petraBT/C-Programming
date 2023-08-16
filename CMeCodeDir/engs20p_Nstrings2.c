#include <stdio.h>
#include <string.h>

int main(void) {
   char firstName[30];
   char lastName[] = "Bonfert-Taylor";
   
   strcpy(firstName, "Petra");
   printf("My name is %s %s.\n", firstName, lastName);
   return 0;
}
