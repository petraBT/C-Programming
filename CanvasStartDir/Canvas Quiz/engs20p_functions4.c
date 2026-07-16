#include <stdio.h>

/* Here is your prototype. */
void minutesToHoursMinutes(int totalMinutes, int *hours, int *minutes);

int main(void) {
 
	int totalTime, newHours, newMinutes;
    totalTime = 0;

	printf("Enter total minutes to convert: ");
	scanf("%d", &totalTime);
	
    minutesToHoursMinutes(totalTime, &newHours, &newMinutes);
    printf("%d minutes equals %d hours and %d minutes.", totalTime, newHours, newMinutes);
    
    return(0);
}

/* Your function goes here. */