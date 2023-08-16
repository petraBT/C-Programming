#include <stdio.h>
int main(void) {
    int n;
 /* n++; ++n; n--; --n; */   
    n = 5;
    printf("%d ", n);
    printf("%d ", n++); /* postfix */
    printf("%d ", n);
    printf("\n\n");
    
    n = 5;
    printf("%d ", n);
    printf("%d ", ++n); /* prefix */
    printf("%d ", n);
    printf("\n\n");

    n = 5;
    printf("%d ", n);
    printf("%d ", n--); /* postfix */
    printf("%d ", n);
    printf("\n\n");
    
    n = 5;
    printf("%d ", n);
    printf("%d ", --n); /* prefix */
    printf("%d ", n);
    printf("\n\n");
    return(0);
}