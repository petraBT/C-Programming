#include <stdio.h>

typedef struct {
            char name[30];
            long id;
            int class;
} student_t;

int main(void)
{
    student_t me = {"Petra", 123456L, 1994};
    
    /* Complete the code in each of the three
       lines below so that the student's record 
       is printed to the screen. */
   

    printf("Student %s ",);
    printf("with id %ld ",   );
    printf("belongs to the class of %d.",   );
    
    return(0);

}