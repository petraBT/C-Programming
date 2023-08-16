#define NROWS 4
#define NCOLS 2
#include <stdio.h>
int main(void) {

    int matrix1[NROWS][NCOLS] = {{1,2}, {3,4}, {5,6}, {7,8} };
    int matrix2[NROWS][NCOLS] = { {1,2},
                                  {3,4},
                                  {5,6},
                                  {7,8}};
    int matrix3[][NCOLS] = {{1,2}, {3,4}, {5,6}, {7,8} };
    int matrix4[][NCOLS] = {1, 2, 3, 4, 5, 6, 7, 8};
    return 0;
}