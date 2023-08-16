#include <stdio.h>
#include <string.h>

int main(void) {
   char name1[] = "Petra"; 
   char name2[] = "Karin";
   /* try other words such as fool and foolish, thrill and thrifty, lastname and Lastname, etc. */
   int val;
   
   val = strcmp(name1, name2);
   printf("Comparing %s to %s yields val = %d.\n", name1, name2, val);

    if (val<0) {
        printf("%s comes before %s in the alphabet.\n", name1, name2);
    } else if (val>0) {
        printf("%s comes after %s in the alphabet.\n", name1, name2);
    } else if (val==0) {
        printf("%s and %s are equal.\n", name1, name2);
    }
   return 0;
}
