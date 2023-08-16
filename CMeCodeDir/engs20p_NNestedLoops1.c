#include <stdio.h>

int main(void) {
    int year, month;
    int month_total;
    
    month_total = 0;

    for (year=2010; year <= 2017; year++) {
       printf("%d:  ", year);

       for (month=1; month <= 12; month++) {
          printf(" %02d", month);
          month_total++;
       }
       printf("\n");
    }
    printf("\n%d total months\n", month_total);
    
    return(0);
}
