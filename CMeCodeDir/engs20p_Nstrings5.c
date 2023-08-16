#include <stdio.h>
#include <string.h>

int main(void) {
   char firstName[50];
   char lastName[50];
   
   printf("Please enter your first and last name: ");
   scanf("%s %s", firstName, lastName);
   printf("Your name is %s %s.", firstName, lastName);
   return 0;
}
