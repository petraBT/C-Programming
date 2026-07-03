#include <stdio.h>
/* Prototypes for square and cube functions */
float cTof (float temp);
float fToc (float temp);

int main(void){
	float temp[] = {2.3, 5.4, 34.3, 2.8, 12.0, 6.0, 27.6, 19.9, 20.3, 15.1};
	int size = 10;
	int choice, i;
	float tempconv;
	/* Declare function pointers used to point to cTof or fToc functions*/
	...

	printf("Do you want to convert to Celcius (1) or to Fahrenheit (2)? ");
	scanf("%d", &choice);

	/* Use an if statement to assign the correct function pointer to operation*/ 
	if ...

	/* Loop to calculate and print all the results */
	printf("Converted temperatures: ");
	for...

	return 0;
}
//Functions go here
float fToc (float temp){
	//Write the temperature conversion
	return (temp-32)*5.0/9.0;
}
float cTof (float temp){
	//Write the temperature conversion
	return temp*9.0/5.0+32;
}
