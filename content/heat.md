title: Heat distribution with MPI
source: Lecture 13
lead: The heat plate from the pthreads unit, split into row bands, one per rank. Each rank keeps copies of the rows just outside its band and refreshes them with a message every iteration.

- What lecture 13 is about:
    - The heat diffusion case study from the pthreads unit, rewritten for distributed memory
    - A rank only sees its own memory, so reading a neighbour's row now means receiving a message
    - Everything else (the plate, the averaging rule, the stopping rule) is the same

- The problem (review):
    - A square plate, cold on all four edges, with a hot block held fixed in the centre
    - Each interior cell's next value is the average of its 4 neighbours (up, down, left, right) from the previous step
    - **fixed cells**: the cold edges and the hot block. They never update
    - Repeat until the largest change anywhere on the plate drops below `EPSILON`
    - Orientation used in the lecture: row 0 is the top, row N - 1 the bottom, so row i + 1 is "down"

- The pthreads version it replaces:
    - Each thread owns a contiguous band of rows and reads any row of the shared grid directly
    - Two barriers per iteration: after everyone writes, and after thread 0 computes the global max, swaps and decides
    - Hazard 1: a thread reading a neighbour's row while it is being written
    - Hazard 2: threads racing past thread 0's stop decision
    - Keep both in mind, MPI removes them in a different way

- Foster's methodology again:
    - **Partitioning**: unchanged. One cell's update is the smallest task. Within an iteration all cells are independent, across iterations they are strictly ordered
    - **Communication**: the step that changes. A rank needs the row just above and just below its band, and another rank owns those rows
    - So every rank, every iteration: two rows in, two rows out
    - **Agglomeration**: still one contiguous band of rows per rank, but now the band also stores copies of the two rows outside it
    - **Mapping**: same arithmetic as pthreads, plus a new job: the tables must let rank 0 put the whole grid back together for output

- Ghost rows:
    - **ghost row** (also called a halo row): a local copy of a row owned by a neighbouring rank
    - A rank with `my_rows` rows allocates `(my_rows + 2) x N` doubles, the 2 extra rows are the ghosts
    - The rank stores and reads its ghost rows but never computes them
    - **halo exchange**: refreshing the ghost rows from the neighbours once per iteration, before computing

- Local array layout on one rank:

| Local row | What it holds |
|---|---|
| 0 | top ghost: copy of the last row of the rank above |
| 1 | first owned row |
| ... | owned rows |
| `my_rows` | last owned row |
| `my_rows + 1` | bottom ghost: copy of the first row of the rank below |

- Local rows are not global rows:
    - Every rank's array starts at local row 0, so local row 1 is only global row 1 on rank 0
    - Conversion: `global_row = row_start - 1 + local_row`
    - `is_fixed(i, j)` asks about the plate, so it must be given the global row
    - Getting this off by one shifts the hot block or a whole band, and the lecture names it the likely culprit when output is wrong

    ::: warn Exam trap
    - Rank 2 owns global rows 9 to 11, but in its own array they are local rows 1 to 3. `is_fixed` must be given 9, 10, 11, not 1, 2, 3
    :::

- The decomposition (mapping):

    ```c
    updatable_rows = N - 2;               /* rows 0 and N-1 are fixed, nobody owns them */
    base = updatable_rows / comm_sz;
    rem  = updatable_rows % comm_sz;
    row_count[r] = base + (r < rem ? 1 : 0);   /* the first rem ranks get one extra row */
    row_start[r] = 1 + sum of row_count[0 .. r-1];
    ```

    - Every rank builds both arrays for all ranks: it tells a rank its own range, and lets rank 0 reassemble the grid

- Example: 16 rows on 4 ranks:
    - `updatable_rows = 14`, `base = 3`, `rem = 2`

| Rank | row_start | row_count | Global rows owned |
|---|---|---|---|
| 0 | 1 | 4 | 1 to 4 |
| 1 | 5 | 4 | 5 to 8 |
| 2 | 9 | 3 | 9 to 11 |
| 3 | 12 | 3 | 12 to 14 |

- Exchange topology:
    - Each interior rank does two exchanges: one with the rank above, one with the rank below
    - Rank r's down-exchange is matched by rank r + 1's up-exchange
    - Rank 0 has no rank above, the last rank has no rank below

