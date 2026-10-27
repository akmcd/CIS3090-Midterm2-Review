title: mpi_Bcast.c

- What it is:
    - The textbook's `mpi_trap3.c`: the same trapezoidal rule, with the hand-written message loops replaced by collective calls
    - `MPI_Bcast` shares the input and `MPI_Reduce` adds up the partial results
    - Textbook reference: 3.4.2 and 3.4.5, lecture 10 and lecture 11

- The main function:

    {{code mpi_Bcast.c 43-84 hl=57,59,60,65,66,67,70,71,74}}

- What is new compared with mpi_SendRec.c:
    - Line 57: still every rank calls `Get_input`
    - Lines 70 and 71: one `MPI_Reduce` replaces the whole send-or-receive if/else
    - Line 74: only [[r0]] prints, because only rank 0 receives the total

- Reading the MPI_Reduce call:
    - `&local_int`: this rank's partial result, the input
    - `&total_int`: where the combined result goes, only meaningful on the destination
    - `1`: one element
    - `MPI_DOUBLE`: the datatype
    - `MPI_SUM`: add them up
    - `0`: the destination rank
    - `MPI_COMM_WORLD`: every process takes part
    - On [[rx]] `total_int` is never set, so reading it there would give garbage

- The input function:

    {{code mpi_Bcast.c 96-106 hl=99,100,101,103,104,105}}

- Reading the MPI_Bcast calls:
    - Only [[r0]] runs the `if` block, so only rank 0 prompts and calls `scanf`
    - Then every rank calls `MPI_Bcast` three times, once each for `a`, `b`, `n`
    - The fourth argument, 0, is the source rank, the one that already holds the value
    - On rank 0 the buffer is read, on every other rank it is written
    - The three calls match by order, not by name, so every rank must call them in the same order
    - Putting the `MPI_Bcast` calls inside `if (my_rank == 0)` would be a bug, because the other ranks would never take part

- Running it:

        $ echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast
        Enter a, b, and n
        With n = 1024 trapezoids, our estimate
        of the integral from 0.000000 to 3.000000 = 9.000004291534424e+00

    - Same output as `mpi_SendRec`
    - In general the last digits can differ, because the tree in `MPI_Reduce` adds the pieces in a different order than a simple loop

- With 3 processes (`n` not divisible):

        $ echo "0 3 1024" | mpiexec -n 3 ./mpi_Bcast
        Enter a, b, and n
        With n = 1024 trapezoids, our estimate
        of the integral from 0.000000 to 3.000000 = 8.973662840668112e+00

    - Each rank gets 341 trapezoids, so 1023 get covered and the last strip is never computed
    - No error is reported, the answer is just wrong

- Why it is better than mpi_SendRec:
    - Fewer lines of code than the Send/Recv version
    - Four collective calls (three `MPI_Bcast`, one `MPI_Reduce`) replace the loops of sends and receives
    - Lecture 10 says the MPI library chooses an efficient pattern for the machine, so the summing is shared among processes
    - The header comment still says Compile `mpi_trap2`, and the algorithm comment still describes the Send/Recv version
