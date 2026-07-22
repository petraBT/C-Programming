#include<stdio.h>
void swap(int *a, int *b);
void insertionSort(int numbers[], int len);
void printArray(int numbers[], int len);

int main(void) {
    int list[] = {759, 14, 2, 900, 106, 77, -10, 8, -3, 5}; /* unsorted list */
    int n = 10;
    printf("Unsorted: \n");
    printArray(list, n);
    insertionSort(list, n);
    printf("Sorted: \n");
    printArray(list, n);
    return 0;
}

void printArray(int numbers[], int len) {
    int i;
    for (i=0; i<len; i++)  {
        printf("%d ", numbers[i]);
    }
    printf("\n");
}

void swap(int *a, int *b) { 
    int temp = *a; 
    *a = *b; 
    *b = temp; 
}

void insertionSort(int numbers[], int len){
    int i, j; 
    for (i = 1; i < len; i++) {
        j = i;
        while ((j>0) && (numbers[j]<numbers[j-1])) {
           swap(&numbers[j], &numbers[j-1]);
           j--;
        }
    } 
}
