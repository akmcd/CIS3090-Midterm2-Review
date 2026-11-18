title: Questions for lectures 12 to 17

- How to use these:
    - Same as the first question page: answer first, then open the answer and mark yourself
    - Answers marked as run were checked by compiling and running the code (Open MPI for the heat program, Warp 1.16 on the CPU)
    - Marks on this page are kept separately from the first question page

{{progress}}

::: q
Odd-even sort, 4 ranks. In an **odd** phase, who is rank 0's partner, and what does rank 0 do?
---
- Rank 0 is even, and in an odd phase an even rank's partner is rank - 1 = -1
- -1 is not a valid rank, so rank 0 has no partner: no `MPI_Sendrecv`, no merge
- It moves straight on to the next phase without waiting for anyone
- Rank 3 is idle too: it is odd, so its partner is 3 + 1 = 4, which is past the last rank
:::

::: q
Ranks 2 and 3 hold the sorted blocks `12 21 27 49` and `6 9 18 40` and do a compare-split in an even phase. What does each keep?
---
- Merge the two blocks: `6 9 12 18 21 27 40 49`
- The lower rank keeps the low half: rank 2 gets `6 9 12 18`
- The higher rank keeps the high half: rank 3 gets `21 27 40 49`
- In the code, rank 3 (odd) calls `Merge_keep_high` and rank 2 calls `Merge_keep_low`
:::

::: q
The pthreads odd-even sort needed two barriers per phase. Why does the MPI version need none?
---
- In pthreads, all blocks sit in one shared address space, so a fast thread could overwrite its block while a slow partner was still reading it
- In MPI each rank's memory is private. A partner only ever sees the copy it received, so there is nothing to race over
- `MPI_Sendrecv` synchronizes the two ranks of a pair as a side effect of moving the data
- Ranks without a partner make no call and do not wait for anyone
:::

::: q
Both ranks of a pair run this. It passes every test with 16 numbers. Is it correct?

```c
MPI_Send(local_A, local_n, MPI_INT, partner, 0, comm);
MPI_Recv(temp_B,  local_n, MPI_INT, partner, 0, comm, &status);
```
---
- No, it is unsafe
- Whether `MPI_Send` blocks is up to the implementation and usually depends on message size
- Small blocks get buffered, so the send returns before the partner posts a receive and the test passes
- Large blocks are not buffered, so both ranks wait in `MPI_Send` for a receive that never starts: deadlock
- Proof: change `MPI_Send` to `MPI_Ssend` and it hangs immediately
- Fix: `MPI_Sendrecv`, or have one rank of each pair receive first
:::

::: q
Heat diffusion, N = 16, 4 ranks. Which global rows does rank 2 own, and which global rows are copied into its two ghost rows?
---
- 14 updatable rows, `base = 3`, `rem = 2`, so the counts are 4, 4, 3, 3
- `row_start` for rank 2 is 1 + 4 + 4 = 9, so it owns global rows 9, 10 and 11
- Top ghost (local row 0): a copy of global row 8, owned by rank 1
- Bottom ghost (local row 4): a copy of global row 12, owned by rank 3
:::

::: q
Rank 2 above is at local row 3 and column j. Which global row does it pass to `isFixed`, and why does it matter?
---
- `global_row = row_start - 1 + local_row = 9 - 1 + 3 = 11`
- `isFixed` asks about the plate (the cold edges and the hot block), and those are defined in global coordinates
- Passing the local row 3 would test the wrong row, so the hot block would land in the wrong place for that rank
:::

::: q
Why does the heat program use `MPI_PROC_NULL` instead of an `if` around the halo exchange?
---
- Rank 0 has no rank above it and the last rank has none below it
- A send or receive with `MPI_PROC_NULL` finishes immediately and does nothing
- The ghost row on that side keeps its initial value, which is the cold edge of the plate, which is correct
- So every rank can make the same two `MPI_Sendrecv` calls, with no special cases
:::

::: q
Someone deletes the down-exchange `MPI_Sendrecv` (keeping only the up-exchange) and runs on 4 ranks. What happens?
---
- It hangs on the very first iteration, before writing any frame (run: killed after a timeout)
- Rank 1's up-exchange sends to and receives from rank 0
- But rank 0's up-exchange is with `MPI_PROC_NULL`, and its down-exchange was deleted, so rank 0 never sends to rank 1
- Rank 1 waits forever for that row. Every up-exchange depends on a down-exchange that no longer exists
- The slides suggest a visible seam instead. With this file, removing either call on every rank leaves every pair unmatched, so it hangs
- On 1 rank it still runs, because both neighbours are `MPI_PROC_NULL` (run)
:::

::: q
The halo exchange is moved to **after** the compute phase. Does the program still converge? Is it right?
---
- It still converges, but the result is wrong (run on 4 ranks: 89 iterations instead of 69, and the frames differ)
- The compute phase now reads ghost rows from the previous iteration, which are stale
- So the cells next to a rank boundary use old neighbour values
- On 1 rank the result is still correct (run), because there are no ghost rows between ranks
:::

::: q
The heat program uses `MPI_Gatherv` to build each frame. Why not `MPI_Gather`? With N = 16 and 4 ranks, what are `recv_counts[3]` and `displs[3]`?
---
- `MPI_Gather` needs every rank to send the same amount, but the bands here are 4, 4, 3 and 3 rows
- `MPI_Gatherv` takes a count and a displacement for each rank
- Rank 3: `row_count = 3`, `row_start = 12`
- `recv_counts[3] = 3 * 16 = 48` and `displs[3] = 12 * 16 = 192`
:::

