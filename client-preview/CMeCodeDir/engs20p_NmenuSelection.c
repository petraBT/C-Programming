#include <stdio.h>

int main(void) {
   char again, ch, jnk;

/* First attempt */
   again = 'y';
   do {
      printf("S[o]rt list\n");
      printf("Sea[r]ch list\n");
      printf("Sa[v]e list\n\n");

      printf("Enter choice (o,r,v) : ");
      scanf("%c", &ch);

      printf("You selected option %c\n", ch);

      printf("Again? Press 'n' to quit, 'y' to continue:");
      scanf("%c", &again);
   } while (again != 'n');

/* Second attempt */
/*   again = 'y';
   do {
     printf("S[o]rt list\n");
     printf("Sea[r]ch list\n");
     printf("Sa[v]e list\n\n");

     printf("Enter choice (o,r,v) [v]: ");
     scanf("%c%c", &ch, &jnk);

     printf("You selected option %c\n", ch);

     printf("Again? Press 'n' to quit, 'y' to continue [y]:");
     scanf("%c%c", &again, &jnk);
   } while (again != 'n');
*/
/* Third attempt */
/*   again = 'y';
   do {
     printf("S[o]rt list\n");
     printf("Sea[r]ch list\n");
     printf("Sa[v]e list\n\n");

     printf("Enter choice (o,r,v) [v]: ");
     scanf("%c", &ch);
     if (ch == '\n') ch = 'v';
     else scanf("%c", &jnk);

     printf("You selected option %c\n", ch);

     printf("Again? Press 'n' to quit, 'y' to continue [y]:");
     scanf("%c", &again);
     if (again == '\n') ch = 'y';
     else scanf("%c", &jnk);
   } while (again != 'n');
*/
   return(0);
}
