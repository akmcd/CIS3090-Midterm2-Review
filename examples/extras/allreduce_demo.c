#include <stdio.h>
#include <mpi.h>
int main(void) {
   int rank, size, mine, total = -1, total2 = -1;
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   MPI_Comm_size(MPI_COMM_WORLD, &size);
   mine = rank + 1;
   MPI_Reduce(&mine, &total, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
   MPI_Allreduce(&mine, &total2, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
   /* print in rank order so the output is deterministic */
   for (int r = 0; r < size; r++) {
      if (r == rank) printf("rank %d: Reduce total = %d, Allreduce total = %d\n", rank, total, total2);
      fflush(stdout);
      MPI_Barrier(MPI_COMM_WORLD);
   }
   MPI_Finalize();
   return 0;
}
