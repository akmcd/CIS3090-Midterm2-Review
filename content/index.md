title: Start here

- What this site is:
    - Study notes for the CIS*3090 midterm, built around reading and predicting MPI code
    - **MPI** (Message Passing Interface): a C library for running one program as several cooperating processes
    - Every program output shown here was produced by compiling and running the code with MPICH
    - Extra demo programs that are not from the course sit in `examples/extras/`

- What is covered so far:
    - **Lecture 09**: distributed memory systems, MPI basics, send and receive
    - **Lecture 10**: collective communication (Reduce, Allreduce, Bcast, Scatter, Gather)
    - **Lecture 11**: the trapezoidal rule, first with Send/Recv, then with Bcast and Reduce
    - **Textbook**: Chapter 3, sections 3.1 to 3.4
    - **Code**: `mpi_hello.c`, `mpi_hello2.c`, `mpi_SendRec.c`, `mpi_Bcast.c` and the makefile
    - Earlier lectures (pthreads, performance, heat distribution) are not on this site yet

- A good study order:
    - Read Big ideas, then Send and receive, then Collective communication
    - Open each code walkthrough and try to predict the output before reading it
    - Play with the trapezoid trace until the rank slices feel obvious
    - Finish with the code-reading questions, covering the answers until you have committed to one

- How rank colours work:
    - Every MPI process has a number called its **rank**
    - This site gives each rank a colour: [[r0]] [[r1]] [[r2]] [[r3]] and [[rx]] for any rank not named
    - Code walkthroughs use the colour to say which ranks run which lines

- Two things in the zip that can trip you up:
    - `mpi_SendRec.c` is the textbook's `mpi_trap2.c`, and `mpi_Bcast.c` is `mpi_trap3.c`
    - The comments inside those files still use the old names
    - The makefile builds `mpi_hello`, `mpi_SendRec` and `mpi_Bcast`, but not `mpi_hello2`
    - The trapezoid programs read input from the keyboard, so pipe it in: `echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast`

- Compile and run:
    - `mpicc -std=c99 -Wall -o mpi_hello mpi_hello.c`
    - `mpiexec -n 4 ./mpi_hello`
    - `-n 4` starts four processes
