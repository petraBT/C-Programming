#define MAX 200
#define WORDLEN 50
#include <stdio.h>

// prototypes here

int main(void) {
    FILE *ifile;
    char text[MAX][WORDLEN];
    int i,N;
   
    i=0;
    ifile = fopen("reverseText.txt", "r");
    while((i<MAX) && (fscanf(ifile, "%s", text[i])!=EOF)) {
        i++;
    }
    N=i;
    printText(text, N);
    printf("\n\n");
    printReverseText(text, N);
    return 0;
}

// function definitions here
