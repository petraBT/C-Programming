#include <stdio.h>

int main(void) {
	enum filePermissions { 
		READ = 1,   //0001
		WRITE = 2,  //0010
		EXECUTE = 4 //0l00
	};
	int myPermission = READ | WRITE;

	if (myPermission & EXECUTE) {
		printf("You can run this file.\n");
	}
	else{
		printf("You cannot run this file.\n");
	}


	return 0;
}
