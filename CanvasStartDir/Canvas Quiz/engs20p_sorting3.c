#include <stdio.h>

void printArray(int numbers[], int len);
void bubbleSort(int numbers[], int len);
int main(void)
{
    /* Feel free to change the array, just be sure to update the length n, if necessary. */ 
    int numbers[]={5, -1, 8, 4, 0, -10, 12, 6};
    int n=8;
    int i, j;
    
    printf("Before: ");
    printArray(numbers, n);
    bubbleSort(numbers, n);
    printf("Sorted array: ");
    printArray(numbers, n);
    
    return(0);
}

void printArray(int numbers[], int len)
{
    int i;
    for (i=0; i<len; i++) 
    {
        printf("%d ", numbers[i]);
    }
    printf("\n");
}

void bubbleSort(int numbers[], int len)
{
    int i,j;
    
    for(j=0;j<len-1; j++)       
    {
        for(i=0;i<len-1;i++)
        {
            
            /* You need to fill in this part. 
               If you use additional variables,
               be sure to declare them. */
    
        }
    }
}