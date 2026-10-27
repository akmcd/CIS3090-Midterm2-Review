title: mpi_SendRec.c

- What it is:
    - The textbook's `mpi_trap2.c`: a parallel trapezoidal rule using only `MPI_Send` and `MPI_Recv`
    - Input is read by [[r0]] and sent to everyone, and the partial results are summed by [[r0]] with a loop of receives
    - Textbook reference: 3.2 and 3.3.2, lecture 09 slides 38 to 42 and lecture 11

- The main function:

    {{code mpi_SendRec.c 44-95 hl=59,61,62,67,68,69,72,73,77,78,80,85}}

- Line by line:
    - Lines 45 to 48: `local_a`, `local_b` and `local_int` get a different value on each rank
    - `local_n` is the same number everywhere, but the textbook still calls it a **local** variable, meaning one process uses it
    - `a`, `b`, `n` are the textbook's **global** variables, meaning every process needs the same values
    - Line 59: **every** rank calls `Get_input`, and inside it each rank takes a different branch
    - Lines 61 and 62: `h` and `local_n`, identical on all ranks
    - Lines 67 to 69: each rank computes its own slice and its own partial integral
    - Lines 72 to 74: [[rx]] send `local_int` to rank 0 (one `MPI_DOUBLE`, tag 0)
    - Lines 76 to 81: [[r0]] starts `total_int` with its own part, then receives from rank 1, 2, ... and adds each in turn
    - Lines 85 to 89: only [[r0]] prints the result

- The input function (lines 107 to 127):

    {{code mpi_SendRec.c 107-127 hl=111,112,113,115,116,117,120,122,124}}

    - [[r0]] prompts, reads `a`, `b`, `n` with one `scanf`, then loops over every other rank sending three messages to each
    - [[rx]] do three receives from rank 0 in the same order: `a`, then `b`, then `n`
    - All six calls use tag 0 and the same communicator, and that is safe because messages from the same sender do not overtake each other
    - The types must line up: `a` and `b` are `MPI_DOUBLE`, `n` is `MPI_INT`
    - Swapping the receives for `a` and `b` would silently swap their values, since both are doubles
    - Swapping the receive for `n` with one of those would be a type mismatch

- Running it (the program asks for keyboard input, so pipe it in):

        $ echo "0 3 1024" | mpiexec -n 4 ./mpi_SendRec
        Enter a, b, and n
        With n = 1024 trapezoids, our estimate
        of the integral from 0.000000 to 3.000000 = 9.000004291534424e+00

    - This is a real run, and the true answer is 9
    - The estimate is slightly high because x squared is convex

- Counting messages for p processes:
    - Input: 3 sends to each of the other p - 1 ranks, which is 3(p - 1)
    - Results: one message from each other rank, which is p - 1
    - Total: 4(p - 1) messages, and all of them go through rank 0
    - For p = 4 that is 12 messages
    - Rank 0 handles these one after another, which is the bottleneck that collectives fix

- Things to check yourself on:
    - Why does the sum loop receive from `source` in rank order, and what does that mean for the floating-point result?
    - What happens if the ranks other than 0 never call `Get_input`?
    - What goes wrong if `n` is not divisible by `comm_sz`? (See The trapezoidal rule)
    - The header comment says Compile `mpi_trap2`, the makefile target is `mpi_SendRec`
