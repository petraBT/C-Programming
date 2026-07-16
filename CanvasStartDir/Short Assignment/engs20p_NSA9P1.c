#include <stdio.h>

int isPrime (int number);

int main(void) {
    int i, sum, num, divisor;
    
    for (i = 0; i < 100; i++) {
        sum = 0;
        num = i;
        
        for (divisor = 2; divisor < i; divisor++) {
            if (i % divisor == 0 && isPrime(divisor)) {
                    sum += divisor;
                    num /= divisor;
                    
                    if (isPrime(num)) {
                        sum = sum + num;
                        printf("The factor sum of %d equals %d which is ", i, sum);

                        if (isPrime(sum)) 
                            printf("prime.\n");
                        else
                            printf("not prime.\n");
                    }
            }
        }
    }
}

int isPrime(int number)  { 
    int i;
    for (i = 2; i < number; i++) {
        if (number % i == 0)
            return 0;
    }
    return 1;
}