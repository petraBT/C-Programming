#include <stdio.h>
#define MAXLEN 100

// Function prototype
int areIndependentIsograms(char word1[], char word2[]);

int main(void) {
    char word1[MAXLEN];
    char word2[MAXLEN];

    printf("Enter the first word: ");
    scanf("%s", word1);

    printf("Enter the second word: ");
    scanf("%s", word2);

    if (areIndependentIsograms(word1, word2)) {
        printf("The words %s and %s are independent isograms.\n", word1, word2);
    } else {
        printf("The words %s and %s are not independent isograms.\n", word1, word2);
    }

    return 0;
}