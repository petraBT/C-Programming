#include <stdio.h>
#include <string.h>

int main(void) {
   char firstName[10];
   char lastName[30];
   
   strcpy(firstName, "Petra The Chocolate Eater");
   strcpy(lastName, "Bonfert-Taylor");
   printf("My name is %s %s.\n", firstName, lastName);
   return 0;
}
