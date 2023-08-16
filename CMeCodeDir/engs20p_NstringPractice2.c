#include <stdio.h>
#include <string.h>

// prototype

int main(void) {
    char phrase[]= "Today is Wednesday!";
    int num;
    num = countWords(phrase);
    printf("The sentence \"%s\" has %d words.\n", phrase, num);
    return 0;
}

// function definition