::: q
A rank finishes the compute phase very early and calls `MPI_Allreduce`. What happens to it, and what does that do to the measured times?
---
- It waits inside `MPI_Allreduce` until every rank has entered the call
- That waiting is counted in `reduce_time` (and waiting in the Sendrecvs in `comm_time`)
- So those timers mostly measure load imbalance, not data transfer. In the lecture, 0.466 s of "comm" was for 4 KB rows
:::

::: q
A program's speedup on 8 cores is 6. What is its efficiency, and what does that number mean?
---
- `E = S / p = 6 / 8 = 0.75`
- On average each core spends 75% of its time doing useful work on the problem
- The rest is overhead: communication, synchronization, idle time
:::

::: q
90% of a program can be parallelized perfectly. What speedup does Amdahl's law give on 4 cores, and what is the most it could ever reach?
---
- `S = 1 / (0.9/4 + 0.1) = 1 / 0.325 = 3.08` (the lecture table shows 3.07)
- The maximum, as p grows without limit, is `1 / 0.1 = 10`
- Even with 1000 cores, the 10% serial part keeps it under 10
:::

::: q
Classify each with Flynn's taxonomy: a single-core laptop from 2005, an x86 SSE vector unit, an MPI cluster, a 16-core desktop CPU.
---
- Single-core laptop: SISD
- SSE vector unit: SIMD
- MPI cluster: MIMD with distributed memory (each node is often shared memory, so hybrid)
- 16-core desktop: MIMD with shared memory
- A GPU is usually described as SIMT, a lockstep relative of SIMD
:::

::: q
A crossbar switch connects 4 CPUs to 4 memory modules. When do two CPUs slow each other down? How is that different from a bus?
---
- Only when two CPUs want the same memory module at the same time
- Otherwise each CPU gets its own path, so all four can access memory at once
- On a bus every access shares one path, so CPUs wait for each other even when they want different memory
:::

::: q
What is wrong with this Warp kernel, meant to compute `z = x + y`?

```python
@wp.kernel
def addArrays(x: wp.array(dtype=float), y: wp.array(dtype=float)):
    tid = wp.tid()
    return x[tid] + y[tid]
```
---
- Kernels do not return values, so the sums go nowhere
- Add an output parameter `z: wp.array(dtype=float)` and write `z[tid] = x[tid] + y[tid]`
- On the host, create `z` with `wp.zeros(...)` and pass it in `outputs=[z]`
:::

::: q
A kernel contains `if x[tid] > 0: ... else: ...`, and about half the threads in each group take each branch. Why is this slow on a GPU?
---
- Threads in a group run in lockstep with one program counter
- When they disagree, the group runs the `if` path with the `else` threads masked off, then the `else` path with the `if` threads masked off
- The time is the sum of both branches, as if every thread ran both
:::

::: q
A GPU version of a small program (1000 elements) runs slower than the CPU version. Give the most likely reason.
---
- Copying the data from CPU memory to GPU memory and back goes over the bus, which is expensive
- For small problems that copy can take longer than the computation it saves
- The GPU only pays off when there is enough work per byte copied
:::

::: q
Apply the 3 x 3 mean filter to the centre pixel. Then apply the high-pass kernel (8 in the centre, -1 around it) to the same neighbourhood.

```
10  10  10
10  90  10
10  10  10
```
---
- Mean: sum is 8 x 10 + 90 = 170, and 170 / 9 = 18.9
- High-pass: 8 x 90 - 8 x 10 = 720 - 80 = 640
- The mean filter spreads the bright spot out, the high-pass filter makes it stand out
- A median filter here gives 10: the bright pixel is an outlier and is removed completely
:::

::: q
A 5 x 5 kernel is used on a 100 x 80 image with no border handling. How big is the region where convolution is possible, and where does it start?
---
- Half-width m = 2
- Region: (100 - 4) x (80 - 4) = 96 x 76
- It starts at (2, 2), the first pixel that is 2 away from every edge
:::

::: q
Why are smoothing kernels normalized, and why is the sharpening kernel's sum 0 instead of 1?
---
- A smoothing kernel divided by its sum keeps a constant region at the same value and keeps total brightness unchanged
- The sharpening kernel is meant to give 0 on constant regions and a large value at edges, so its coefficients add to 0
- Its output is an edge map, which is then added back to the image (as in unsharp masking)
:::

::: q
Unsharp masking with k = 0.5 is applied to the row `10 10 10 10 50 50 50 50`, with a 3-wide mean as the blur. What are the two values next to the edge, and what is this effect called?
---
- Blur: `10 10 10 23.3 36.7 50 50 50`
- Edge image g = f - blur: `0 0 0 -13.3 13.3 0 0 0`
- `f + 0.5 g`: `10 10 10 3.3 56.7 50 50 50`
- The values next to the edge are 3.3 and 56.7: below 10 and above 50
- That is **overshoot**: the edge gets steeper by getting taller
:::

::: q
An image has salt-and-pepper noise. Which filter do you choose, a 3 x 3 mean or a 3 x 3 median, and what is the risk?
---
- The median: an isolated noisy pixel never ends up as the middle value, so it is removed, and edges stay sharp
- The mean would only smear each spike into its neighbours
- Risk: any real feature smaller than half the neighbourhood (a thin line, a small dot) is removed too
:::

::: q
Is a median filter a convolution? Could you write it as a kernel matrix?
---
- No. Convolution is a weighted sum, and the median comes from sorting
- No fixed set of weights gives the middle value for every neighbourhood, so there is no kernel matrix
- It is a non-linear, order-statistic (rank) filter
:::

::: q
In a Gaussian filter, what happens when sigma increases?
---
- The weights spread out more, so more blur
- The kernel gets bigger, since it runs from -[3 sigma] to [3 sigma]
- It stays rotationally symmetric, so no direction is blurred more than another
:::
