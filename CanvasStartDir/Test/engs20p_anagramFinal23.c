#include <stdio.h>
#include <string.h>
#define MAXLEN 50

int main(void) {
    char word1[MAXLEN], word2[MAXLEN];
    int anagrams = 0;
    
    printf("Please enter two words you wish to compare, separated by a space: ");
    scanf("%s %s", word1, word2);
    
    /* your code goes here */
    
    printf("The words %s and %s ", word1, word2);
    if (anagrams) {
        printf("are anagrams.\n");
    } else {
        printf("are not anagrams.\n");
    }
    
    return 0;
}