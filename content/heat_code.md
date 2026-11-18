title: heatDiffusionMpi.c

- How to read this program:
    - Pick a rank to see what it runs. Almost every line is run by every rank: only the frame write is rank 0 only
    - Press Next step to follow one iteration: the halo exchange, the Allreduce and the Gatherv
    - Change the number of processes and watch how many rows cross between ranks
    - The rank lens cannot show it, but the partners differ: rank 0 and the last rank talk to `MPI_PROC_NULL` on one side

{{walk heat}}

- Things to notice:
    - Lines 164 and 167 are the whole halo exchange. There is no `if` around them, because `MPI_PROC_NULL` handles the ends
    - The exchange is the first thing in the loop, so the ghost rows are fresh before any cell reads them
    - Line 176 converts the local row to a global row before `isFixed` is asked about the plate
    - The `if` on line 207 is evaluated identically on every rank, so `MPI_Gatherv` is always called by everyone
    - Line 211 is the only rank branch inside the loop

- Trip-ups in the course file:
    - The comment at the top says "Shared-memory (Pthreads) implementation". It was copied from the pthreads file, this one is MPI
    - The build line in the comment puts `-lm` before the source file. On Ubuntu with gcc that link fails ("DSO missing from command line", tested with MPICH and Open MPI), so use the order from the slides: `... heatDiffusionMpi.c -lm`
    - The variable names are camelCase (`myRows`, `rowStart`), the slides use snake_case (`my_rows`, `row_start`). Same variables
    - `textFrames` writes `roundf(9 * value)`, which is how the slides get the 0 to 9 grids

::: run Real run on 4 ranks, the slides' toy grid (Open MPI)
$ mpirun -np 4 ./heatDiffusionMpi 16 6 1e-4 50000 1 frames txt
N=16 ranks=4 K=6 eps=0.0001 -> 69 iterations, 0.006 sec, 70 frames -> frames/
compute=0.000 comm=0.000 allreduce=0.000 output=0.006
:::

::: run Frame 9 (the grid as iteration 10 begins, slide 37)
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 1 1 1 1 0 0 0 0 0 0
0 0 0 0 1 1 1 2 2 1 1 1 0 0 0 0
0 0 0 1 2 3 3 3 3 3 3 2 1 0 0 0
0 0 1 2 3 5 6 6 6 6 5 3 2 1 0 0
0 0 1 3 5 9 9 9 9 9 9 5 3 1 0 0
0 1 1 3 6 9 9 9 9 9 9 6 3 1 1 0
0 1 2 3 6 9 9 9 9 9 9 6 3 2 1 0
0 1 2 3 6 9 9 9 9 9 9 6 3 2 1 0
0 1 1 3 6 9 9 9 9 9 9 6 3 1 1 0
0 0 1 3 5 9 9 9 9 9 9 5 3 1 0 0
0 0 1 2 3 5 6 6 6 6 5 3 2 1 0 0
0 0 0 1 2 3 3 3 3 3 3 2 1 0 0 0
0 0 0 0 1 1 1 2 2 1 1 1 0 0 0 0
0 0 0 0 0 0 1 1 1 1 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
:::

- The decomposition helper (lines 339 to 350):

{{code heatDiffusionMpi.c 339-350 hl=341,342,345}}

- Reading the helper:
    - `base` and `rem` are computed once, then each rank r gets `base` rows plus one if `r < rem`
    - `row` starts at 1, because global row 0 is the fixed top edge
    - Every rank fills the table for every rank, not just its own entry
