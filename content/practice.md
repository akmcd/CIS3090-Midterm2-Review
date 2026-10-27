title: Code-reading questions

- How to use these:
    - Read the question, decide on an answer in your head or on paper, then open the answer
    - Every answer marked as run was checked by compiling and running the program with MPICH
    - Programs for questions 6, 7, 8, 10, 14 and 16 are in `examples/extras/`
    - After each answer, mark whether you got it, and review the missed ones at the end

{{progress}}

::: q
`mpi_hello.c` is run with `mpiexec -n 1 ./mpi_hello`. What does it print, and how many times does the loop body on line 52 run?
---
- It prints `Greetings from process 0 of 1!` and nothing else (run)
- Rank 0 is the only process, so it prints its own greeting
- The loop `for (int q = 1; q < comm_sz; q++)` starts at 1 and `comm_sz` is 1, so the body runs zero times
- No sends or receives happen at all
:::

::: q
`mpi_hello.c` runs on 8 processes. How many `MPI_Send` calls and how many `MPI_Recv` calls happen in total, and which ranks make them?
---
- 7 sends, made by ranks 1 to 7, one each
- 7 receives, all made by rank 0
- In general `comm_sz - 1` of each, and they must match one to one
- A receive with no send hangs, and a send with no receive can hang or lose the message
:::

::: q
In `mpi_hello.c` the receive on line 54 uses `q` as the source. Suppose you change it to `MPI_ANY_SOURCE`. Does the program still work, and what can change in the output?
---
- It still works: rank 0 still receives exactly 7 messages (for 8 processes) and prints each one
- The order of the greeting lines can now change from run to run
- With `q`, rank 0 waits for rank 1 first, then 2, and so on, which forces rank order
- With `MPI_ANY_SOURCE`, rank 0 takes whichever message arrives first
:::

::: q
In `mpi_hello2.c`, rank 7 of 16 sends the string `"Greetings from process 7 of 16!"`. What does `MPI_Get_count` give rank 0 for that message?
---
- The string has 31 characters
- `strlen(greeting)+1` adds the terminator, so 32 elements are sent as `MPI_CHAR`
- `MPI_Get_count(&status, MPI_CHAR, &count)` therefore sets `count` to 32
- Check with the real run on 4 ranks: "Greetings from process 1 of 4!" is 30 characters and rank 0 reported 31 elements
:::

::: q
A receiver uses `MPI_ANY_SOURCE` and `MPI_ANY_TAG`. How does it find out who sent the message, what tag it had, and how many elements arrived?
---
- Pass the address of an `MPI_Status` variable as the last argument of `MPI_Recv`
- `status.MPI_SOURCE` holds the sender's rank
- `status.MPI_TAG` holds the tag
- `MPI_Get_count(&status, datatype, &count)` gives the number of elements
- The count is a function call because it depends on the datatype
- Only a receiver can use wildcards, a sender must always name a destination and a tag
:::

::: q
What happens when this program runs on 2 processes?

```c
if (rank == 1) MPI_Send(&x, 1, MPI_INT, 0, 5, MPI_COMM_WORLD);
if (rank == 0) { MPI_Recv(&y, 1, MPI_INT, 1, 7, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                 printf("got %d\n", y); }
```
---
- It hangs and never prints (run: it had to be killed after a timeout)
- The send uses tag 5 and the receive wants tag 7, so they do not match
- Rank 0 blocks forever waiting for a message that matches
- Rank 1's message has no receive, so it is never delivered
- With `MPI_ANY_TAG` on the receive, the pair would match
:::

::: q
Two processes each run this code, where `partner` is the other rank. Is it safe?

```c
MPI_Ssend(&mine, 1, MPI_INT, partner, 0, MPI_COMM_WORLD);
MPI_Recv(&other, 1, MPI_INT, partner, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
```
---
- No. Both ranks block in `MPI_Ssend`, each waiting for the other to start a receive, so neither ever gets to its `MPI_Recv` (run: it hangs)
- This is a deadlock, because each process waits for an event the other can only cause after it finishes waiting
- With plain `MPI_Send` it may seem to work if the message is small enough to be buffered, which is exactly why it is called unsafe
- Safety check: swap `MPI_Send` for `MPI_Ssend`, if it hangs it is unsafe
- Fix one: even ranks send then receive, odd ranks receive then send
- Fix two: use `MPI_Sendrecv`
:::

::: q
Three processes all have `a = 1` and `c = 2`. Rank 1 executes the first block below and ranks 0 and 2 execute the second. What are `b` and `d` on rank 0?

```c
/* rank 1 */
MPI_Reduce(&c, &d, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
MPI_Reduce(&a, &b, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);

/* ranks 0 and 2 */
MPI_Reduce(&a, &b, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
MPI_Reduce(&c, &d, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
```
---
- `b = 4` and `d = 5` (run)
- Collective calls match by the order they are made, not by the variable names
- The first call on every rank combines `a` (rank 0) + `c` (rank 1) + `a` (rank 2) = 1 + 2 + 1 = 4, and that goes into `b` on rank 0
- The second call combines 2 + 1 + 2 = 5 and goes into `d`
- This is textbook Table 3.3
:::

