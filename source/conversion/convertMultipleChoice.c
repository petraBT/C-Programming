#include <stdio.h>
#include <strings.h>
#include <stdlib.h>

#define FNLENGTH 200
#define MAX 10000
#define TAGLEN 2000

void call(FILE *ifile, FILE *ofile, char command[], char line[]);
void dumptagcall(FILE *ofile, char line[]);
int parse(FILE *ifile, FILE *ofile, char tag[]);
void potentialmc(FILE *ifile, FILE *ofile);
void dumpStatement(FILE *ofile, char statement[]);
void createMC(char statement[], char newstatement[]);

int main( int argc, char *argv[] )  {

	char ifilename[FNLENGTH];
	char ofilename[FNLENGTH];
	FILE *ifile, *ofile;
	char *extensionp;
	int i=0;
	char tag[TAGLEN];
		
    if( argc == 2 ) {
    	strcpy(ifilename, argv[1]);
        printf("Converting file %s.\n", ifilename);
    }
    else if( argc > 2 ) {
       printf("Too many arguments supplied.\n");
       exit(-1);
    }
    else {
       printf("Please supply filename as argument.\n");
       exit(-1);
   }
   
   strcpy(ofilename, ifilename);
   extensionp = strchr(ofilename, '.');
   strcpy(extensionp,".new");
   printf("Output filename is %s.\n", ofilename);
   
   ifile = fopen(ifilename, "r");
   ofile = fopen(ofilename, "w");
   
   while (parse(ifile, ofile, tag)) {
   	  if (strcmp(tag, "<statement>")==0) {
   		   call(ifile, ofile, "statement", tag);
   	  } else {
   	  	   call(ifile, ofile, "dump", tag);
   	  }
   } 
   
   fclose(ifile);
   fclose(ofile);   
   return(0);
}

void call(FILE *ifile, FILE *ofile, char command[], char line[]) {
	if (strcmp(command,"statement")==0)
		potentialmc(ifile, ofile);
	else if (strcmp(command,"dump")==0)
		dumptagcall(ofile, line);
	else
		printf("Unknown command: %s\n", command);		
}

void dumptagcall(FILE *ofile, char line[]) {
	fprintf(ofile, "%s", line);
}

void potentialmc(FILE *ifile, FILE *ofile) {
	char statement[MAX];
	char newstatement[MAX];
	char tag[TAGLEN];
	int i = 0;
	int j = 0;
	int cont;
	int readingdone = 0;
	char c;
	char *p;
	
	while (!readingdone) {
		while ((cont = (fscanf(ifile, "%c", &c)!= EOF)) && (c!='<')) {
			statement[j] = c;
			j++;
		}
		if (!cont) {
			printf("emergency stop\n");
			statement[j] = '\0';
			dumptagcall(ofile, statement);
			return;
		}
	
		tag[0] = '<';
		i = 1;
		do {
		   cont = (fscanf(ifile, "%c", &c)!=EOF);
		   tag[i] = c;
		   i++;
		} while ((c != '>') && (i<TAGLEN) && cont);
		tag[i]='\0';
		if ((i==TAGLEN) || (!cont)) {
			printf("Something went wrong: %s\n", tag);
			printf("Aborting.\n");
			return;
		} else if (strcmp(tag, "</statement>") == 0) {
			readingdone = 1;
			statement[j] = '\0';
		} else {
			i = 0;
			while (tag[i] != '\0') {
				statement[j++] = tag[i++];
			}
		}
	}
	p = strstr(statement, "Enter your choice");
	if (p!=NULL) {
		createMC(statement, newstatement);
		fprintf(ofile, "%s", newstatement);
	} else {
		dumpStatement(ofile, statement);
	}
}

void dumpStatement(FILE *ofile, char statement[]) {
	fprintf(ofile, "<statement>");
	dumptagcall(ofile, statement);
	fprintf(ofile, "</statement>");
}

void createMC(char statement[], char newstatement[]) {
	int mcdone = 0;
	char *p, *q, *e;
	int i = 0;
	char mcOpening[] = 
		"</statement>\n" 
		"            <choices randomize=\"yes\">\n"  
		"               <choice correct=\"yes\">)\n"
		"                  <statement>\n"
		"                     <p>";
	char mcOpeningEnd[] = 
		"</p>\n"
		"                  </statement>\n"
		"                  <feedback>\n"
		"                     <p>Correct</p>\n"
		"                  </feedback>\n"
		"               </choice>\n";
	char mcGeneralStart[] =  
		"               <choice>\n"
		"                  <statement>\n"
		"                     <p>";
	char mcGeneralEnd[] = 
	    "</p>\n"
		"                  </statement>\n"
		"                  <feedback>\n"
		"                     <p>Not quite. Try again!</p>\n"
		"                  </feedback>\n"
		"               </choice>\n";
    char mcClosing[] = 
        "            </choices>";

/*    char mcClosing[] = 
        "            </choices>\n"
        "            <hint>\n"
        "               <p>Coming soon.</p>\n"
        "            </hint>"; */


	p = strstr(statement, "<ol>");
	if (p!=NULL) {
		strcpy(newstatement, "<statement>");
		q = newstatement + strlen(newstatement);
		i = 0;
		while (statement+i<p) {
			q[i] = statement[i];
			i++;
		}
		q = q+i;
		strcpy(q, mcOpening);
		q = q+strlen(mcOpening);
		p = strstr(p, "<li>");
		e = strstr(p, "</li>");
		if (p!=NULL && p<e) {
			p = p+strlen("<li>");
			i = 0;
			while (p+i<e) {
				q[i] = p[i];
				i++;
			}
			q = q+i;	
			p = p+i;
            strcpy(q, mcOpeningEnd);
            q = q + strlen(mcOpeningEnd);
        	do {
        		p = strstr(p, "<li>");
        		if (p!=NULL) e = strstr(p, "</li>");
				if (p!=NULL && p<e) {
				    p = p+strlen("<li>");
					strcpy(q, mcGeneralStart);
					q = q + strlen(mcGeneralStart);
					i = 0;
					while (p+i<e) {
						q[i] = p[i];
						i++;
					}
					q = q+i;	
					p = p+i;
					strcpy(q, mcGeneralEnd);
            		q = q + strlen(mcGeneralEnd);
        		} else {
        			mcdone = 1;
        		}
        	} while (!mcdone);
        	strcpy(q, mcClosing);
		} else {
			printf("something went wrong. Dumping.");
			strcpy(newstatement, statement);
		}
	} else {
		printf("didn't fix anything\n");
	}
}

int parse(FILE *ifile, FILE *ofile, char tag[]) {
	char c, p;
	int i, brackets;
	int cont;
	
	while ((cont = (fscanf(ifile, "%c", &c)!= EOF)) && (c!='<')) {
		fprintf(ofile, "%c", c);
	}
	if (!cont) 
		return(0); //nothing to read
	
	tag[0] = '<';
	i = 1;
	do {
	   cont = (fscanf(ifile, "%c", &c)!=EOF);
	   if (cont) {
	   		tag[i] = c;
	   		i++;
	   	}
	} while ((c != '>') && (i<TAGLEN) && cont);
	tag[i]='\0';
	//printf("Check: tag = %s.\n", tag);
	if ((i==TAGLEN) || (!cont)) {
		printf("Invalid tag found: %s\n", tag);
		printf("Aborting.\n");
		return(0);
	}
		
	return(1);	//content was read
}