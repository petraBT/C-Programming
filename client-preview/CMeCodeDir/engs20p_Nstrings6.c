#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(void) {
   char firstName[50];
   char lastName[50];
   char name[200];
   
   printf("Please enter your first and last name: ");
   scanf("%s %s", firstName, lastName);
   sprintf(name, ":-) %s The Chocolate Eater %s!", firstName, lastName);
   printf("Your name is %s.", name);
   return 0;
}
