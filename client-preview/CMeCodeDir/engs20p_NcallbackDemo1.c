#include <stdio.h>

/* callback functions */
void sayHello();
void sayGoodbye();

/* master functions */
void repeatThreeTimes( void (* messageFunction) () );

int main(void){
	
	repeatThreeTimes(sayHello);
	repeatThreeTimes(sayGoodbye);

	return 0;
}

void sayHello(){
	printf("Hello!\n");
}

void sayGoodbye(){
	printf("Goodbye!\n");
}

void repeatThreeTimes( void (* messageFunction) () ){
	int i;
	for(i=0; i<3; i++){
		messageFunction();
	}
}
