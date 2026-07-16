void showMyFile(char *);
----------student code starts here----------

/******************************************************************************
Please do not modify this section, except to put in your magic number.
Replace the sample number on the line below with your magic number. 
1234
Replace the sample number on the line above with your magic number. 
*******************************************************************************/

/* Use the function showMyFile("filename") to display your file for 
   testing purposes!*/



----------student code ends here----------
void showMyFile(char *filename) {
    FILE *ifile;
    char ch;
    ifile = fopen(filename, "r");
   
    if (ifile != NULL){
      while (fscanf(ifile, "%c", &ch) != EOF){
         printf("%c", ch);
      }
      printf("\n");
      fclose(ifile);
    }
}