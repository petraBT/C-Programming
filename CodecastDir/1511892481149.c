#include <stdio.h>

int main(void) {
    int applesPerSalad;
    applesPerSalad = 2;
    
    printf("One fruit salad needs %d apples.\n", applesPerSalad);
    printf("Two fruit salads need %d apples.\n", 2*applesPerSalad);
    printf("%d fruit salads need %d apples.\n", 8, 8*applesPerSalad);
    printf("That\'s a lot of apples: %d more than for one salad.\n", 
    8*applesPerSalad - applesPerSalad);

    return(0);
}