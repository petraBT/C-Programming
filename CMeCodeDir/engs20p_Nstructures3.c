#define STRLEN 50
#include <stdio.h>

typedef struct {
   char firstName[STRLEN];
   char lastName[STRLEN];
   int birthYear;
   double aveGrade;
} student_t;

int main(void) {
   student_t me={"Petra", "Bonfert-Taylor", 1989, 3.5};
   student_t you={"Karin", "Berger", 2005, 3.5};
   
   printf("Name: %s %s\n", me.firstName, me.lastName);
   printf("Year of birth: %d\n",me.birthYear);
   printf("Average grade: %.2lf\n",me.aveGrade);
   printf("\n");
   printf("Name: %s %s\n", you.firstName, you.lastName);
   printf("Year of birth: %d\n",you.birthYear);
   printf("Average grade: %.2lf\n",you.aveGrade);
   
   return 0;
}
