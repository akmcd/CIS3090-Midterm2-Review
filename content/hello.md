title: mpi_hello.c

- What it does:
    - Every rank except 0 builds a greeting string and sends it to rank 0
    - [[r0]] prints its own greeting, then receives and prints the others in rank order
    - Textbook reference: Section 3.1 and lecture 09, slides 13 to 22

- The code:

    {{code mpi_hello.c 23-64 hl=35,38,41,43,48,52,54,61}}

- Line by line:
    - Line 27: `MAX_STRING` is 100, the size of the greeting buffer and also the receive count
    - Lines 35 to 41: set up MPI, then every rank learns `comm_sz` and its own `my_rank`
    - Line 43: the branch that makes this SPMD, [[rx]] go one way and [[r0]] the other
    - Lines 45 to 48: [[rx]] write the message with `sprintf`, then send it to rank 0 with tag 0
    - Line 48: the length is `strlen(greeting)+1` so the terminating `'\0'` travels with the text
    - Line 51: [[r0]] prints its own message directly, it never sends to itself
    - Lines 52 to 57: [[r0]] receives from rank `q` specifically, for q = 1, 2, ... comm_sz - 1
    - Line 54: the receive count is `MAX_STRING`, the buffer capacity, not the message length
    - Line 61: every rank shuts MPI down

- Output with `mpiexec -n 4 ./mpi_hello`:

        Greetings from process 0 of 4!
        Greetings from process 1 of 4!
        Greetings from process 2 of 4!
        Greetings from process 3 of 4!

    - The order is always the same, because only rank 0 prints and it receives from rank 1, then 2, then 3
    - If rank 3 sends first, its message waits until rank 0 asks for it
    - Compare with the lecture slide 18 version, where rank 0 prints "Process 0 of 4 is ready to receive" instead, the file here does not

- With one process (`-n 1`):
    - Only `Greetings from process 0 of 1!` is printed
    - The loop on line 52 runs zero times because `comm_sz` is 1

- Things to be able to explain:
    - Number of messages: `comm_sz - 1` sends and the same number of receives
    - Why they must match: a missing send leaves rank 0 waiting forever, a missing receive can hang or lose the message
    - Why the `+1`: without it the string has no terminator when it arrives, so `printf("%s")` can read past the end
    - Textbook exercise 3.1 asks what happens with `strlen(greeting)` and with `MAX_STRING` as the send length
    - Why `source` is `q` and not a wildcard: it forces the printed order, which is the next file's contrast
