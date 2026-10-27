title: mpi_hello.c

- What it does:
    - Every rank except 0 builds a greeting string and sends it to rank 0
    - [[r0]] prints its own greeting, then receives and prints the others in rank order
    - Textbook reference: Section 3.1 and lecture 09, slides 13 to 22

- Try this first:
    - Pick Rank 0, then Rank 2, and watch which lines stay lit
    - Press Next step to see the messages in the order they happen
    - Change the number of processes and see how the loop on line 52 follows it

{{walk hello}}

- Output with `mpiexec -n 4 ./mpi_hello`:

    ::: run Real run, 4 processes
    $ mpiexec -n 4 ./mpi_hello
    Greetings from process 0 of 4!
    Greetings from process 1 of 4!
    Greetings from process 2 of 4!
    Greetings from process 3 of 4!
    :::

    - The order is always the same, because only rank 0 prints and it receives from rank 1, then 2, then 3
    - If rank 3 sends first, its message waits until rank 0 asks for it
    - Lecture 09 slide 18 shows a different print on rank 0 ("Process 0 of 4 is ready to receive"); the file here does not

- With one process (`-n 1`):
    - Only `Greetings from process 0 of 1!` is printed
    - The loop on line 52 runs zero times because `comm_sz` is 1

- Things to be able to explain:
    - Number of messages: `comm_sz - 1` sends and the same number of receives
    - Why they must match: a missing send leaves rank 0 waiting forever, a missing receive can hang or lose the message
    - Why the `+1`: without it the string has no terminator when it arrives, so `printf("%s")` can read past the end
    - Why `source` is `q` and not a wildcard: it forces the printed order, which is the next file's contrast
    - Textbook exercise 3.1 asks what happens with `strlen(greeting)` and with `MAX_STRING` as the send length
