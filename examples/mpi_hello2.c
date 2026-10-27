/* File:       
 *    mpi_hello.c
 *
 * Purpose:    
 *    A "hello,world" program that uses MPI
 *
 * Compile:    
 *    mpicc -g -Wall -std=c99 -o mpi_hello2 mpi_hello2.c
 * Usage:        
 *    mpiexec -n<number of processes> ./mpi_hello
 *
 * Input:      
 *    None
 * Output:     
 *    A greeting from each process
 *
 * Algorithm:  
 *    Each process sends a message to process 0, which prints 
 *    the messages it has received, as well as its own message.
 *
 * IPP:  Section 3.1 (pp. 84 and ff.)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>  /* For strlen             */
#include <mpi.h>     /* For MPI functions, etc */ 

const int MAX_STRING = 100;

int main(void) {
   char       greeting[MAX_STRING];  /* String storing message */
   int        comm_sz;               /* Number of processes    */
   int        my_rank;               /* My process rank        */

   /* Start up MPI */
   MPI_Init(NULL, NULL); 

   /* Get the number of processes */
   MPI_Comm_size(MPI_COMM_WORLD, &comm_sz); 

   /* Get my rank among all the processes */
   MPI_Comm_rank(MPI_COMM_WORLD, &my_rank); 


   if (my_rank != 0) { 
      /* Create message */
      sprintf(greeting, "Greetings from process %d of %d!", my_rank, comm_sz);
               
      srand(my_rank);
      int tag = rand() % 50;

      /* Send message to process 0 */
      MPI_Send(greeting, strlen(greeting)+1, MPI_CHAR, 0, tag, MPI_COMM_WORLD); 
   } else {  
      /* Print my message */
      printf("Greetings from process %d of %d!\n", my_rank, comm_sz);
      for (int q = 1; q < comm_sz; q++) {
         /* Receive message from some process */
         MPI_Status status;
         MPI_Recv(greeting, MAX_STRING, MPI_CHAR, MPI_ANY_SOURCE, MPI_ANY_TAG, MPI_COMM_WORLD, &status);
         int rank = status.MPI_SOURCE;  // retrieve sender’s rank 
         int tag = status.MPI_TAG;      // retrieve sent tag
         int count;
         MPI_Get_count(&status, MPI_CHAR, &count); 
         printf("Received a message from process %d with tag %d: %d elements\n", rank, tag, count);

         /* Print message from some process */
         printf("%s\n", greeting);
      } 
   }

   /* Shut down MPI */
   MPI_Finalize(); 

   return 0;
}  /* main */

