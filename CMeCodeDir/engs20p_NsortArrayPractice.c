#include <stdio.h>

/* prototypes here */
void printArray(int N, int array[], int sort[]);

int main(void) {
    int list[] = {5, -1, 8, 4, 0, -10}; // sample list - feel free to change!
    int sort[]={0, 1, 2, 3, 4, 5}; // change this - play with different orders
    int n=6; 
    printf("Unsorted: ");
    printArray(n, list, sort);
    sortArray(n, list, sort);
    printf("Sorted: ");
    printArray(n, list, sort);
    return 0;
}

void sortArray(...)

void printArray(int N, int array[], int sort[]) {
    int i;
    for (i=0; i<N; i++) {
        printf("%d ", array[sort[i]]);
    }
    printf("\n");
}