- The halo exchange, two calls per iteration:

    ```c
    /* up-exchange: send my first owned row, receive into my top ghost */
    MPI_Sendrecv(&cur[IDX(1, 0)],           N, MPI_DOUBLE, up_neighbour,   0,
                 &cur[IDX(0, 0)],           N, MPI_DOUBLE, up_neighbour,   0,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    /* down-exchange: send my last owned row, receive into my bottom ghost */
    MPI_Sendrecv(&cur[IDX(my_rows, 0)],     N, MPI_DOUBLE, down_neighbour, 0,
                 &cur[IDX(my_rows + 1, 0)], N, MPI_DOUBLE, down_neighbour, 0,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    ```

    - `IDX(i, j)` is `i * N + j`, so `&cur[IDX(1, 0)]` is the start of local row 1
    - Example with 4 ranks: rank 1's local row 1 (global 5) lands in rank 0's local row 5, its bottom ghost
    - And rank 0's local row 4 (global 4) lands in rank 1's local row 0, its top ghost
    - `MPI_Sendrecv` posts its receive as part of the call, so no rank is stuck mid-send
    - It does not return until the incoming row has arrived, so a rank cannot compute with a half-updated ghost

- The ends: MPI_PROC_NULL:

    ```c
    int up_neighbour   = (my_rank == 0)           ? MPI_PROC_NULL : my_rank - 1;
    int down_neighbour = (my_rank == comm_sz - 1) ? MPI_PROC_NULL : my_rank + 1;
    ```

    - **MPI_PROC_NULL**: MPI's name for "nobody". A send or receive with it finishes at once and does nothing
    - Rank 0's top ghost and the last rank's bottom ghost are left alone, and they already hold the cold edge
    - So every rank makes the same two calls, with no `if` for the boundary ranks

- Convergence check: one call:

    ```c
    MPI_Allreduce(&local_max, &global_max, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
    ```

    - Each rank finds the largest change in its own band, `MPI_MAX` combines them, and every rank receives the result
    - No rank leaves the call until every rank has entered it, so it also acts as the barrier
    - Every rank then tests `global_max < EPSILON || iteration >= MAX_ITERS - 1` on the same number, so all stop together
    - Barrier, thread 0's reduction loop, barrier: three pthreads constructs become one line

- Frame output: MPI_Gatherv:
    - To write a frame, rank 0 needs every rank's band: that is a gather
    - `MPI_Gather` needs the same count from every rank, but the bands can differ in size (4, 4, 3, 3 above)
    - **MPI_Gatherv**: "v" for varying. It takes a count per rank and a displacement per rank saying where that rank's data lands

    ```c
    for (int r = 0; r < comm_sz; r++) {
        recv_counts[r] = row_count[r] * N;   /* how many values rank r sends */
        displs[r]      = row_start[r] * N;   /* where they start in the full grid */
    }
    ```

| Rank | row_start | row_count | recv_counts | displs |
|---|---|---|---|---|
| 0 | 1 | 4 | 64 | 16 |
| 1 | 5 | 4 | 64 | 80 |
| 2 | 9 | 3 | 48 | 144 |
| 3 | 12 | 3 | 48 | 192 |

- What the Gatherv table shows:
    - The total is 224 = 14 x 16. The grid has 256 cells, the missing 32 are rows 0 and 15
    - Those edge rows are never sent, so rank 0's full grid must already hold them: `calloc` sets them to 0.0 once
    - Only rank 0 uses the receive arguments, but every rank must call `MPI_Gatherv`

- The loop, end to end:
    - Step 1: Halo exchange: two `MPI_Sendrecv` calls refresh both ghost rows of `cur`
    - Step 2: Compute: for each owned row, convert to the global row, copy fixed cells, average the rest into `next`, track `local_max`
    - Step 3: `MPI_Allreduce` with `MPI_MAX` gives every rank `global_max`
    - Step 4: Swap `cur` and `next`
    - Step 5: Every `FRAME_STRIDE` iterations, `MPI_Gatherv` to rank 0, and rank 0 writes the frame
    - Step 6: Every rank decides for itself whether to stop, on identical data

