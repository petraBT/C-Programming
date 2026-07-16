void showMyFile(char *);
----------student code starts here----------

/******************************************************************************
Please do not modify this section, except to put in your magic number.
Replace the sample number on the line below with your magic number. 
1234
Replace the sample number on the line above with your magic number. 
*******************************************************************************/

/* Use the function showMyFile("filename") to display your file!*/

#define MAX 100
#include <stdio.h>

void printList(int array[], int N);

// add your prototypes here

/* Please do not modify this main function. */
int main(void) {
	int list1[MAX], list2[MAX], combined[2*MAX];
	int N1, N2;
	
	readFile("firstList.txt", list1, &N1);
	readFile("secondList.txt", list2, &N2);
	if ((N1!=-1) && (N2!=-1)) {
		mergeLists(list1, N1, list2, N2, combined);
		printList(combined, N1+N2);
	}
	return 0;
}

void printList(int array[], int N) {
	int i;
	for (i=0; i<N; i++) {
		printf("%d ", array[i]);
	}
	printf("\n");
}

// add your function definitions here */

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