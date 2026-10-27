#include <stdio.h>
#include <mpi.h>
/* Textbook Table 3.3: collective calls match by ORDER, not by variable name */
int main(void) {
   int rank, a = 1, b = 0, c = 2, d = 0;
   MPI_Init(NULL, NULL);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   if (rank == 1) {
      MPI_Reduce(&c, &d, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(&a, &b, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
   } else {
      MPI_Reduce(&a, &b, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
      MPI_Reduce(&c, &d, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
   }
   if (rank == 0) printf("b = %d, d = %d\n", b, d);
   MPI_Finalize();
   return 0;
}
