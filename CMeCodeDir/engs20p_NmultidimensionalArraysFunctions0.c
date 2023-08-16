#define NROWS 3
#define NCOLS 4
#include <stdio.h>
void zeroArray(int array[][NCOLS]);
void printArray(int array[][NCOLS]);
int main(void) {
    int matrix[NROWS][NCOLS];
    int i,j;
   
    printArray(matrix);
    zeroArray(matrix);
    printf("\n");
    printArray(matrix);
    return 0;
}

void zeroArray(int array[][NCOLS]) {
    int i,j;
    for (i=0; i<NROWS; i++) {
        for (j=0; j<NCOLS; j++) {
            array[i][j]=0;
        }
    }
}

void printArray(int array[][NCOLS]) {
    int i,j;
    for (i=0; i<NROWS; i++) {
        for (j=0; j<NCOLS; j++) {
            printf("%d ", array[i][j]);
        }
        printf("\n");
    }
}
