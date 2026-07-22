#include <stdio.h>
#define NUM 100

// prototypes here

int main(void){
    char array[NUM];
    int length;
    
    enterPhrase(array, &length);
    printPhrase(array, length);

  return 0;  
}

// function definitions here
