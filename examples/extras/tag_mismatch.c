#include <stdio.h>
#include <mpi.h>
int main(void) {
   int rank, x = 42, y = 0;
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   if (rank == 1) MPI_Send(&x, 1, MPI_INT, 0, 5, MPI_COMM_WORLD);       /* tag 5 */
   if (rank == 0) { MPI_Recv(&y, 1, MPI_INT, 1, 7, MPI_COMM_WORLD, MPI_STATUS_IGNORE); /* tag 7 */
                    printf("got %d\n", y); }
   MPI_Finalize();
   return 0;
}
