#include <stdio.h>

int main(void) {
    FILE *ifile;  /* ifile is a variable name - you could use any other name here. 
                     However, the '*' is important. We'll learn about it more later. 
                     We call this a file pointer. */
    int i, num, N, sum;
    
    N = 10; /* we are told there are 10 numbers in the file */
    
    ifile = fopen("my_first_file.txt", "r"); /* open file for reading. 
                                                     The "r" stands for reading. */

    sum = 0;
    for (i = 0; i<N; i++) {
        fscanf(ifile, "%d", &num);
        printf("I read %d from the file. \n", num);
        sum += num;
    }
    
    fclose(ifile);
    
    printf("The sum of the numbers read is %d. The average is %.2f.", sum, (float) sum / N);
    
    return(0);
}
