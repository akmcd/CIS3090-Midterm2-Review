title: Reading MPI code

- Why a routine helps:
    - Every code question is the same question in different clothes: what does each rank do, and do the messages line up?
    - Doing the same steps in the same order stops you from reading the code top to bottom as if one process ran it

- Step 1, fix the number of processes:
    - Use the number in the question, or pick a small one like 3 or 4
    - Write down every rank: 0, 1, 2, and so on
    - If the question says "for any number of processes", check p = 1 and p = 2 as well

- Step 2, split the code by rank:
    - Find every `if (my_rank ...)` and decide which ranks take each branch
    - Lines outside any branch run on every rank
    - On the code pages, picking a rank in the lens does this for you, so use it to check your own answer

- Step 3, list the communication each rank makes:
    - For each rank, write its calls in order: `Send to 0, tag 0` or `Recv from 1, tag 0`
    - Loops count: a loop `for (q = 1; q < comm_sz; q++)` on rank 0 is `comm_sz - 1` calls
    - A collective is one call on every rank, so it goes on every rank's list

- Step 4, match them up:
    - A send and a receive match when the communicator, the tag, the source and the destination all agree
    - The datatypes must agree too, and the receive count must be at least the send count
    - Collectives match by the order they are made, so check that every rank has the same sequence
    - Every send needs exactly one receive, and every receive needs exactly one send
    - The Send and receive page has a lab for this step

- Step 5, ask whether anything waits forever:
    - A receive with no matching send waits forever
    - Two ranks that both do a blocking send first and then a receive can wait on each other
    - A collective that one rank skips leaves the others waiting
    - **deadlock**: a set of processes each waiting for something only another waiting process could provide

- Step 6, predict the output:
    - Only print statements produce output, so find which ranks reach each `printf`
    - If just one rank prints, the order is fixed
    - If several ranks print, the order can change from run to run, so say "any order"
    - If rank 0 prints what it received in a loop, the order follows the loop (the source it asks for)

- Try the routine on this program:

    ```c
    if (rank == 1) MPI_Send(&x, 1, MPI_INT, 0, 5, MPI_COMM_WORLD);
    if (rank == 0) MPI_Recv(&y, 1, MPI_INT, 1, 7, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    ```

    - Step 2: rank 1 runs the send, rank 0 runs the receive, and any other rank runs nothing
    - Step 3: rank 1 has `Send to 0, tag 5`, rank 0 has `Recv from 1, tag 7`
    - Step 4: the source and destination agree, but the tags (5 and 7) do not
    - Step 5: rank 0 waits forever, so the program hangs
    - The Hangs and mix-ups page shows this exact program

- Takeaway:
    - Split by rank, list each rank's calls, match them, then look for waits
