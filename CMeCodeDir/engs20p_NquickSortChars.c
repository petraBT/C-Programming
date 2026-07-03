#define SIZE 8
#include<stdio.h>
void printArray(int list[],int n);
void quickSort(int list[], int start, int end);
int partition(int list[], int start, int end);

int main(void) {
    
    int list[] = {20,5,8,47,35,2,78,24}; /* unsorted numbers */
    printf("Unsorted array\n");
    printArray(list,SIZE);
    quickSort(list,0, SIZE-1);
    printf("Sorted array\n");
    printArray(list,SIZE);

	return 0;
}
int partition(int list[], int start, int end){
    int i, j, pivot, swap;
    pivot = list[end];
    i = start - 1;
    for(j=start; j<end; j++){
        if(list[j]<pivot){
            i++;
            swap = list[i];
            list[i] = list[j];
            list[j] = swap;
        }
    }
    i++;
    swap = list[end];
    list[end] = list[i];
    list[i] = swap;
    printArray(list,SIZE);
    return i;
}
void quickSort(int list[], int start, int end){
    int i;
    if(end>start){
        i = partition(list, start, end);

        //sort left part
        quickSort(list, start, i-1);

        //sort right part
        quickSort(list, i+1, end);
    }
    else{
        return;
    }
}
void printArray(int list[],int n){
    int i;
    for(i=0; i<n; i++){
        printf("%d ", list[i]);
    }
    printf("\n");
}