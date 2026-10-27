#include <stdio.h>
#include <mpi.h>
/* Both ranks Ssend first, then Recv: unsafe. Uses MPI_Ssend to force blocking behaviour */
int main(void) {
   int rank, mine = 1, other = 0;
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   int partner = 1 - rank;
   MPI_Ssend(&mine, 1, MPI_INT, partner, 0, MPI_COMM_WORLD);
   MPI_Recv(&other, 1, MPI_INT, partner, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
   printf("rank %d done\n", rank);
   MPI_Finalize();
   return 0;
}
