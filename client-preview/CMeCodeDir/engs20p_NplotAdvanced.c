#include <stdio.h>
#include <stdlib.h>

int main(void){
    float data[5] = {1.2, 2.5, 4.0, 3.1, 5.5};
    float data2[5] ={5.4, 0.2, 3.9, 8.2, 4.6};
    int i;
    int size = 5;
    
    FILE *gfile = popen("gnuplot", "w");

    fprintf(gfile, "set terminal png\n");
    fprintf(gfile, "set output 'plot_multiple_curves.png'\n");

    fprintf(gfile, "set title 'Comparison data and data2'\n");
    fprintf(gfile, "set xlabel 'time (seconds)'\n");
    fprintf(gfile, "set ylabel 'position (m)'\n");

    fprintf(gfile, "plot '-' with lines title 'data', '-' with lines title 'data 2'\n");
    for(i=0; i<size; i++){
        fprintf(gfile, "%d %f\n", i, data[i]); // coordinates x and y
    }
    fprintf(gfile, "e\n");

    for(i=0; i<size; i++){
        fprintf(gfile, "%d %f\n", i, data2[i]); //coordinates of x and y for second curve
    }
    fprintf(gfile, "e\n");
    pclose(gfile);

    return 0;
}