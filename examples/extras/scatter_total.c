#include <stdio.h>
#include <mpi.h>
int main(void) {
   int rank, size, all[8] = {1,2,3,4,5,6,7,8}, mine[8] = {0};
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   MPI_Comm_size(MPI_COMM_WORLD, &size);
   /* send_count = TOTAL (8) instead of per-process chunk (2) */
   MPI_Scatter(all, 8, MPI_INT, mine, 2, MPI_INT, 0, MPI_COMM_WORLD);
   printf("rank %d got %d %d\n", rank, mine[0], mine[1]);
   MPI_Finalize();
   return 0;
}
