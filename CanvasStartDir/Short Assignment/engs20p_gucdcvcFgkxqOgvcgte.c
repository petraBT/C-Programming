#include <stdio.h>   /* for printf(), etc */
#include <stdlib.h>  /* for malloc(), etc */
#include <string.h> /* for string operations */

#define TSTRLEN 25
#define GSTRLEN 10

struct movie {
      char    title[TSTRLEN];
      char    genre[GSTRLEN];
      short   rating;
      struct movie *next;
};

typedef struct movie movie_t;

movie_t *create_movie(char *newtitle, char *newgenre, short newrating);
void destroy_movie(movie_t *ptr);
void destroy_database(movie_t *ptr);

int main(void)
{
	movie_t *movie_list;
	movie_t *end, *new;
	
	/* Create first element of database */
	movie_list = create_movie("Gravity", "sci-fi", 7);
	end = movie_list;
	
	/* Create second element and link it to the first */
	new = create_movie("How to train your dragon", "fantasy", 8);
	end->next = new;
	end = new;
	
	/* Create third element and link it to the second */
	new = create_movie("Interstellar", "sci-fi", 9);
	end->next = new;
	end = new;
	
	
	/* Your code here! */
	
	
	
	/* Free all reserved space */
	destroy_database(movie_list); 	
	return(0);
	
}

movie_t *create_movie(char *newtitle, char *newgenre, short newrating)
{
	movie_t *ptr;
	
	/* allocate the memory for a single movie type object */
	ptr = (movie_t *)malloc(sizeof(movie_t));
	
	/* now initialize it with input parameters */
	strcpy(ptr->title, newtitle);
	strcpy(ptr->genre, newgenre);
	ptr->rating = newrating;
	ptr->next = NULL;		/* default to NULL pointer */
	
	return (ptr);
}

void destroy_movie(movie_t *ptr)
{
	free(ptr);
}

void destroy_database(movie_t *ptr)
{
	movie_t *current, *next;
	
	/* Start with the first element of the movie list  */
	/* (passed into the function from main).           */ 
	/* Before you can destroy it though, you need to   */
	/* memorize the address of the next element.       */
	current = ptr;
	next = current->next;
	
	do {
		destroy_movie(current);
		current = next;    /* move on to the next record */
		if (current != NULL) next = current->next;
	} while (current != NULL);  /* Finished if you reach the last one. */
	
}