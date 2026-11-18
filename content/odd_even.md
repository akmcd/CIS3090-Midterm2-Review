title: Odd-even sort with MPI

- What lecture 12 is about:
    - The same odd-even transposition sort from the pthreads unit, rewritten for distributed memory
    - Same decomposition, same phases. The one new question: how does a rank get its partner's block when it cannot read that memory?
    - Answer: it receives it in an MPI message, so communication is no longer free
    - The course file `mpi_odd_even.c` is not in the project files yet, so this page uses the code shown on the slides

- The serial algorithm (review):
    - **odd-even transposition sort**: a bubble sort variant split into phases
    - **even phase**: compare-swap the pairs (a[0], a[1]), (a[2], a[3]), ...
    - **odd phase**: compare-swap the pairs (a[1], a[2]), (a[3], a[4]), ...
    - **compare-swap**: if the left value is bigger, swap the two
    - A list of n elements is sorted after at most n phases
    - Slide example: 5 9 4 3, then 5 9 3 4, then 5 3 9 4, then 3 5 4 9, then 3 4 5 9 (4 phases)

- Foster's methodology, one step at a time:
    - **Partitioning**: the smallest task is one compare-swap on a neighbouring pair
    - Inside one phase the pairs do not overlap, so all compare-swaps can run at once
    - Across phases it is serial: phase j must finish before phase j + 1 starts
    - **Communication**: each compare-swap needs both values of its pair
    - In pthreads that was just a read of shared memory
    - In MPI it is a real message: send your block, receive your partner's block
    - This is the step that cannot be copied from the pthreads version
    - **Agglomeration**: group n/p contiguous elements into one block per rank
    - Inside a block, sorting is a local `qsort()`
    - Between blocks, a compare-swap of two numbers becomes a **compare-split** of two sorted blocks
    - **compare-split**: merge the two sorted blocks, the lower rank keeps the low half and the higher rank keeps the high half
    - **Mapping**: block r goes to rank r, so neighbouring blocks stay on neighbouring ranks
    - The example code requires `global_n` to divide evenly by p

- Who is your partner?:
    - It depends on your rank's parity and the phase's parity

| Phase | Even rank | Odd rank |
|---|---|---|
| Even phase | rank + 1 | rank - 1 |
| Odd phase | rank - 1 | rank + 1 |

- Reading the partner table:
    - Even phase with 4 ranks: pairs (0,1) and (2,3), everyone works
    - Odd phase with 4 ranks: only pair (1,2), ranks 0 and 3 are idle
    - If the computed partner is below 0 or at least p, that rank skips the phase: no message, no merge
    - The code stores this as `even_partner` and `odd_partner`, using a negative value for "no partner"

- Worked example from the slides (16 numbers, 4 ranks):
    - Start: `33 36 27 15 | 43 35 36 42 | 49 21 12 27 | 40 9 18 6`
    - Each rank sorts its own block first, with no communication

| Step | Rank 0 | Rank 1 | Rank 2 | Rank 3 |
|---|---|---|---|---|
| After local qsort | 15 27 33 36 | 35 36 42 43 | 12 21 27 49 | 6 9 18 40 |
| Phase 0 (even): (0,1), (2,3) | 15 27 33 35 | 36 36 42 43 | 6 9 12 18 | 21 27 40 49 |
| Phase 1 (odd): (1,2) | 15 27 33 35 (idle) | 6 9 12 18 | 36 36 42 43 | 21 27 40 49 (idle) |
| Phase 2 (even): (0,1), (2,3) | 6 9 12 15 | 18 27 33 35 | 21 27 36 36 | 40 42 43 49 |
| Phase 3 (odd): (1,2) | 6 9 12 15 (idle) | 18 21 27 27 | 33 35 36 36 | 40 42 43 49 (idle) |

- What the table shows:
    - With p ranks, at most p phases are needed, here 4
    - Phase 0, pair (0,1): merge to `15 27 33 35 36 36 42 43`, rank 0 keeps `15 27 33 35`, rank 1 keeps `36 36 42 43`
    - Read the final row left to right and the whole list is sorted

