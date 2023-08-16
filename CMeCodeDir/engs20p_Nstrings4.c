#include <stdio.h>
#include <string.h>

int main(void) {
   char firstName[50];
   char lastName[] = "Bonfert-Taylor";
   int len;
   
   strcpy(firstName, "Petra The Chocolate Eater");
   len = strlen(firstName);
   printf("%s has %d letters, and %s has %d letters.\n", firstName, len, lastName, (int) strlen(lastName));
   return 0;
}
