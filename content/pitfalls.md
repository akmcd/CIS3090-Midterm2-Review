title: Hangs and mix-ups

- How to use this page:
    - Each program below is short and goes wrong in a different way
    - Read the code and use the lens first, and guess what will happen before you step through
    - These programs are not from the course; they are in `examples/extras/`, and each result was checked by running it

- Program 1, a tag that does not match:
    - Guess first: two processes, one send, one receive, same source and communicator. Does it print `got 42`?

{{walk tag_mismatch}}

- What happens in program 1:

    ::: run Real run, 2 processes (killed after a timeout)
    $ mpiexec -n 2 ./tag_mismatch
    (no output, the program hangs)
    :::

    - A receive only accepts a message whose communicator, source and tag all match
    - Rank 1's send may finish anyway, because small messages are usually buffered by the system
    - Fix: use the same tag on both sides, or receive with `MPI_ANY_TAG`

- Program 2, two sends facing each other:
    - Guess first: both ranks send to the other and then receive. Is that safe?

{{walk head_to_head}}

- What happens in program 2:

    ::: run Real run, 2 processes (killed after a timeout)
    $ mpiexec -n 2 ./head_to_head
    (no output, the program hangs)
    :::

    - **deadlock**: each rank waits for something only the other rank could do
    - With `MPI_Send` instead of `MPI_Ssend` this might appear to work, because the message could be buffered
    - That is why it is called **unsafe**: it works only if the system happens to buffer
    - The safety check is to replace `MPI_Send` with `MPI_Ssend` and see if it still finishes
    - Fix: even ranks send first and odd ranks receive first, or use `MPI_Sendrecv`

- Program 3, collectives match by order, not by name:
    - Guess first: rank 1 calls the two reductions in the opposite order. What are `b` and `d` on rank 0?

{{walk reduce_order}}

- What happens in program 3:

    ::: run Real run, 3 processes
    $ mpiexec -n 3 ./reduce_order
    b = 4, d = 5
    :::

    - Both calls on each rank are `MPI_Reduce` with `MPI_SUM` and root 0, so MPI matches the 1st with the 1st and the 2nd with the 2nd
    - The first call adds rank 1's `c` (2) to the others' `a` (1 each): 2 + 1 + 1 = 4, stored in rank 0's `b`
    - The second call adds rank 1's `a` (1) to the others' `c` (2 each): 1 + 2 + 2 = 5, stored in rank 0's `d`
    - This is textbook Table 3.3

- Takeaway:
    - A hang almost always means one side is waiting for something that never comes
    - Look for the call whose partner (matching send, receive or collective) does not exist
