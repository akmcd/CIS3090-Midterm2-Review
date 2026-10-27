title: Send and receive

- **Point-to-point communication**: one process sends, exactly one process receives
    - The two functions are `MPI_Send` and `MPI_Recv`

- MPI_Send:
    - Signature:

        ```c
        int MPI_Send(const void* buf, int count, MPI_Datatype datatype,
                     int dest, int tag, MPI_Comm comm);
        ```

    - `buf`, `count`, `datatype` describe the data: where it is, how many elements, what type
    - `count` is a number of elements, not bytes
    - `dest`, `tag`, `comm` describe where it goes
    - `tag` is a non-negative int that lets a receiver tell kinds of messages apart
    - The textbook's example: tag 0 for messages to print, tag 1 for messages used in a computation
    - `MPI_Send(greeting, strlen(greeting)+1, MPI_CHAR, 0, 0, MPI_COMM_WORLD)` sends a string to rank 0
    - The `+1` sends the terminating `'\0'` too

- MPI_Recv:
    - Signature:

        ```c
        int MPI_Recv(void* buf, int count, MPI_Datatype datatype,
                     int source, int tag, MPI_Comm comm, MPI_Status* status);
        ```

    - The first six arguments mirror `MPI_Send`
    - Here `count` is how many elements the buffer can hold, not how many arrived
    - `status` receives details about the message, or pass `MPI_STATUS_IGNORE`
    - The receiver must already know the type, and an upper limit on the size

- Message matching:
    - A send from process q to process r is received by r's `MPI_Recv` when all of these hold
    - Both use the same communicator
    - The tags are equal
    - r's `source` is q, and q's `dest` is r
    - The buffers are compatible: same datatype, and the receive count is at least the send count (the textbook's rule of thumb)

- Try the matching rules:
    - Change one thing at a time and see which check fails
    - The presets reproduce programs in `examples/extras/`

{{lab match}}

- Wildcards (receiver only):
    - `MPI_ANY_SOURCE`: accept a message from any sender
    - `MPI_ANY_TAG`: accept any tag
    - Use `MPI_ANY_SOURCE` when you do not know which process will finish first
    - A sender can never use a wildcard, it must name a rank and a non-negative tag
    - The textbook calls this a "push" mechanism, not a "pull"
    - There is no wildcard for the communicator

- Finding out what a wildcard receive got:
    - `status.MPI_SOURCE`: the sender's rank
    - `status.MPI_TAG`: the tag
    - `MPI_Get_count(&status, MPI_CHAR, &count)`: how many elements arrived
    - The count is not a struct member because it depends on the datatype, and computing it costs a little

- Does a send wait?:
    - `MPI_Recv` always blocks until a matching message has arrived
    - **blocking**: the call does not return until it can
    - `MPI_Send` depends on the implementation: it may copy the message into a system buffer and return at once, or wait until the receiver is ready
    - Implementations usually pick a cutoff size, small messages are buffered and large ones block
    - When `MPI_Send` returns, you only know your send buffer is safe to reuse, not that the message arrived
    - Lecture 09 slide 29 calls `MPI_Send` synchronous, but slide 34 and the textbook say it may buffer or block, so the buffer-or-block answer is the safe one
    - `MPI_Isend` and `MPI_Irecv` are non-blocking versions, and the course does not use them

- Message order:
    - MPI messages are **non-overtaking**: two messages from the same sender to the same receiver arrive in the order they were sent
    - Messages from different senders have no guaranteed order
    - This is why `Get_input` can send `a`, `b`, `n` with the same tag and still have them arrive in order

- Classic pitfalls (all likely exam material):
    - A receive with no matching send hangs forever
    - A tag or rank mismatch makes the receive hang, or match the wrong send
    - A blocking send with no matching receive can hang
    - A buffered send with no matching receive loses the message
    - The number of sends must equal the number of receives
    - `tag_mismatch.c` in `examples/extras/` shows the hang, and it really does hang when run

- Checking and fixing an unsafe program:
    - **unsafe**: it only works if the system happens to buffer the messages
    - Test by replacing every `MPI_Send` with `MPI_Ssend`, which always waits until the receive has started
    - If the program still finishes, it is safe
    - Fix one way: even ranks send first and odd ranks receive first
    - Fix another way: use `MPI_Sendrecv`, which schedules the send and receive so they cannot deadlock
    - `head_to_head.c` in `examples/extras/` has two ranks that each `MPI_Ssend` before receiving, and it hangs
