#include <stdio.h>
#define MAXLEN 50

int containsString(char word[], char sub[]);

int main(void) {
    char wordarray[][MAXLEN] = {"thermostat", "most", "strawberry", "hello", "hello", "mostly"};
    char subarray[][MAXLEN] = {"most", "thermostat", "berries", "hello", "Hello", "most"};
    int n = 6;
    int i;
    
    for (i=0; i<n; i++) {
        if (containsString(wordarray[i], subarray[i]))
            printf("The word %s contains the word %s.\n", wordarray[i], subarray[i]);
        else
            printf("The word %s does not contain the word %s.\n", wordarray[i], subarray[i]);
    }
    return 0;
}

int containsString(char word[], char sub[]) {
    /* Your code goes here */
}