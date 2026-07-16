void showMyFile(char *);

----------student code starts here----------
/* Use the function showMyMile("filename") to display your file!*/
#define N 12
#define MAXLEN 30
#include <stdio.h>

typedef struct {
    int year;
    int month;
    int day;
    char name[MAXLEN];
} moonDate_t;

void readMoons(moonDate_t *dates);
void printMoons(moonDate_t *dates);

int main(void) {
    moonDate_t dates[N];
    readMoons(dates);
    printMoons(dates);
    return 0;
}

----------student code ends here----------
void showMyFile(char *filename)
{
    FILE *ifile;
    char ch;
    ifile = fopen(filename, "r");
    
    if (ifile != NULL){
    
        while (fscanf(ifile, "%c", &ch) != EOF){
            printf("%c", ch);
        }
        fclose(ifile);
    } else {
        printf("File \"%s\" does not exist. Check your spelling of the filename.\n", filename);
    }
}