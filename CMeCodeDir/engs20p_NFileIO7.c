/* Use the function showMyFile("filename") to display your file!*/
#include <stdio.h>

int main(void) {
    FILE *ifile;  
    int num;
    
    ifile = fopen("my_first_file_misspelled.txt", "r"); 
     
    fscanf(ifile, "%d", &num);
    printf("I read the number %d from the file.\n", num);
    fclose(ifile);

/* The 'right' way... */
/*
    ifile = fopen("my_first_file_misspelled.txt", "r"); 
    if (ifile == NULL) {
        printf("File not found!! Exiting.\n");
    } else {
        fscanf(ifile, "%d", &num);
        printf("I read the number %d from the file.\n", num);
        fclose(ifile);
    }

*/
    return(0);
}
