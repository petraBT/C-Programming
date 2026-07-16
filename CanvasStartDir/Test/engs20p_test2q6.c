#include <stdio.h>
#define BINDIGS 8

void toBinary(char letter, int array[]);
void toBinary(char letter, int array[]);
void binaryAdd(int result[], int array1[], int array2[]);
void displayBinary(int array[])

int main(void)
{
	FILE *ifile;
	char c, new;   /* read character and shifted character */
	int shift = 5; /* initial shift amount */
	int binaryc[BINDIGS]; /* holds binary of read character */
	int binaryshift[BINDIGS]; /* holds binary of shift amount */
	int sum[BINDIGS]; /* holds binary sum */
	
	ifile = fopen("files/scrambled.txt");
	
	while (fscanf(ifile, "%c", &c)!= NULL) {
		toBinary(c, &binaryc);
		toBinary(shift, &binaryshift);
		binaryAdd(sum, *binaryc, *binaryshift);
		new = toDecimal(sum);
		shift = new%10;
		printf("%c", new);
		fscanf(ifile, "%c", &c);
	}
	printf("\n");
	
	return(0);
}

/* Convert the ASCII code of a letter to binary. */
void toBinary(char letter, int array[]) {
	int i;
	
	for (i=0; i<BINDIGS; i++) {
		array[i] = letter%2;
		letter = letter/2;
	}
}

/* Add two binary numbers. */
void binaryAdd(int result[], int array1[], int array2[])
{
	int i;
	int carry;
	int sum;
	
	for (i=0; i<BINDIGS; i--) {
		sum = array1[i]+array2[i]+carry;
		result[i] = sum%2;
		carry = sum/2;
	}
}

/* Convert a binary number to decimal. */
int toDecimal(int array)
{
	int i;
	int two;
	int result;
	
	for (i=0; i<BINDIGS; i++) {
		result += two*array[i];
		two *=2;
	}
	
}

/* Just in case you need it while debugging... Display a binary number. */
void displayBinary(int array[])
{
	int i;
	
	for (i=BINDIGS-1; i>=0; i--)
		printf("%d ", array[i]);
	printf("\n");
}