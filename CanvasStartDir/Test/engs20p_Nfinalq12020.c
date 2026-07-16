/******************************************************************************
Please do not modify this section, except to put in your magic number.
Replace the sample number on the line below with your magic number. 
1234
Replace the sample number on the line above with your magic number. 
*******************************************************************************/

#include <stdio.h>
#define STRLEN 50

void enterString(char * str);
// add your prototype here

/* Please do not modify this main function. */
int main(void) {
    char string1[STRLEN], string2[STRLEN];
    int result;
    
    printf("Please enter the first string: ");
    enterString(string1);
    printf("Please enter the second string: ");
    enterString(string2);
    result = containsString(string1, string2);
    if (result == 0) {
        printf("The string \"%s\" does not contain the string \"%s\".\n", string1, string2);
    } else if (result == 1) {
        printf("The string \"%s\" contains the string \"%s\".\n", string1, string2);
    } else {
        printf("Your function returned an invalid value.\n");
    }
    
    return 0;
}

void enterString(char * str) {
    int i = 0;
    char c;
    int done = 0;
    do {
        scanf("%c", &c);
        if (c!='\n') {
            str[i] = c;
        } else {
            str[i] = '\0';
            done = 1;
        }
        i++;
        if (i==STRLEN-1) {
            str[i] = '\0';
            done = 1;
        }
    } while (!done);
}
 /* add your function here */