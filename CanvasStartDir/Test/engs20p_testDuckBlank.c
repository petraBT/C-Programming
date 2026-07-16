#include <stdio.h>
#include <string.h>

#define ROWS 4
#define COLS 7

void findBounds(char game[ROWS][COLS], int *colmin, int *colmax);

int main(void) {
   char game[ROWS][COLS] = {" ----- ", 
                            "|  XX |", 
                            "| XX  |", 
                            " ----- "};
   int first, last;

   findBounds(game, &first, &last);
   printf("First game column to contain a non-space character: %d\n", first);
   printf("Last game column to contain a non-space character: %d\n", last);
   return 0;
}