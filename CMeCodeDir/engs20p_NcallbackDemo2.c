#include <stdio.h>
#include <math.h>

/* callback functions */
float fsquare(int num);
float fcube(int num);
float fsquareroot(int num);

/* master function */
float calculate(int num, float (*op)(int));

int main(void) {
	int num = 6;
	float result;

	result = calculate(num, &fsquare);
	printf("Square of %d: %f\n", num, result);
	result = calculate(num, &fcube);
	printf("Cube of %d: %f\n", num, result);
	printf("Square roof of %d: %f\n", num, calculate(num,&fsquareroot));

	return (0);
}

float calculate(int num, float (*op)(int)){
	float result;
	result = (*op)(num);
	return result;
}

float fcube(int num){
	return num * num * num;
}

float fsquare(int num){
	return num * num;
}

float fsquareroot(int num){
	return sqrt(num);
}

