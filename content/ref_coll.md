title: Collective functions

- What makes a call collective:
    - Every process in the communicator must make the call
    - The arguments must be compatible on every process, for example the same root rank
    - There are no tags, so calls match by communicator and by the order they are made
    - Output arguments must not be the same variable as input arguments (aliasing is illegal)
    - Matching a collective on one process with a `MPI_Recv` on another is an error
    - The Collective communication page explains this with a lab

::: fn MPI_Bcast
Copies data from one process to every other process.

```c
int MPI_Bcast(void* data_p, int count, MPI_Datatype datatype,
              int source_proc, MPI_Comm comm);
```

| Argument | Meaning |
|---|---|
| `data_p` | input on `source_proc`, output on every other process |
| `count` | number of elements |
| `datatype` | type of each element |
| `source_proc` | rank that holds the data |
| `comm` | the communicator |

- Every process makes the same call, including the source
- Putting it inside `if (my_rank == 0)` is a bug, because the other ranks never take part
- Used in the course: `mpi_Bcast.c` lines 103 to 105
:::

::: fn MPI_Reduce
Combines one value from every process into a single result on one process.

```c
int MPI_Reduce(const void* input_data_p, void* output_data_p, int count,
               MPI_Datatype datatype, MPI_Op operator, int dest_process, MPI_Comm comm);
```

| Argument | Meaning |
|---|---|
| `input_data_p` | this process's contribution |
| `output_data_p` | where the result goes, only used on `dest_process` |
| `count` | number of elements; with more than 1 it combines arrays element by element |
| `datatype` | type of each element |
| `operator` | how to combine, like `MPI_SUM` |
| `dest_process` | rank that receives the result |
| `comm` | the communicator |

- Every process must pass an `output_data_p`, but only the destination's is written (`NULL` is fine elsewhere)
- `MPI_Reduce(&x, &x, ...)` is illegal, because the input and output are the same variable
- A tree lets pairs combine at the same time, so p processes need about log2(p) rounds instead of p - 1 receives in a row
- Used in the course: `mpi_Bcast.c` lines 70 and 71
:::

::: fn MPI_Allreduce
Like `MPI_Reduce`, but every process gets the result.

```c
int MPI_Allreduce(const void* input_data_p, void* output_data_p, int count,
                  MPI_Datatype datatype, MPI_Op operator, MPI_Comm comm);
```

- It has no destination argument, because the destination is everyone
- Use it when every process needs the total for its next step
- The lecture calls it a **butterfly reduce**: a tree sum followed by the same tree run backwards
- Used in this site: `allreduce_demo.c` in `examples/extras/`
:::

::: fn MPI_Scatter
Splits an array on one process and gives each process a different chunk.

```c
int MPI_Scatter(const void* send_buf_p, int send_count, MPI_Datatype send_type,
                void* recv_buf_p, int recv_count, MPI_Datatype recv_type,
                int src_proc, MPI_Comm comm);
```

| Argument | Meaning |
|---|---|
| `send_buf_p` | the whole array, only used on `src_proc` |
| `send_count` | elements sent to each process, not the length of the whole array |
| `recv_buf_p` | where this process's chunk goes |
| `recv_count` | elements received by each process |
| `src_proc` | rank that holds the array |

- Rank 0 gets the first chunk, rank 1 the next, and so on (a **block** distribution)
- Passing the total length as `send_count` makes MPI abort with "Message truncated"
- Used in this site: `scatter_gather.c` in `examples/extras/`
:::

::: fn MPI_Gather
Collects one chunk from every process into one array on a single process.

```c
int MPI_Gather(const void* send_buf_p, int send_count, MPI_Datatype send_type,
               void* recv_buf_p, int recv_count, MPI_Datatype recv_type,
               int dest_proc, MPI_Comm comm);
```

- It is the reverse of `MPI_Scatter`
- Rank 0's chunk goes first, then rank 1's, and so on
- `recv_count` is the number of elements from each process, not the total
- `recv_buf_p` is only used on `dest_proc`
:::

::: fn MPI_Allgather
Like `MPI_Gather`, but every process receives the whole array.

```c
int MPI_Allgather(const void* send_buf_p, int send_count, MPI_Datatype send_type,
                  void* recv_buf_p, int recv_count, MPI_Datatype recv_type, MPI_Comm comm);
```

- It has no destination argument
- Every process needs a receive buffer big enough for all the chunks
:::

::: fn MPI_Barrier
Makes every process wait until all of them have reached the call.

```c
int MPI_Barrier(MPI_Comm comm);
```

- No process returns from it until every process in the communicator has started it
- It is mostly used for timing and for ordering output while debugging
:::
