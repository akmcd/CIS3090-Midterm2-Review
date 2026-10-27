#include <stdio.h>
#include <mpi.h>
int main(void) {
   int rank, big[10] = {0,1,2,3,4,5,6,7,8,9}, small[5];
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   if (rank == 1) MPI_Send(big, 10, MPI_INT, 0, 3, MPI_COMM_WORLD);
   if (rank == 0) { MPI_Recv(small, 5, MPI_INT, 1, 3, MPI_COMM_WORLD, MPI_STATUS_IGNORE); printf("received ok\n"); }
   MPI_Finalize();
   return 0;
}
