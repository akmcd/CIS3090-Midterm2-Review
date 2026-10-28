title: Setup and shutdown

- Every MPI program has the same frame:
    - Start MPI, find out how many processes there are and which one this is, do the work, shut MPI down
    - All four functions below are called by every process
    - The order is always Init, then Comm_size and Comm_rank, then your code, then Finalize

::: fn MPI_Init
Starts MPI. It must come before any other MPI call.

```c
int MPI_Init(int* argc_p, char*** argv_p);
```

| Argument | Meaning |
|---|---|
| `argc_p` | pointer to `argc` from `main`, or `NULL` |
| `argv_p` | pointer to `argv` from `main`, or `NULL` |

- Every process calls it
- The course programs pass `NULL, NULL` because they do not read command-line arguments
- Used in the course: `mpi_hello.c` line 35, `mpi_SendRec.c` line 51
:::

::: fn MPI_Comm_size
Finds out how many processes are in a communicator.

```c
int MPI_Comm_size(MPI_Comm comm, int* comm_sz_p);
```

| Argument | Meaning |
|---|---|
| `comm` | the communicator, usually `MPI_COMM_WORLD` |
| `comm_sz_p` | output: where to store the number of processes |

- The number comes from `mpiexec -n 4`, so the same program can run with any count
- Write code that works for any `comm_sz`, because you do not know it when you write the program
- Used in the course: `mpi_hello.c` line 38
:::

::: fn MPI_Comm_rank
Finds out which process this is, as a number from 0 to `comm_sz - 1`.

```c
int MPI_Comm_rank(MPI_Comm comm, int* my_rank_p);
```

| Argument | Meaning |
|---|---|
| `comm` | the communicator, usually `MPI_COMM_WORLD` |
| `my_rank_p` | output: where to store this process's rank |

- Each process gets a different answer, and that is the only thing that makes processes behave differently
- Programs branch on it: `if (my_rank != 0) { ... } else { ... }`
- A rank belongs to a communicator, so the same process can have different ranks in different communicators
- Used in the course: `mpi_hello.c` line 41
:::

::: fn MPI_Finalize
Shuts MPI down and frees what it was using.

```c
int MPI_Finalize(void);
```

- Every process calls it, after its last MPI call
- No MPI function may be called after it
- Used in the course: `mpi_hello.c` line 61

:::

- Names and constants:
    - **communicator**: a group of processes that can send messages to each other
    - `MPI_COMM_WORLD`: the communicator holding every process that `mpiexec` started
    - **rank**: a process's number inside a communicator
    - Everything MPI defines starts with `MPI_`
    - Function names and types have a capital letter right after the underscore, like `MPI_Comm_rank`
    - Constants and macros are all capitals, like `MPI_COMM_WORLD`

- Return values:
    - Most MPI functions return an `int`, and `MPI_SUCCESS` means the call worked
    - The course examples ignore return values to keep the code short

- Compiling and running:
    - `mpicc -std=c99 -Wall -o prog prog.c` compiles with the MPI library
    - `mpiexec -n 4 ./prog` starts 4 processes of `prog`
    - Most systems let only rank 0 read from the keyboard, so pipe input in: `echo "0 3 1024" | mpiexec -n 4 ./prog`
    - Every process can print, but the order of lines from different ranks can change from run to run
