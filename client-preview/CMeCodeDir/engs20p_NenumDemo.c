#include <stdio.h>

int main(void) {
	enum day { MON, TUE, WED, THU, FRI, SAT, SUN }; // MON == 0, SUN == 6
	enum day today = WED; // assign enumerator
								 
	printf("day %d\n", today);  // prints 2 (0‑based)
										 
	if (today == WED){
		printf("mid‑week!\n");
	}

	return 0;
}
