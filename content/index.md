title: Predict what every rank does

- Try it now on `mpi_hello.c`, run with 4 processes. This is the kind of question the midterm asks.

{{walk hello}}

- What this site is for:
    - Each code page lets you pick a rank and see only the lines that rank runs
    - Each message timeline can be stepped through, one send or receive at a time
    - **MPI** (Message Passing Interface): a C library for running one program as several cooperating processes
    - Every output shown here came from compiling and running the code with MPICH

- What is covered so far:
    - **Lecture 09**: distributed memory systems, MPI basics, send and receive
    - **Lecture 10**: collective communication (Reduce, Allreduce, Bcast, Scatter, Gather)
    - **Lecture 11**: the trapezoidal rule, first with Send/Recv, then with Bcast and Reduce
    - **Textbook**: Chapter 3, sections 3.1 to 3.4
    - **Code**: `mpi_hello.c`, `mpi_hello2.c`, `mpi_SendRec.c`, `mpi_Bcast.c` and the makefile
    - Earlier lectures (pthreads, performance, heat distribution) are not on this site yet

- A good study order:
    - Big ideas, then Reading MPI code, which is the routine to use on every exam question
    - Send and receive, then Collective communication, and try the lab on each page
    - Open each code page and predict the output before you read the notes
    - Finish with Hangs and mix-ups and the code-reading questions

- Two things in the zip that can trip you up:
    - `mpi_SendRec.c` is the textbook's `mpi_trap2.c`, and `mpi_Bcast.c` is `mpi_trap3.c`
    - The comments inside those files still use the old names
    - The makefile builds `mpi_hello`, `mpi_SendRec` and `mpi_Bcast`, but not `mpi_hello2`
    - The trapezoid programs read input from the keyboard, so pipe it in: `echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast`

- Compile and run:
    - `mpicc -std=c99 -Wall -o mpi_hello mpi_hello.c`
    - `mpiexec -n 4 ./mpi_hello`
    - `-n 4` starts four processes

- All pages:

{{map}}
