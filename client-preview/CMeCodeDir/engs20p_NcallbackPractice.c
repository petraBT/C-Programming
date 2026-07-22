#include <stdio.h>
#define N 10 
/* Prototypes for square and cube functions */
void printArray(int array[], int size);
void bubble(int array[], int size);

int main(void){
	int list[]={42, 17, -5, 88, 3, 105, -21, 56, 9, 34};

	printf("Unsorted array:\n");
	printArray(list, N);
	bubble(list, N);
	printf("Sorted array:\n");
	printArray(list, N);

	return 0;
}

void bubble(int array[], int size){
	int i,j,swap;
	for(j=0; j<size-1; j++){
		for(i=0; i<size-1; i++){ 
			if(array[i] > array[i+1]){
				swap = array[i];
				array[i] = array[i+1];
				array[i+1] = swap;
			} 
		}
	}
}
void printArray(int array[], int size){
	int i;
	for(i=0; i<size; i++){
		printf("%d ", array[i]);
	}
	printf("\n");
}

