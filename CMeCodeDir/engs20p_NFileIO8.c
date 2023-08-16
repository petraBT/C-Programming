/* Use the function showMyFile("filename") to display your file!*/
#include <stdio.h>

int main(void) {
    FILE *ofile;  /* You can use any variable name here, just make sure you 
                     include the '*'. */
    int num;
    
    ofile = fopen("my_first_output_file.txt", "w"); 
     
    do {
        printf("Please enter a grade. Enter -1 to quit: ");
        scanf("%d", &num);
        if (num != -1)
            fprintf(ofile, "%d ", num);        
    } while (num != -1);
    fclose(ofile);
    
    return(0);
}
