#include <stdio.h>
void countDigitFrequencies(int N, int array[], int digits[], int *processed);

int main(void) {
    int numbers[] = {12, 101, -23, 44, -900};
    int digits[10];
    int n = 5;
    int i, total;
    
    countDigitFrequencies(n, numbers, digits, &total);

    for (i = 0; i < 10; i++) {
        printf("Digit %d: %d times\n", i, digits[i]);
    }
    printf("Total digits processed: %d\n", total);
    return 0;
}

/* Write your function here. */