- The exchange, from the slides:

    ```c
    MPI_Sendrecv(local_A, local_n, MPI_INT, even_partner, 0,
                 temp_B,  local_n, MPI_INT, even_partner, 0,
                 comm, &status);
    if (my_rank % 2 != 0) Merge_keep_high(local_A, temp_B, temp_C, local_n);
    else                  Merge_keep_low (local_A, temp_B, temp_C, local_n);
    ```

    - `local_A` is my block, `temp_B` receives the partner's block, `temp_C` is scratch space for the merge
    - One call sends and receives at the same time, in both directions
    - In an even phase, odd ranks are the higher member of their pair, so they keep the high half
    - The lecture renamed the book's `Merge_low` and `Merge_high` to `Merge_keep_low` and `Merge_keep_high`

::: note Why there are no barriers
- In pthreads, a fast thread could overwrite its block while a slow partner was still reading it, so each phase needed two barriers that every thread had to hit
- In MPI each rank's memory is private, so there is nothing for a fast rank to overwrite
- `MPI_Sendrecv` only synchronizes the two ranks in the pair. It is not a group-wide wait
- An idle rank makes no call at all and moves straight on
- Synchronization is a side effect of the communication call
:::

- Phases can get out of step:
    - Nothing forces all ranks to be in the same phase
    - Example: rank 3 finishes phase 0, has no partner in phase 1, starts phase 2 and blocks sending to rank 2
    - Meanwhile rank 2 may still be finishing its phase 0 merge
    - That is correct: rank 3 simply waits inside `MPI_Sendrecv` until rank 2 arrives

- Why not plain MPI_Send then MPI_Recv?:
    - If both ranks in a pair run `MPI_Send` then `MPI_Recv`, it often works
    - Whether `MPI_Send` blocks is up to the implementation, and usually depends on message size
    - Small messages are buffered, so the send returns before any receive is posted
    - Large messages are not buffered, so each send waits for a receive that never starts: a **deadlock**
    - So small test data passes every time and large data hangs. The bug is latent, not absent
    - **deadlock**: two or more processes each waiting on the other, so none can continue

- Forcing the deadlock with MPI_Ssend:

    ```c
    MPI_Ssend(local_A, local_n, MPI_INT, partner, 0, comm);
    MPI_Recv (temp_B,  local_n, MPI_INT, partner, 0, comm, &status);
    ```

    - `MPI_Ssend` never returns until the matching receive has started
    - Both ranks block in `MPI_Ssend`, so neither reaches its `MPI_Recv`
    - Changing only the even-phase branch is enough: every pair deadlocks in phase 0
    - `make run-lock` runs this version. Each rank prints "sending to ... and waiting", then it hangs
    - See Hangs and mix-ups for the same pattern with two ranks (`head_to_head.c`)

- Running the course program:
    - Build: `mpicc -g -Wall -o mpi_odd_even mpi_odd_even.c`
    - Run: `mpiexec -n <p> mpi_odd_even <g|i> <global_n>`
    - `g` generates a random list on each rank, `i` makes rank 0 read the list from stdin and scatter it
    - Rank 0 gathers and prints the sorted list. The lecture moved the hidden `MPI_Gather` out of `Print_global_list` into `main`
    - `mpi_odd_even_trace.c` builds with `-DTRACE`, `-DSLOW_RANK=k` and `-DSTEP` to show each send, receive and keep
    - The trace lines are printed out of order, so sort them: `... | grep '^\[' | sort -s -k2,2n`

- Lecture 12 review questions:
    - Should the local sort be timed? Yes if you are timing the whole sort: it is real work every rank must do. Leave out input generation and printing
    - Where does the MPI version's running time differ from pthreads? In the exchange: every phase now moves n/p elements over the network, which pthreads got for free
    - Where is the serial fraction now? Mostly in the input scatter and the final gather and print on rank 0, plus idle ranks in odd phases
    - These three answers are this site's suggestions, the lecture leaves them open
