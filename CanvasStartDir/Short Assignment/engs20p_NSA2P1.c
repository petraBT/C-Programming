/*
 * miles2km.c
 *
 * Converts distance from miles to kilometers.
 */

#include <stdio.h>		/* printf and scanf definitions */
#define KMS_PER_MILE 1.609	/* conversion constant */

int main(void)
{
	float miles, kms;		/* distance in miles, equivalent
				             * distance in kilometers */
	/* Get the distance in miles. */
	printf("Enter the distance in miles: ");
	scanf("%f", &miles);

	/* Convert the distance to kilometers. */
	kms = KMS_PER_MILE * miles;

	/* Display the distance in kilometers. */
	printf("%f miles equal %f kilometers.\n", miles, kms);

	return (0);
}