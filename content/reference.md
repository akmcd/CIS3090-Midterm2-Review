title: Cheat sheet

- Setup and shutdown:

    ```c
    MPI_Init(NULL, NULL);                          /* before any other MPI call */
    MPI_Comm_size(MPI_COMM_WORLD, &comm_sz);       /* how many processes */
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);       /* which one am I */
    MPI_Finalize();                                /* no MPI calls after this */
    ```

- Point-to-point:

    ```c
    MPI_Send(buf, count, datatype, dest,   tag, comm);
    MPI_Recv(buf, count, datatype, source, tag, comm, &status);   /* or MPI_STATUS_IGNORE */
    MPI_Get_count(&status, datatype, &count);
    ```

    - Recv `count` is the buffer capacity, it must be at least the size of the message
    - Wildcards `MPI_ANY_SOURCE` and `MPI_ANY_TAG` are receiver only
    - `status.MPI_SOURCE`, `status.MPI_TAG` tell you what a wildcard receive matched

- Collective:

    ```c
    MPI_Bcast(data, count, datatype, source, comm);
    MPI_Reduce(in, out, count, datatype, op, dest, comm);
    MPI_Allreduce(in, out, count, datatype, op, comm);
    MPI_Scatter(send, send_count, send_type, recv, recv_count, recv_type, source, comm);
    MPI_Gather(send, send_count, send_type, recv, recv_count, recv_type, dest, comm);
    ```

    - `send_count` in Scatter and Gather is per process, not the total
    - Every process in the communicator must make the call, in the same order
    - Reduce output is only written on `dest`, and input and output must not be the same variable

- Datatypes used in the examples:
    - `MPI_CHAR` for `char`, `MPI_INT` for `int`, `MPI_DOUBLE` for `double`
    - The MPI type must match the C type of the variable

- Reduction operators (textbook Table 3.2):

| Operator | Meaning |
|---|---|
| `MPI_SUM`, `MPI_PROD` | sum, product |
| `MPI_MAX`, `MPI_MIN` | maximum, minimum |
| `MPI_MAXLOC`, `MPI_MINLOC` | extreme value and where it is |
| `MPI_LAND`, `MPI_LOR`, `MPI_LXOR` | logical and, or, exclusive or |
| `MPI_BAND`, `MPI_BOR`, `MPI_BXOR` | bitwise and, or, exclusive or |

- Point-to-point against collective:

| | Point-to-point | Collective |
|---|---|---|
| Who takes part | one sender, one receiver | all processes in the communicator |
| Matched by | communicator, tag, source and dest | communicator and order of calls |
| Tags | yes | no |
| Wildcards | receiver only | none |

- Four ways code hangs or goes wrong:
    - Receive with no matching send
    - Tag, rank or communicator mismatch
    - Two blocking sends facing each other
    - A collective that not every process calls, or that is called in a different order

- Trapezoid formulas:
    - `h = (b - a) / n`
    - `local_n = n / comm_sz` (assumes n divides evenly)
    - `local_a = a + my_rank * local_n * h`
    - `local_b = local_a + local_n * h`
    - Estimate: `h * (f(a)/2 + f(x_1) + ... + f(x_n-1) + f(b)/2)`

- Commands:

    ```
    mpicc -g -Wall -std=c99 -o mpi_hello mpi_hello.c
    mpiexec -n 4 ./mpi_hello
    echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast
    ```
