title: mpi_hello2.c

- What changed from mpi_hello.c:
    - Each sender picks a random tag
    - [[r0]] receives with wildcards, then asks the `status` object who sent it, which tag it had, and how many elements arrived
    - Textbook reference: 3.1.9 and 3.1.10 (message matching and the status argument)

- The code (lines 45 to 70):

    {{code mpi_hello2.c 45-70 hl=49,50,53,59,60,61,62,64,65}}

- Line by line:
    - Line 49: `srand(my_rank)` seeds the random generator with the rank, so each rank gets its own number
    - Line 50: `tag = rand() % 50` is a tag from 0 to 49
    - Line 53: [[rx]] send the greeting using that tag, the only change on the sender side
    - Line 59: [[r0]] declares an `MPI_Status` to hold information about each message
    - Line 60: the receive says `MPI_ANY_SOURCE` and `MPI_ANY_TAG`, so it takes whichever message arrives first
    - Lines 61 and 62: `status.MPI_SOURCE` and `status.MPI_TAG` are the sender's rank and the tag it used
    - Line 64: `MPI_Get_count` fills `count` with the number of `MPI_CHAR` elements received
    - Lines 65 and 68: first the info line, then the greeting text itself

- Output with `mpiexec -n 4 ./mpi_hello2` (one real run):

        Greetings from process 0 of 4!
        Received a message from process 1 with tag 33: 31 elements
        Greetings from process 1 of 4!
        Received a message from process 2 with tag 40: 31 elements
        Greetings from process 2 of 4!
        Received a message from process 3 with tag 46: 31 elements
        Greetings from process 3 of 4!

    - The tags 33, 40, 46 come from this machine's `rand()`, so other systems can print other tags
    - The order of the three "Received" blocks can change between runs, because `MPI_ANY_SOURCE` takes whoever arrives first
    - Each block is one receive, so the info line and the greeting always stay together

- Why the count is 31:
    - The text is "Greetings from process 1 of 4!" which is 30 characters
    - Plus the `'\0'` sent by `strlen(greeting)+1` makes 31 elements
    - For rank 10 of 12 the text is 32 characters, so the count would be 33

- Why this program needs `status`:
    - With wildcards, the receiver does not know who sent the message, which tag it had, or how long it was
    - **status** is how it finds out
    - Count is not a field of the status, because it depends on the datatype, so `MPI_Get_count` computes it

- Notes:
    - The comment at the top of the file still says `mpi_hello.c`, and the makefile does not build this program
    - Compile it yourself with `mpicc -std=c99 -Wall -o mpi_hello2 mpi_hello2.c`
