title: Collective communication

- Two kinds of communication:
    - **point-to-point**: two processes, using `MPI_Send` and `MPI_Recv`
    - **collective**: every process in a communicator takes part
    - Lecture 10 groups them by shape: 1-to-N (broadcast), N-to-1 (reduction), N-to-N (all-reduce)

- Rules that differ from point-to-point (textbook 3.4.3):
    - Every process in the communicator must call the same collective function
    - Matching a `MPI_Reduce` on one process with a `MPI_Recv` on another is erroneous and likely hangs or crashes
    - The arguments must be compatible on every process, for example the same destination rank
    - The output argument is only used on the destination process, but every process must still pass something (`NULL` is fine)
    - There are no tags, calls match by communicator and by the **order** the calls are made
    - Never use the same variable as both input and output: `MPI_Reduce(&x, &x, ...)` is illegal because MPI forbids aliasing an output argument

- Why order matters (textbook Table 3.3):
    - Every process calls `MPI_Reduce` with `MPI_SUM` and destination 0
    - Rank 1 reduces `c` first then `a`, the other ranks reduce `a` first then `c`
    - With `a = 1` and `c = 2` everywhere, the first call combines `c` from rank 1 with `a` from the others
    - So `b` ends up as 1 + 2 + 1 = 4 and `d` as 2 + 1 + 2 = 5 on three processes
    - Variable names never matter for matching, only call order does
    - `reduce_order.c` in `examples/extras/` prints `b = 4, d = 5`

- Why collectives exist (the tree idea):
    - A loop where rank 0 receives from everyone makes rank 0 do p - 1 receives one after another
    - A **tree-structured** sum lets pairs of processes combine at the same time
    - With 8 processes, ranks 1, 3, 5, 7 send to 0, 2, 4, 6 in round one
    - Then ranks 2 and 6 send to 0 and 4, and finally rank 4 sends to 0
    - That is 3 rounds, which is log2 of 8
    - MPI implementers tune the tree to the hardware, so you do not have to
    - Lecture 10's picture is an example, a real implementation may shape the tree differently

- MPI_Reduce:
    - Signature:

        ```c
        MPI_Reduce(input_data, output_data, count, datatype, operator, dest_process, comm);
        ```

    - Every process contributes `input_data`, and the combined result lands in `output_data` on `dest_process`
    - With `count` greater than 1 it combines arrays element by element, for example adding vectors
    - The operator says how to combine: `MPI_SUM`, `MPI_PROD`, `MPI_MIN`, `MPI_MAX`, and logical or bitwise AND, OR, XOR
    - `MPI_MAXLOC` and `MPI_MINLOC` also return where the extreme value was
    - Used in the trapezoid program:

        ```c
        MPI_Reduce(&local_int, &total_int, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
        ```

    - This one call replaces the whole loop of receives on rank 0
    - After it, `total_int` only holds the answer on rank 0

- MPI_Allreduce:
    - Same arguments as `MPI_Reduce` but with no `dest_process`

        ```c
        MPI_Allreduce(&tmpVal, &sum, 1, MPI_DOUBLE, MPI_SUM, comm);
        ```

    - Every process receives the combined result
    - The lecture calls it a **butterfly reduce** and draws it as a tree sum followed by the same tree run backwards
    - The textbook shows two ways to build it: reverse the tree, or have processes exchange partial results in pairs (a true butterfly)
    - Use it when every process needs the total for its next step
    - `allreduce_demo.c` on 4 processes: rank 0 to 3 each contribute rank + 1, and every rank prints an Allreduce total of 10

- MPI_Bcast:
    - Signature:

        ```c
        MPI_Bcast(data, count, datatype, source, comm);
        ```

    - The process with rank `source` sends, every other process receives into the same argument
    - So `data` is an input on the source and an output everywhere else
    - It is the reverse of a tree sum, so it is also fast
    - In `Get_input`, only rank 0 calls `scanf`, but all ranks call `MPI_Bcast`
    - The three `MPI_Bcast` calls sit outside the `if (my_rank == 0)` block on purpose

- MPI_Scatter and MPI_Gather (lecture 10):
    - **Scatter** splits an array on one process and gives each process a different chunk
    - **Gather** is the reverse: it collects one chunk from every process into one array on a destination process
    - Signatures:

        ```c
        MPI_Scatter(send_data, send_count, send_type, recv_data, recv_count, recv_type, src_process, comm);
        MPI_Gather(send_data, send_count, send_type, recv_data, recv_count, recv_type, dest_process, comm);
        ```

    - `send_count` in Scatter is the number of elements sent to **each** process, not the length of the whole array
    - The lecture says those arguments "describe the full array", but passing the total makes MPI abort with "Message truncated" (tested in `scatter_total.c`)
    - The send buffer only matters on the source, but every process supplies a receive buffer
    - Gather puts rank 0's chunk first, then rank 1's, and so on
    - `scatter_gather.c`: scatter 1..8, multiply by 10, gather, and rank 0 prints `10 20 30 40 50 60 70 80`
    - The lecture says both will be used in the odd-even sort that comes next

- Other collectives in the textbook summary:
    - `MPI_Allgather`: like Gather but every process gets the whole array
    - `MPI_Barrier`: no process returns until every process in the communicator has started the call
    - Scatter hands out the first n/p elements to process 0, the next n/p to process 1, and so on
    - That is a **block** distribution, and the textbook also describes **cyclic** (round robin) and **block-cyclic**
