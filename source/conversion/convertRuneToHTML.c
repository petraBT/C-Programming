#include <stdio.h>
#include <strings.h>
#include <stdlib.h>

#define FNLENGTH 200
#define MAX 10000
#define TAGLEN 2000

void call(FILE *ifile, FILE *ofile, char command[], char line[]);
void dumptagcall(FILE *ofile, char line[]);
void responseboxcall(FILE *ifile, FILE *ofile);
int parse(FILE *ifile, FILE *ofile, char tag[]);
void dumpactivity(FILE *ofile, char activity[], char xmlid[]);
void dumpFalseActivity(FILE *ofile, char activity[]);
void getxmlid(char activity[], char xmlid[]);
void programToResponse(char activity[], char xmlid[]);

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
   	  if (strcmp(tag, "<activity>")==0) {
   		   call(ifile, ofile, "response", tag);
   	  } else {
   	  	   call(ifile, ofile, "dump", tag);
   	  }
   } 
   
   fclose(ifile);
   fclose(ofile);   
   return(0);
}

void call(FILE *ifile, FILE *ofile, char command[], char line[]) {
	if (strcmp(command,"response")==0)
		responseboxcall(ifile, ofile);
	else if (strcmp(command,"dump")==0)
		dumptagcall(ofile, line);
	else
		printf("Unknown command: %s\n", command);		
}

void dumptagcall(FILE *ofile, char line[]) {
	fprintf(ofile, "%s", line);
}

void responseboxcall(FILE *ifile, FILE *ofile) {
	char activity[MAX];
	char tag[TAGLEN];
	char xmlid[TAGLEN];
	int i = 0;
	int j = 0;
	int cont;
	int readingdone = 0;
	char c;
	
	while (!readingdone) {
		while ((cont = (fscanf(ifile, "%c", &c)!= EOF)) && (c!='<')) {
			activity[j] = c;
			j++;
		}
		if (!cont) {
			printf("emergency stop\n");
			activity[j] = '\0';
			dumptagcall(ofile, activity);
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
		} else if (strcmp(tag, "</activity>") == 0) {
			readingdone = 1;
			activity[j] = '\0';
		} else {
			i = 0;
			while (tag[i] != '\0') {
				activity[j++] = tag[i++];
			}
		}
	}
	//printf("***\n%s\n***", activity);
	getxmlid(activity, xmlid);
	//printf("xml:id = %s\n", xmlid);
	if (xmlid[0]!='\0') {
		programToResponse(activity, xmlid);
		//printf("modified:\n%s\n", activity);
		dumpactivity(ofile, activity, xmlid);
	} else {
		//printf("dumping\n");
		dumpFalseActivity(ofile, activity);
	}
}

void dumpFalseActivity(FILE *ofile, char activity[]) {
	fprintf(ofile, "<activity>");
	dumptagcall(ofile, activity);
	fprintf(ofile, "</activity>");
}

void dumpactivity(FILE *ofile, char activity[], char xmlid[]) {
	fprintf(ofile, "<activity xml:id=%s>", xmlid);
	dumptagcall(ofile, activity);
	fprintf(ofile, "</activity>");
}

void getxmlid(char activity[], char xmlid[]) {
	char *p = NULL;
	int i = 0;
	p = strstr(activity, "xml:id=");
	if (p!=NULL) {
		p = p+strlen("xml:id=");
		while (p[i] != ' ') {
			xmlid[i] = p[i];
			i++;
		}
		xmlid[i] = '\0';
	} else {
		xmlid[0] = '\0';
	}
}

void programToResponse(char activity[], char xmlid[]) {
	char *p = NULL;
	char comparestring[MAX];
	int i = 0;
	
	sprintf(comparestring, "<program xml:id=%s", xmlid);
	
	p = strstr(activity, comparestring);
	if (p!=NULL) {
		strcpy(p, "<response/>\n");
		p = p+strlen("<response/>\n");
		while (*p != '>') {
			*p = '\0';
			p++;
		}
		*p = '\0';
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