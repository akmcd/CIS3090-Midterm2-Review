all: mpi_hello mpi_SendRec mpi_Bcast

mpi_hello: mpi_hello.c
	mpicc mpi_hello.c -o mpi_hello

mpi_SendRec: mpi_SendRec.c
	mpicc mpi_SendRec.c -o mpi_SendRec

mpi_Bcast: mpi_Bcast.c
	mpicc mpi_Bcast.c -o mpi_Bcast

clean:
	rm mpi_hello mpi_SendRec mpi_Bcast
