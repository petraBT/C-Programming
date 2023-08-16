#define N 10
#include <stdio.h>

/* function prototype here */

int main(void) {
    int array[N];
    int i;
    
    for (i=0; i<N; i++) {
        array[i] = 0;
    }
    printf("Array elements before function call: \n");
    for (i=0; i<N; i++) {
        printf("%d  ", array[i]);
    }
    printf("\n");
    
    /* function call here */
    
    printf("Array elements after function call: \n");
    for (i=0; i<N; i++) {
        printf("%d  ", array[i]);
    }
    printf("\n");
    
    return 0;
}

void enterValues(/*complete this part */) {
    /* function body here */
}