::: q
What is wrong with this call?

```c
MPI_Reduce(&x, &x, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
```
---
- The input and output buffers are the same variable, which is called **aliasing**
- MPI forbids aliasing an output argument, so the call is illegal
- The result is unpredictable: it might be correct, wrong, or crash
- Use two separate variables, as in `MPI_Reduce(&local_int, &total_int, ...)`
:::

::: q
Four ranks each set `mine = rank + 1` and `total = -1`, then run both calls below. What do rank 0 and rank 1 hold in `total` and `total2` afterwards?

```c
MPI_Reduce(&mine, &total, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
MPI_Allreduce(&mine, &total2, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
```
---
- Rank 0: `total = 10` and `total2 = 10`
- Rank 1: `total = -1` and `total2 = 10` (run)
- 1 + 2 + 3 + 4 = 10
- `MPI_Reduce` only writes its output on the destination rank, so rank 1's `total` is untouched
- `MPI_Allreduce` has no destination, every rank gets the result
:::

::: q
`mpi_Bcast.c` is run with `echo "0 3 1024" | mpiexec -n 3 ./mpi_Bcast`. The true integral of x squared from 0 to 3 is 9. What is wrong with the answer?
---
- It prints about 8.9737 (run: 8.973662840668112e+00) with no error message
- `local_n = n/comm_sz` is integer division, so 1024/3 is 341
- 3 ranks times 341 is 1023 trapezoids, so the last strip of the interval is never computed
- The program assumes `n` is divisible by `comm_sz`
- It gives the same correct-looking answer on 1, 2, 4 and 8 ranks (run), because they all divide 1024
:::

::: q
Find the bug.

```c
void Get_input(int my_rank, int comm_sz, double* a_p, double* b_p, int* n_p) {
   if (my_rank == 0) {
      printf("Enter a, b, and n\n");
      scanf("%lf %lf %d", a_p, b_p, n_p);
      MPI_Bcast(a_p, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
      MPI_Bcast(b_p, 1, MPI_DOUBLE, 0, MPI_COMM_WORLD);
      MPI_Bcast(n_p, 1, MPI_INT, 0, MPI_COMM_WORLD);
   }
}
```
---
- The `MPI_Bcast` calls are inside the `if`, so only rank 0 makes them
- Every process in the communicator must call a collective function, so this is erroneous
- The other ranks never receive `a`, `b`, `n` and compute with uninitialized values
- Fix: close the `if` after `scanf`, so all ranks execute the three `MPI_Bcast` calls
:::

::: q
A sum over 8 processes is done two ways: rank 0 loops over `MPI_Recv` from each other rank, or `MPI_Reduce` uses a tree. How many steps does rank 0 take in each?
---
- The loop: 7 receives, one after another
- The tree: 3 rounds, which is log2 of 8
- Round 1: ranks 1, 3, 5, 7 send to 0, 2, 4, 6
- Round 2: ranks 2 and 6 send to 0 and 4
- Round 3: rank 4 sends to 0
- The lecture's figure shows this shape, real implementations may choose a different tree
:::

::: q
Four ranks run this code. What does rank 2 hold in `mine` right after the scatter, and what does rank 0 print at the end?

```c
int all[8] = {1,2,3,4,5,6,7,8}, mine[8], back[8] = {0};
int chunk = 8 / size;                       /* size is 4 */
MPI_Scatter(all, chunk, MPI_INT, mine, chunk, MPI_INT, 0, MPI_COMM_WORLD);
for (int i = 0; i < chunk; i++) mine[i] *= 10;
MPI_Gather(mine, chunk, MPI_INT, back, chunk, MPI_INT, 0, MPI_COMM_WORLD);
/* rank 0 then prints back[0] to back[7] */
```
---
- `chunk` is 2, and `send_count` is the number of elements per process
- Rank 2 gets the third chunk: `mine[0] = 5` and `mine[1] = 6`
- Each rank multiplies its chunk by 10
- Gather puts rank 0's chunk first, then rank 1's, and so on
- Rank 0 prints `10 20 30 40 50 60 70 80` (run)
- Passing 8 as the send count instead of `chunk` makes MPI abort with "Message truncated" (run)
:::

::: q
`mpi_SendRec.c` runs on 6 processes. How many point-to-point messages travel in total, and where do they go?
---
- Input: 3 sends to each of the 5 other ranks, which is 15
- Results: 1 message from each of the 5 other ranks, which is 5
- Total 20, which is 4(p - 1) with p = 6
- All 20 are sent to or from rank 0
- The `mpi_Bcast.c` version does the same job with 3 `MPI_Bcast` calls and 1 `MPI_Reduce` call on every rank
:::

::: q
Rank 1 calls `MPI_Send` with 10 ints and tag 3. Rank 0 calls `MPI_Recv` for source 1, tag 3, same communicator and datatype, but a count of 5. Will they match?
---
- The source, destination, tag and communicator all match
- But the buffers are not compatible, because the textbook's rule of thumb needs the receive count to be at least the send count
- The receive buffer is too small for the message, so MPI aborts with a "Message truncated" error (run)
- A receive count larger than the send count is fine, which is why `mpi_hello.c` receives with `MAX_STRING`
:::
