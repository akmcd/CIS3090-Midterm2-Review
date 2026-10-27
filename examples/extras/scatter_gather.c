#include <stdio.h>
#include <mpi.h>
int main(void) {
   int rank, size, all[8] = {1,2,3,4,5,6,7,8}, mine[8], back[8] = {0};
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   MPI_Comm_size(MPI_COMM_WORLD, &size);
   int chunk = 8 / size;
   MPI_Scatter(all, chunk, MPI_INT, mine, chunk, MPI_INT, 0, MPI_COMM_WORLD);
   for (int i = 0; i < chunk; i++) mine[i] *= 10;
   MPI_Gather(mine, chunk, MPI_INT, back, chunk, MPI_INT, 0, MPI_COMM_WORLD);
   if (rank == 0) {
      for (int i = 0; i < 8; i++) printf("%d ", back[i]);
      printf("\n");
   }
   MPI_Finalize();
   return 0;
}
