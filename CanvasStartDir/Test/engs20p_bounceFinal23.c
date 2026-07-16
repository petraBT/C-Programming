#include <stdio.h>
#include <stdlib.h>

#define ROWS 10
#define COLS 40

void clearInputBuffer();
void display(char game[ROWS][COLS]);
void rightshift(char game[ROWS][COLS]);
void leftshift(char game[ROWS][COLS]);
void initialize(char game[ROWS][COLS]);
void moviemode(char game[ROWS][COLS]); 

void findBounds(char game[ROWS][COLS], int *colmin, int *colmax);

int main(void) {
   char game[ROWS][COLS];

   initialize(game);
   moviemode(game);
   
   return 0;
}

void initialize(char game[ROWS][COLS]) {
   int i,j;   
   for (i=0; i<ROWS; i++) {
       for (j=0; j<COLS; j++) {
           game[i][j] = ' ';
       }
   }
   
   for (i=1; i<ROWS-1; i++) {
       game[i][0] = game[i][COLS-1] = '|';
   }
   
   for (j=1; j<COLS-1; j++) {
       game[0][j] = game[ROWS-1][j] = '-';
   }
   
   strcpy(&game[3][4], "    __");
   strcpy(&game[4][4], "___( o)>");
   strcpy(&game[5][4], "\\ <_. )");
   strcpy(&game[6][4], " `---'");
   for (i=0; i<ROWS; i++) {
       for (j=0; j<COLS; j++) {
           if (game[i][j] == '\0')
                game[i][j] = ' ';
       }
   }
}

void moviemode(char game[ROWS][COLS]) {
    int i, j, colmin, colmax;
    char dummy;
    i = 0;
    display(game);
    do {
        findBounds(game, &colmin, &colmax);
        for (j = colmax+1; j<COLS-1; j++) {
            rightshift(game);
            display(game);
            hold();
        }
        findBounds(game, &colmin, &colmax);
        for (j = colmin-1; j>0; j--) {
            leftshift(game);
            display(game);
            hold();
        }
        i++;
    } while (i<3);
    printf("\nGood bye!");
} 

void hold() {
    long unsigned i;
    for (i=0; i<1000000; i++);
}

void findBounds(char game[ROWS][COLS], int *colmin, int *colmax) {
    *colmin = 0;
    *colmax = COLS-1;
}

void display(char game[ROWS][COLS]) {
    int i,j;
    
    system("clear");
    printf("\n\n");
    for (i=0; i<ROWS; i++) {
       printf("    ");
       for (j=0; j<COLS; j++) {
           printf("%c", game[i][j]);
       }
       printf("\n");
   }
    
}


void rightshift(char game[ROWS][COLS]) {
    int i,j;
    char store;
    
    for (i=1; i<ROWS-1; i++) {
        for (j=COLS-2; j>1; j--) {
            game[i][j] = game[i][j-1];
        } 
        game[i][1] = ' ';
    }
}

void leftshift(char game[ROWS][COLS]) {
    int i,j;
    
    for (i=1; i<ROWS-1; i++) {
        for (j=1; j<COLS-2; j++) {
            game[i][j] = game[i][j+1];
        } 
        game[i][COLS-2] = ' ';
    }
}

void clearInputBuffer() {
	char junk;
    
	do {
      scanf("%c", &junk);
	} while (junk != '\n');
}