- Worked example:

    ::: eg 16 x 16 grid, 6 x 6 hot block, 4 ranks, iteration 10
    - The full grid exists only in our heads, and on rank 0 when a frame is written. No rank holds it
    - Rank 2 owns global rows 9 to 11. Its top ghost copies global row 8 (rank 1) and its bottom ghost copies global row 12 (rank 3)
    - At the start of iteration 10 both ghosts still hold last iteration's copies, which are now stale
    - After the exchange the ghosts are fresh and the three owned rows are untouched: the exchange only writes ghosts
    - Only now may rank 2 compute, which is why the exchange comes first in the loop
    :::

::: note Why there are no barriers
- Hazard 1 (reading a row mid-write) is gone: data only crosses a rank boundary when it is sent, and `MPI_Sendrecv` does not return until it has landed
- Hazard 2 (racing past the stop decision) is gone: `MPI_Allreduce` releases nobody until everyone has arrived, and gives them all the same number
- MPI does not need less synchronization. The synchronization is inside the calls that move the data
- In pthreads the data moved for free and you paid separately in barriers. In MPI you pay once, in the call that does both
:::

- Summary of what changed from pthreads:
    - A free read became a message: two ghost rows per rank, two `MPI_Sendrecv` calls per iteration
    - An implicit mapping became an explicit one: someone has to know every rank's slice to reassemble the grid
    - Barrier, reduction, barrier became one `MPI_Allreduce`
    - Two hazards disappeared, because process isolation removed both the free read and the race
    - The lecture's moral: the memory model decides which problems you have and how you solve them

- Things the lecture suggests trying (checked on this site with Open MPI):
    - Run on 1, 3, 4 and 14 ranks: the text frames are byte-identical, because each frame depends only on the previous one and MAX does not depend on order
    - Move the exchange to after the compute phase: it still converges, but on 4 ranks it took 89 iterations instead of 69 and the frames are wrong. On 1 rank it is still right, because there are no ghosts between ranks
    - `-np 15` on the 16 x 16 grid: only 14 rows can be updated, so the program prints "comm_sz must be between 1 and N-2" and calls `MPI_Abort`
    - Make one rank quit early: the others hang forever at the next collective, which is why the code uses `MPI_Abort` instead of `return`
    - Delete one of the two `MPI_Sendrecv` calls: the slides say a seam appears, but in this file every pair then has an unmatched call, so on 4 ranks it hung before writing a single frame. See the practice questions

- Timing the program:
    - Four `MPI_Wtime` accumulators per rank: compute, comm (the two Sendrecvs), reduce (the Allreduce), output (Gatherv and file write)
    - `MPI_Barrier` before the clock starts, because ranks leave `MPI_Init` at different times. It is the only barrier in the file
    - At the end, `MPI_Reduce` with `MPI_MAX` to rank 0: Reduce because only rank 0 prints, MAX because the run ends when the slowest rank does
    - The four maxima can come from four different ranks, so they do not add up to the elapsed time

- Reading the numbers (lecture run, 514 x 514, 4 ranks, 2221 iterations):
    - `compute=0.196 comm=0.466 allreduce=0.074 output=0.443`
    - It looks like communication costs 0.466 s, but a row is only 514 x 8 bytes, about 4 KB
    - comm and reduce time are mostly **waiting**: a rank that arrives at Sendrecv or Allreduce first sits there with the clock running
    - So they measure load imbalance, not bytes moved
    - Sources of imbalance: some ranks get one extra row, ranks holding the hot block do less arithmetic (fixed cells are cheap), and rank 0 writes the frames while others wait for it next iteration
    - 100 microseconds of skew per iteration over 2200 iterations is about a fifth of a second

- Build and run:
    - `mpicc -O2 -Wall -o heatDiffusionMpi heatDiffusionMpi.c -lm`
    - `mpirun -np 4 ./heatDiffusionMpi 16 6 1e-4 50000 1 frames txt`
    - Arguments in order: N, K (hot block size), epsilon, max iterations, frame stride, output folder, format (`pgm` or `txt`)
    - `python3 heat_diffusion_stitch.py frames heat_diffusion.gif 80` turns the frames into a GIF
