title: Understand MPI code by following every rank

{{home}}

- What this site is for:
    - Each code page shows the program as plain code. Pick a rank to see which lines it runs
    - Press Next step to follow the messages one send or receive at a time
    - Press the i button on a line to read what it does
    - **MPI** (Message Passing Interface): a C library for running one program as several cooperating processes
    - Every output shown here came from compiling and running the code (MPICH for lectures 09 to 11, Open MPI for the heat program, Warp 1.16 for the GPU example)
    - Lectures 12 to 17 each have a Learn page, and there is a second question page for them

- What is covered so far:
    - **Lecture 09**: distributed memory systems, MPI basics, send and receive
    - **Lecture 10**: collective communication (Reduce, Allreduce, Bcast, Scatter, Gather)
    - **Lecture 11**: the trapezoidal rule, first with Send/Recv, then with Bcast and Reduce
    - **Lecture 12**: odd-even sort for distributed memory (`MPI_Sendrecv`, deadlock with `MPI_Ssend`)
    - **Lecture 13**: heat distribution for distributed memory (ghost rows, `MPI_PROC_NULL`, `MPI_Allreduce`, `MPI_Gatherv`)
    - **Lecture 14**: parallel hardware and performance (Flynn, UMA and NUMA, speedup, efficiency, Amdahl's law)
    - **Lecture 15**: GPGPU and Nvidia Warp
    - **Lectures 16 and 17**: image processing, convolution, sharpening, smoothing and the median filter
    - **Textbook**: Chapter 2, sections 2.3 and 2.6.1 to 2.6.2, and Chapter 3, sections 3.1 to 3.4
    - **Code**: `mpi_hello.c`, `mpi_hello2.c`, `mpi_SendRec.c`, `mpi_Bcast.c`, the makefile and `heatDiffusionMpi.c`
    - `mpi_odd_even.c` and the Warp example `arrAdd.py` were not in the project files, so those pages use the slide code
    - The pthreads lectures (01 to 08) are not on this site

- A good study order:
    - Big ideas, then Reading MPI code, which is the routine to use on every exam question
    - Send and receive, then Collective communication, and try the lab on each page
    - Open each code page and predict the output before you read the notes
    - Finish with Hangs and mix-ups and the code-reading questions
    - For lectures 12 to 17: read the Learn page for each lecture, open `heatDiffusionMpi.c`, then try the second question page

- Two things in the zip that can trip you up:
    - `mpi_SendRec.c` is the textbook's `mpi_trap2.c`, and `mpi_Bcast.c` is `mpi_trap3.c`
    - The comments inside those files still use the old names
    - The makefile builds `mpi_hello`, `mpi_SendRec` and `mpi_Bcast`, but not `mpi_hello2`
    - The trapezoid programs read input from the keyboard, so pipe it in: `echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast`

- Compile and run:
    - `mpicc -std=c99 -Wall -o mpi_hello mpi_hello.c`
    - `mpiexec -n 4 ./mpi_hello`
    - `-n 4` starts four processes
