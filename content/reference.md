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
    MPI_Sendrecv(sendbuf, scount, stype, dest, stag,
                 recvbuf, rcount, rtype, source, rtag, comm, &status);
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
    MPI_Gatherv(send, send_count, send_type, recv, recv_counts, displs, recv_type, dest, comm);
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

- Odd-even sort (lecture 12):
    - Partner: even phase, even rank + 1 and odd rank - 1. Odd phase, even rank - 1 and odd rank + 1
    - Partner outside 0 to p - 1 means idle that phase
    - Compare-split: merge the two sorted blocks, the lower rank keeps the low half
    - At most p phases with p ranks
    - Exchange with `MPI_Sendrecv`, never Send then Send

- Heat diffusion (lecture 13):
    - `updatable_rows = N - 2`, `base = updatable_rows / p`, `rem = updatable_rows % p`
    - `row_count[r] = base + (r < rem ? 1 : 0)`, `row_start[0] = 1`
    - Local array is `(my_rows + 2) x N`, local rows 0 and `my_rows + 1` are ghosts
    - `global_row = row_start - 1 + local_row`
    - `up = rank 0 ? MPI_PROC_NULL : rank - 1`, `down = last rank ? MPI_PROC_NULL : rank + 1`
    - Gatherv: `recv_counts[r] = row_count[r] * N`, `displs[r] = row_start[r] * N`
    - Convergence: `MPI_Allreduce(&local_max, &global_max, 1, MPI_DOUBLE, MPI_MAX, comm)`

- Performance (lecture 14):
    - Speedup `S = T_serial / T_parallel`, linear speedup is `S = p`
    - Efficiency `E = S / p`
    - Overhead: `T_parallel = T_serial / p + T_overhead`
    - Amdahl: `S = 1 / (parallel / p + serial)`, maximum `1 / serial`
    - Flynn: SISD, SIMD, MISD, MIMD. UMA same access time, NUMA local is faster

- GPGPU and Warp (lecture 15):
    - One thread per element, `tid = wp.tid()`, kernels write to an output array and return nothing
    - Host steps: NumPy data, `wp.array`, `wp.zeros`, `wp.launch(kernel, dim, inputs, outputs, device)`, `.numpy()`
    - Divergent branches cost the sum of both paths. Copying to the GPU can dominate small problems

- Image processing (lectures 16 and 17):
    - Convolution: `g(x, y) = sum of w(i, j) * f(x + i, y + j)` over the kernel
    - Normalize smoothing kernels by their sum. High-pass kernels sum to 0
    - Processable region for half-width m: `(M - 2m) x (N - 2m)` from (m, m)
    - Unsharp mask: `g = f - blur(f)`, `f_UM = f + k g`, k from 0.2 to 0.7, k > 1 is high-boost
    - Gaussian: `w(i, j) = e^(-(i^2 + j^2) / (2 sigma^2))`, radius 3 sigma
    - Median: sort the neighbourhood, take the middle. Best for impulse noise, keeps edges, removes features under half the window

- Commands:

    ```
    mpicc -g -Wall -std=c99 -o mpi_hello mpi_hello.c
    mpiexec -n 4 ./mpi_hello
    echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast
    mpicc -O2 -Wall -o heatDiffusionMpi heatDiffusionMpi.c -lm
    mpirun -np 4 ./heatDiffusionMpi 16 6 1e-4 50000 1 frames txt
    mpiexec -n 4 ./mpi_odd_even g 16
    python3 arrAdd.py
    ```
