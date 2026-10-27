title: Big ideas

- Shared memory versus distributed memory:
    - **shared memory**: all threads see the same variables (pthreads works this way)
    - **distributed memory**: each process has its own private memory, and processes talk over a network
    - MPI is built for distributed memory
    - The same MPI program also runs on one machine with several cores
    - MPI hides whether two processes share a machine or not

- Why communication cost shapes everything:
    - Sending data over a network takes time, while threads share data almost instantly
    - So MPI pays off when each process computes for a long time between messages
    - It fits **data-parallel** problems, where every process does the same work on a different piece of data
    - Lecture 09's example is a render farm: each machine renders its own animation frame

- MPI compared with pthreads (lecture 09):
    - pthreads: shared memory, works with threads, built for concurrency, so you do all the parallel computation work by hand
    - MPI: distributed memory, works with processes, designed with parallel computation in mind

- SPMD:
    - **SPMD** (single program, multiple data): every process runs the same executable
    - Different processes do different things by branching on their rank
    - The classic shape is `if (my_rank != 0) { send } else { receive }`
    - The textbook (3.1.5) points to the if-else in the hello program as what makes it SPMD

- The calls every MPI program uses:
    - `MPI_Init(NULL, NULL)`: starts MPI, must come before any other MPI call
    - `NULL, NULL` is fine when the program does not use `argc` and `argv`
    - `MPI_Comm_size(MPI_COMM_WORLD, &comm_sz)`: stores how many processes there are
    - `MPI_Comm_rank(MPI_COMM_WORLD, &my_rank)`: stores which process this is, from 0 to `comm_sz - 1`
    - `MPI_Finalize()`: shuts MPI down, no MPI calls are allowed after it

- Two words to know:
    - **communicator**: a group of processes that can send messages to each other
    - `MPI_COMM_WORLD` is the communicator holding every process that `mpiexec` started
    - **rank**: a process's number inside a communicator, like a process id that does not depend on the system
    - Lecture 09 compares a communicator to a radio channel that processes listen on
    - Several communicators let different groups talk without picking up each other's messages

- Compile and run:
    - `mpicc` is a wrapper around the C compiler that adds the MPI library
    - `mpiexec -n 4 ./prog` starts 4 processes of `prog`
    - Write programs that work for any number of processes, because you do not know the number in advance

- Naming rule from the textbook (3.1.2):
    - Everything MPI defines starts with `MPI_`
    - Function names and types have a capital letter right after the underscore
    - Constants and macros are all capitals, like `MPI_COMM_WORLD`

- Input and output:
    - Most implementations let only rank 0 read from stdin
    - So rank 0 calls `scanf`, then sends the values to everyone else
    - Every process can write to stdout, but the order is nondeterministic and lines can interleave
    - **nondeterministic**: the result can differ from one run to the next
    - To get ordered output, have the other ranks send their text to rank 0, which prints in rank order
    - `mpi_hello.c` does exactly this
    - Debug prints should include the rank

- Error codes:
    - Most MPI functions return an `int`, and `MPI_SUCCESS` means it worked
    - The course examples ignore the return values to keep code short
