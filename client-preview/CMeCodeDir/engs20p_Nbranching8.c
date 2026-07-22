#include <stdio.h>
int main(void) {
    int sunny = 8; /* on a scale of 1 to 10 */
    int vacation = 1;
    
    if ( (sunny>5) && vacation) {
        printf("It\'s super sunny and I am on vacation! What could be better?\n");
    } else {
        printf("Ugh!\n");
    }
    
    return(0);
}
