# Topic quiz bank. Run `python content/data_src/make_data.py` after editing; it writes data/bank.js.
# Q(topic, kind, question, options, answer, why, code=None, ctx=None)
# answer is the index of the correct option, or a list of indices for "select all that apply".

BANK = []


def Q(topic, kind, q, options, answer, why, code=None, ctx=None):
    BANK.append(dict(topic=topic, kind=kind, q=q, options=options, answer=answer, why=why, code=code, ctx=ctx))


# ---------------------------------------------------------------- 1. Distributed memory and MPI
T = "concepts"
Q(T, "concept", "How does data get from one MPI process to another?",
  ["Both processes read the same global variable", "One process sends a message and the other receives it",
   "The operating system copies memory pages between them", "Through a buffer protected by a mutex"], 1,
  "Each MPI process has its own private memory. Nothing is shared, so data only moves when one process sends and another receives.")
Q(T, "concept", "What does **SPMD** mean?",
  ["Single program, multiple data: every process runs the same executable and branches on its rank",
   "Single process, multiple devices: one process drives several GPUs",
   "Shared program memory distribution: processes share the code segment",
   "Serial program, multiple data: the program runs once per input file"], 0,
  "SPMD is single program, multiple data. The `if (my_rank != 0) ... else ...` in the hello program is what makes it SPMD.")
Q(T, "concept", "All processes in an MPI program run the same code. What makes them behave differently?",
  ["Their rank, which each process gets from `MPI_Comm_rank`", "mpiexec passes each one a different source file",
   "The order the operating system schedules them in", "Each one is compiled with different flags"], 0,
  "The rank (0 to `comm_sz - 1`) is the only thing that differs. Programs branch on it.")
Q(T, "concept", "What is `MPI_COMM_WORLD`?",
  ["The communicator holding every process that mpiexec started", "The number of processes in the program",
   "A wildcard that matches any sender", "The process with rank 0"], 0,
  "A communicator is a group of processes that can message each other. `MPI_COMM_WORLD` contains all of them.")
Q(T, "concept", "Which call must come before any other MPI call?",
  ["`MPI_Init`", "`MPI_Comm_size`", "`MPI_Comm_rank`", "`MPI_Barrier`"], 0,
  "`MPI_Init` starts MPI. `MPI_Finalize` is the last call, and no MPI call is allowed after it.")
Q(T, "scenario", "A program is started with `mpiexec -n 4 ./prog`. How many times does `main` run?",
  ["4 times, once in each process", "Once, with 4 threads inside it", "Once on rank 0, which then starts 3 others", "It depends on how many cores the machine has"], 0,
  "mpiexec starts 4 separate processes of the same executable, and each one runs `main` from the start.")
Q(T, "concept", "Which statement about MPI and pthreads matches lecture 09?",
  ["MPI uses processes with separate memory, pthreads uses threads that share memory",
   "Both use threads, but MPI threads run on different machines",
   "pthreads is designed for distributed memory, MPI for shared memory",
   "MPI programs cannot run on a single multi-core machine"], 0,
  "pthreads is shared memory with threads. MPI is distributed memory with processes, and it still runs fine on one machine with several cores.")
Q(T, "concept", "Several MPI processes all call `printf`. What can you say about the output?",
  ["The order can change from run to run, and lines can interleave", "It always appears in rank order",
   "Only rank 0's output appears", "MPI buffers it and prints it at `MPI_Finalize`"], 0,
  "Output from several processes is nondeterministic. For a fixed order, send the text to rank 0 and print it there, as `mpi_hello.c` does.")
Q(T, "concept", "Most MPI implementations only let which process read from stdin?",
  ["Rank 0", "The last rank", "Every rank", "No rank: input must come from a file"], 0,
  "So rank 0 calls `scanf` and then sends or broadcasts the values to the others.")

# ---------------------------------------------------------------- 2. Reading MPI code
T = "method"
Q(T, "calc", "This runs on 5 processes. How many times is the receive called in total?",
  ["4", "5", "1", "0"], 0,
  "Only rank 0 runs the loop, and q goes 1, 2, 3, 4. Ranks 1 to 4 each send once, so there are 4 receives to match 4 sends.",
  code="if (my_rank != 0) {\n   MPI_Send(msg, len, MPI_CHAR, 0, 0, MPI_COMM_WORLD);\n} else {\n   for (int q = 1; q < comm_sz; q++)\n      MPI_Recv(msg, MAX, MPI_CHAR, q, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);\n}")
Q(T, "scenario", "What happens when this runs on 2 processes?",
  ["It hangs: rank 0 waits for tag 7 but the message has tag 5", "It prints the value of x",
   "MPI aborts with a tag error", "It works, because tags are ignored when the ranks match"], 0,
  "Source and destination agree, but the tags do not. Rank 0's receive never matches, so it blocks forever.",
  code="if (rank == 1) MPI_Send(&x, 1, MPI_INT, 0, 5, MPI_COMM_WORLD);\nif (rank == 0) MPI_Recv(&y, 1, MPI_INT, 1, 7, MPI_COMM_WORLD, MPI_STATUS_IGNORE);")
Q(T, "concept", "When you predict an MPI program, what should you do first?",
  ["Fix a number of processes and decide which ranks run each branch", "Read the code top to bottom as one process",
   "Count the printf calls", "Look for MPI_Finalize"], 0,
  "Pick p, list the ranks, then split the code by `if (my_rank ...)`. Reading top to bottom as one process is the classic mistake.")
Q(T, "concept", "Which of these make a program wait forever?",
  ["A receive with no matching send", "Two ranks that each do `MPI_Ssend` to the other before receiving",
   "A collective call that one rank skips", "A send whose receive uses a larger count"], [0, 1, 2],
  "A larger receive count is fine (it is the capacity). The other three each leave a process waiting for something that never happens.")
Q(T, "scenario", "Ranks 1 to 3 each print a line with `printf`, then rank 0 prints one line. What can you say about the order?",
  ["Lines from ranks 1 to 3 can appear in any order, mixed with rank 0's", "Always rank 1, 2, 3, then 0",
   "Always rank 0 first", "Only rank 0's line appears"], 0,
  "Several ranks printing means the order can change between runs. Only output funnelled through one rank has a fixed order.")
Q(T, "concept", "Which pair of calls matches?",
  ["Rank 1: `MPI_Send(..., 0, 3, comm)` and rank 0: `MPI_Recv(..., 1, MPI_ANY_TAG, comm, ...)`",
   "Rank 1: `MPI_Send(..., 0, 3, comm)` and rank 0: `MPI_Recv(..., 2, 3, comm, ...)`",
   "Rank 1: `MPI_Send(..., 2, 3, comm)` and rank 0: `MPI_Recv(..., 1, 3, comm, ...)`",
   "Rank 1: `MPI_Send(..., 0, 3, comm)` and rank 0: `MPI_Recv(..., 1, 4, comm, ...)`"], 0,
  "Source, destination, tag and communicator must all agree. `MPI_ANY_TAG` accepts tag 3.")
Q(T, "concept", "What is a **deadlock**?",
  ["A set of processes each waiting for something only another waiting process could provide",
   "A process that crashes inside an MPI call", "A message that arrives out of order", "Two processes printing at the same time"], 0,
  "Each process waits on another, so none can ever continue.")

# ---------------------------------------------------------------- 3. Send and receive
T = "sendrecv"
Q(T, "concept", "In `MPI_Recv(buf, count, ...)`, what does `count` mean?",
  ["How many elements the buffer can hold", "Exactly how many elements will arrive", "How many bytes the buffer holds", "How many messages to receive"], 0,
  "It is the capacity in elements. The message may be shorter, but not longer.")
Q(T, "concept", "Which wildcards can a **sender** use?",
  ["None: a sender must name a destination and a non-negative tag", "`MPI_ANY_SOURCE` only", "`MPI_ANY_TAG` only", "Both"], 0,
  "Wildcards are for receivers only. The textbook calls MPI a push mechanism.")
Q(T, "concept", "A receive used `MPI_ANY_SOURCE`. How does the receiver find out who sent the message?",
  ["`status.MPI_SOURCE`", "The return value of `MPI_Recv`", "`MPI_Get_count`", "It cannot find out"], 0,
  "`status.MPI_SOURCE` and `status.MPI_TAG` say what matched. `MPI_Get_count` gives the number of elements.")
Q(T, "calc", "A rank sends `\"Hi rank 3\"` with `strlen(greeting)+1` elements of `MPI_CHAR`. What does `MPI_Get_count` report on the receiver?",
  ["10", "9", "11", "It depends on the receive count"], 0,
  "The string has 9 characters, and the `+1` sends the terminating `'\\0'` too, so 10 elements arrive.")
Q(T, "concept", "When `MPI_Send` returns, what do you know for sure?",
  ["The send buffer can safely be reused", "The receiver has the message", "The receiver has started its receive", "The message is in the receiver's buffer"], 0,
  "`MPI_Send` may copy the message into a system buffer and return, or wait. Either way, only your buffer is guaranteed safe to reuse.")
Q(T, "scenario", "Rank 1 sends 10 ints with tag 3. Rank 0 receives from source 1, tag 3, with a count of 5. What happens?",
  ["MPI aborts with a message-truncated error", "Rank 0 gets the first 5 ints", "It hangs", "Rank 0 gets all 10 ints"], 0,
  "Everything matches except the buffer, which is too small. MPI reports \"Message truncated\". A larger receive count would have been fine.")
Q(T, "concept", "Rank 0 sends a, b and n to rank 1 with the same tag, in that order. Why does rank 1 receive them in the right order?",
  ["Messages between the same two processes are non-overtaking", "MPI sorts messages by size",
   "Rank 1 uses `MPI_ANY_TAG`", "It is not guaranteed, so this is a bug"], 0,
  "Two messages from the same sender to the same receiver arrive in the order they were sent.")
Q(T, "scenario", "Two ranks each run `MPI_Send` to the other, then `MPI_Recv` from the other. Small messages work, large ones hang. What is the best description?",
  ["The program is unsafe: it relies on MPI buffering small messages", "MPI has a bug with large messages",
   "The tags must be different", "It is safe, large messages are just slow"], 0,
  "Small messages get buffered, so the sends return. Large ones block until a receive starts, which never happens. Test with `MPI_Ssend`.")
Q(T, "concept", "Which are correct fixes for two ranks that each send first and then receive?",
  ["Use `MPI_Sendrecv`", "Even ranks send then receive, odd ranks receive then send",
   "Replace `MPI_Send` with `MPI_Ssend`", "Use different tags on the two sends"], [0, 1],
  "`MPI_Ssend` makes the deadlock certain. Different tags change nothing about who waits. Ordering the calls or using `MPI_Sendrecv` fixes it.")

# ---------------------------------------------------------------- 4. Collective communication
T = "collectives"
Q(T, "concept", "How do collective calls match each other?",
  ["By communicator and by the order the calls are made", "By tag", "By variable name", "By the root rank only"], 0,
  "Collectives have no tags. The first collective on every rank matches, then the second, and so on.")
Q(T, "calc", "Three ranks have `a = 1` and `c = 2`. Rank 1 runs the first line, ranks 0 and 2 the second. What is `b` on rank 0 after the first `MPI_Reduce`?",
  ["4", "3", "5", "6"], 0,
  "The first collective on every rank matches: rank 0 gives a (1), rank 1 gives c (2), rank 2 gives a (1). 1 + 2 + 1 = 4 goes into rank 0's b.",
  code="/* rank 1 */       MPI_Reduce(&c, &d, 1, MPI_INT, MPI_SUM, 0, comm);  MPI_Reduce(&a, &b, ...);\n/* ranks 0 and 2 */ MPI_Reduce(&a, &b, 1, MPI_INT, MPI_SUM, 0, comm);  MPI_Reduce(&c, &d, ...);")
Q(T, "scenario", "Four ranks set `mine = rank + 1` and `total = -1`, then call `MPI_Reduce(&mine, &total, 1, MPI_INT, MPI_SUM, 0, comm)`. What is `total` on rank 2?",
  ["-1", "10", "3", "Undefined, the program crashes"], 0,
  "`MPI_Reduce` only writes its output on the destination, here rank 0 (which gets 10). Rank 2's `total` is untouched.")
Q(T, "concept", "What is wrong with `MPI_Reduce(&x, &x, 1, MPI_DOUBLE, MPI_SUM, 0, comm)`?",
  ["The input and output are the same variable, and MPI forbids aliasing an output", "The root must be 1",
   "`MPI_SUM` does not work on doubles", "Nothing"], 0,
  "Using the same buffer for input and output is illegal. The result is unpredictable.")
Q(T, "calc", "A tree-structured sum over 8 processes takes how many rounds?",
  ["3", "7", "8", "4"], 0,
  "log2 8 = 3. A loop of receives on rank 0 would take 7 receives one after another.")
Q(T, "concept", "What does `MPI_Allreduce` do that `MPI_Reduce` does not?",
  ["Every process receives the result", "It works on arrays", "It uses tags", "It only needs rank 0 to call it"], 0,
  "Same arguments minus the destination. Use it when everyone needs the total for the next step.")
Q(T, "scenario", "`MPI_Bcast` is called inside `if (my_rank == 0) { ... }`. What goes wrong?",
  ["The other ranks never take part, so they never get the data", "Nothing, rank 0 is the root",
   "The broadcast happens twice", "Only the last rank gets the data"], 0,
  "Every process in the communicator must call a collective. Close the `if` before the broadcast calls.")
Q(T, "calc", "Four ranks run `MPI_Scatter(all, 2, MPI_INT, mine, 2, MPI_INT, 0, comm)` with `all = {1,2,3,4,5,6,7,8}` on rank 0. What does rank 2 get?",
  ["5 and 6", "3 and 4", "2 and 3", "1 and 2"], 0,
  "`send_count` is per process. Rank 0 gets 1,2, rank 1 gets 3,4, rank 2 gets 5,6, rank 3 gets 7,8.")
Q(T, "concept", "In `MPI_Scatter`, what is `send_count`?",
  ["The number of elements sent to each process", "The length of the whole array", "The number of processes", "The size in bytes"], 0,
  "Per process. Passing the total length made MPI abort with \"Message truncated\" when tested.")
Q(T, "concept", "In `MPI_Bcast(data, count, type, source, comm)`, what is `data` on a process that is not the source?",
  ["An output: it receives the broadcast value", "An input that is ignored", "It must be NULL", "The value to send back to the source"], 0,
  "On the source it is the input, everywhere else it is where the value lands.")

# ---------------------------------------------------------------- 5. The trapezoidal rule
T = "trapezoid"
Q(T, "calc", "a = 0, b = 3, n = 1024 on 4 ranks. What are `local_n` and rank 2's slice?",
  ["256, from 1.5 to 2.25", "256, from 0.75 to 1.5", "341, from 1.5 to 2.25", "1024, from 0 to 3"], 0,
  "local_n = 1024 / 4 = 256. h = 3/1024, so rank 2 starts at 2 x 256 x h = 1.5 and ends 256h = 0.75 later.")
Q(T, "concept", "In the trapezoid estimate `h * [f(a)/2 + f(x_1) + ... + f(b)/2]`, why are the two end points halved?",
  ["Each interior point belongs to two trapezoids, the end points to only one", "To correct for rounding",
   "Because h is halved", "Because f is convex"], 0,
  "Each trapezoid adds (h/2)(left + right). Interior points appear twice, so they lose the half. The ends appear once.")
Q(T, "scenario", "`mpi_Bcast.c` runs with n = 1024 on 3 ranks and prints about 8.97 instead of 9. Why?",
  ["1024 / 3 truncates to 341, so only 1023 trapezoids are computed", "Floating-point error grows with more ranks",
   "MPI_Reduce adds the values in the wrong order", "Rank 0 is counted twice"], 0,
  "The code assumes n divides evenly by comm_sz. The last strip is never computed, and there is no error message.")
Q(T, "calc", "`mpi_SendRec.c` runs on 5 processes. How many point-to-point messages are sent?",
  ["16", "8", "12", "20"], 0,
  "3 input values to each of 4 other ranks (12) plus 4 results back (4). 4(p - 1) = 16.")
Q(T, "concept", "Why is the result for x squared from 0 to 3 slightly above 9?",
  ["x squared is convex, so every trapezoid overestimates", "Integer division adds an extra strip",
   "MPI_SUM rounds up", "h is computed with integer division"], 0,
  "On a convex curve the straight top of each trapezoid sits above the curve.")
Q(T, "concept", "Moving from `mpi_SendRec.c` to `mpi_Bcast.c`, what changes?",
  ["The input becomes MPI_Bcast and the sum becomes MPI_Reduce", "The Trap function changes",
   "h is computed differently", "Every rank now reads stdin"], 0,
  "The maths and `Trap` are identical. Only the communication changes.")

# ---------------------------------------------------------------- 6. Odd-even sort with MPI
T = "odd_even"
Q(T, "concept", "In an even phase of odd-even transposition sort, which pairs are compare-swapped?",
  ["(a[0],a[1]), (a[2],a[3]), ...", "(a[1],a[2]), (a[3],a[4]), ...", "Every pair (a[i], a[i+1])", "(a[0],a[n-1]), (a[1],a[n-2]), ..."], 0,
  "Even phases start at index 0, odd phases at index 1.")
Q(T, "calc", "4 ranks, odd phase. Who is rank 3's partner?",
  ["Nobody: rank 4 does not exist, so rank 3 is idle", "Rank 2", "Rank 0", "Rank 4"], 0,
  "Odd rank in an odd phase: partner = rank + 1 = 4, which is outside 0 to 3. Ranks 0 and 3 are idle in odd phases.")
Q(T, "calc", "Ranks 0 and 1 hold `15 27 33 36` and `35 36 42 43` and do a compare-split. What does rank 0 keep?",
  ["15 27 33 35", "36 36 42 43", "15 27 33 36", "35 36 42 43"], 0,
  "Merge to 15 27 33 35 36 36 42 43. The lower rank keeps the low half.")
Q(T, "concept", "With p ranks and blocks already sorted locally, at most how many phases are needed?",
  ["p", "n", "log2 p", "2p"], 0,
  "Phases are now over blocks, not elements. The lecture's 4-rank example finishes in 4 phases.")
Q(T, "concept", "Why does the MPI odd-even sort need no barriers?",
  ["Each rank's memory is private, and MPI_Sendrecv synchronizes the two ranks of a pair",
   "MPI inserts a barrier inside every Sendrecv", "All ranks run in lockstep", "It does need them, they are hidden in qsort"], 0,
  "There is no shared block for a fast rank to overwrite. Synchronization is a side effect of the exchange, and idle ranks wait for nobody.")
Q(T, "scenario", "Both ranks of a pair call `MPI_Ssend` to each other and then `MPI_Recv`. What happens?",
  ["Deadlock: each waits in Ssend for a receive the other never reaches", "It works, Ssend is buffered",
   "Only the lower rank finishes", "MPI reorders the calls"], 0,
  "`MPI_Ssend` does not return until the matching receive has started. Neither rank ever gets to its receive.")
Q(T, "concept", "Which step of Foster's methodology could **not** be carried over from the pthreads version?",
  ["Communication", "Partitioning", "The phase structure", "The local qsort"], 0,
  "In pthreads the partner's data was a shared read. In MPI it must be sent and received.")
Q(T, "concept", "Can rank 3 be in phase 2 while rank 2 is still finishing phase 0?",
  ["Yes, phases are not locked. Rank 3 simply waits in its phase 2 Sendrecv", "No, MPI keeps all ranks in the same phase",
   "No, that would be a race condition", "Only if a barrier is missing"], 0,
  "The lecture shows exactly this. It is correct, because the Sendrecv blocks until rank 2 arrives.")

# ---------------------------------------------------------------- 7. Heat distribution with MPI
T = "heat"
Q(T, "concept", "What is a **ghost row**?",
  ["A local copy of a row owned by a neighbouring rank", "A row of the plate that is always cold",
   "A row that no rank owns", "A row that is computed twice"], 0,
  "Each rank stores the row just above and just below its band. It reads them but never computes them.")
Q(T, "calc", "N = 16, 4 ranks. How many rows does rank 3 own, and where does it start?",
  ["3 rows, starting at global row 12", "4 rows, starting at row 12", "4 rows, starting at row 13", "3 rows, starting at row 13"], 0,
  "14 updatable rows, base 3, rem 2: counts 4, 4, 3, 3 and starts 1, 5, 9, 12.")
Q(T, "calc", "Rank 2 starts at global row 9. Which global row is its local row 3?",
  ["11", "12", "3", "10"], 0,
  "global = row_start - 1 + local = 9 - 1 + 3 = 11.")
Q(T, "concept", "What does a Sendrecv with `MPI_PROC_NULL` as the partner do?",
  ["Finishes at once and changes nothing", "Sends to rank 0", "Blocks forever", "Aborts the program"], 0,
  "So rank 0 and the last rank make the same two calls as everyone else, and their edge ghost keeps the cold boundary value.")
Q(T, "concept", "How does the MPI version check for convergence?",
  ["`MPI_Allreduce` with `MPI_MAX` on each rank's largest change", "Rank 0 receives every rank's grid",
   "A barrier, then rank 0 decides and broadcasts", "Each rank stops when its own band stops changing"], 0,
  "One Allreduce replaces barrier, reduction loop, barrier. Every rank gets the same number and decides the same way.")
Q(T, "concept", "Why is `MPI_Gatherv` used for frames instead of `MPI_Gather`?",
  ["The bands can have different numbers of rows", "Gather cannot handle doubles", "Gatherv is faster", "Gather needs tags"], 0,
  "Gather assumes every rank sends the same count. Gatherv takes a count and a displacement per rank.")
Q(T, "calc", "N = 16, 4 ranks with counts 4, 4, 3, 3. What is `displs[1]` for the Gatherv?",
  ["80", "64", "16", "5"], 0,
  "displs[r] = row_start[r] * N = 5 * 16 = 80.")
Q(T, "scenario", "Why is the halo exchange done **before** the compute phase in each iteration?",
  ["So the ghost rows hold the neighbours' latest values when cells read them", "So the timers start correctly",
   "Because Allreduce needs the ghost rows", "Order does not matter"], 0,
  "Exchanging after computing leaves stale ghosts. On 4 ranks that version still converged but took 89 iterations instead of 69 and gave wrong frames.")
Q(T, "scenario", "In the timing output, `comm` time is large even though each row is only about 4 KB. What does it mostly measure?",
  ["Waiting for slower neighbours: load imbalance", "Network bandwidth", "Time spent copying ghost rows", "Allreduce arithmetic"], 0,
  "A rank that reaches Sendrecv first waits with the clock running. Extra rows, cheap fixed cells and rank 0's file writes all cause skew.")

# ---------------------------------------------------------------- 8. Hardware and performance
T = "performance"
Q(T, "concept", "A GPU-style vector unit applying one instruction to many data values is which Flynn class?",
  ["SIMD", "MIMD", "SISD", "MISD"], 0,
  "Single instruction, multiple data. A multi-core CPU running independent threads is MIMD.")
Q(T, "concept", "What is the difference between UMA and NUMA?",
  ["UMA: same access time for every core. NUMA: local memory is faster than another chip's",
   "UMA is distributed memory, NUMA is shared memory", "NUMA is easier to program", "UMA allows more total memory"], 0,
  "NUMA exists because it allows more memory. UMA is easier to program because access times are equal.")
Q(T, "concept", "When do two CPUs slow each other down on a crossbar switch?",
  ["Only when they want the same memory module", "Whenever both access memory", "Never", "When more than two CPUs are connected"], 0,
  "Each CPU gets its own path through the switches. A bus, by contrast, has one shared path.")
Q(T, "calc", "A program takes 12 s serially and 4 s on 4 cores. What are the speedup and efficiency?",
  ["S = 3, E = 0.75", "S = 4, E = 1", "S = 3, E = 0.33", "S = 0.33, E = 3"], 0,
  "S = 12 / 4 = 3. E = S / p = 3 / 4 = 0.75.")
Q(T, "calc", "90% of a program parallelizes perfectly. What does Amdahl's law give on 4 cores?",
  ["About 3.08", "4", "About 3.6", "10"], 0,
  "1 / (0.9/4 + 0.1) = 1 / 0.325 = 3.08. The lecture's table shows 3.07.")
Q(T, "calc", "95% of a program parallelizes. What is the most speedup it can ever reach?",
  ["20", "95", "19", "100"], 0,
  "The limit is 1 / serial fraction = 1 / 0.05 = 20.")
Q(T, "concept", "As cores are added to a typical program, what happens to speedup and efficiency?",
  ["Speedup rises, efficiency falls", "Both rise", "Both fall", "Speedup falls, efficiency rises"], 0,
  "Each extra core helps less than the one before. In the lecture's table S goes 1.9, 3.6, 6.5, 10.8 while E goes 0.95, 0.9, 0.81, 0.675.")
Q(T, "concept", "Why do bigger problems usually parallelize better?",
  ["Overhead usually grows more slowly than the serial work", "Bigger problems have no serial part",
   "Amdahl's law does not apply to big problems", "The network gets faster"], 0,
  "With `T_parallel = T_serial / p + T_overhead`, overhead becomes a smaller share, so S and E both rise.")
Q(T, "concept", "A cluster whose nodes are each multi-core shared-memory machines is called:",
  ["A hybrid system", "A grid", "UMA", "SISD"], 0,
  "Shared memory inside each node, distributed memory between nodes. A grid is many clusters spread geographically.")

# ---------------------------------------------------------------- 9. GPGPU and Warp
T = "gpgpu"
Q(T, "concept", "In the stream model, what is a **kernel**?",
  ["A small function applied to every element of a stream", "The operating system core", "The GPU's memory controller", "The first element of a stream"], 0,
  "Kernels take streams in and produce streams out. The most common use is a map.")
Q(T, "concept", "Which rule makes kernels safe to run in parallel?",
  ["A thread's output may not depend on another thread's output", "Each thread may only read its own input element",
   "Kernels must return a value", "Kernels must use locks"], 0,
  "You may read any input element and write one output, but never depend on another output.")
Q(T, "concept", "What is the difference between SIMD and SIMT?",
  ["SIMD: one thread with wide registers. SIMT: many lockstep threads, each with its own registers",
   "SIMT is SIMD on a CPU", "SIMD has many program counters", "They are the same thing"], 0,
  "SIMT shares one program counter across a group of threads, but each has its own register file.")
Q(T, "scenario", "Half the threads in each group take the `if` branch and half the `else`. What does it cost?",
  ["The time of both branches added together", "The time of the longer branch", "The time of the shorter branch", "Nothing extra"], 0,
  "The group runs both paths, masking off the inactive threads each time.")
Q(T, "scenario", "A GPU port of a small program is slower than the CPU version. The most likely reason?",
  ["Copying data to and from the GPU over the bus costs more than the computation saves", "GPUs are slower at addition",
   "Warp only runs on one core", "The kernel has too few lines"], 0,
  "CPU and GPU usually have separate memories. For small problems, the copy dominates.")
Q(T, "concept", "In a Warp kernel, what does `wp.tid()` return?",
  ["This thread's index", "The number of threads", "The device name", "The output array"], 0,
  "Like `my_rank` in MPI. You write the body for one element and use the index to pick it.")
Q(T, "concept", "How does a Warp kernel return its results?",
  ["It writes them into an output array passed in as a parameter", "With a return statement", "Through a global variable", "It prints them"], 0,
  "Kernels return nothing. The host allocates the output with `wp.zeros` and passes it in `outputs=[...]`.")
Q(T, "concept", "Put the host steps in order.",
  ["NumPy data, `wp.array`, `wp.zeros`, `wp.launch`, `.numpy()`", "`wp.launch`, `wp.array`, `wp.zeros`, `.numpy()`, NumPy data",
   "`wp.zeros`, `wp.launch`, NumPy data, `wp.array`, `.numpy()`", "`wp.array`, `.numpy()`, `wp.launch`, `wp.zeros`, NumPy data"], 0,
  "Make the data, copy it into Warp arrays, allocate the output, launch, copy the result back.", )
Q(T, "concept", "GPGPU is an example of which kind of computing?",
  ["Heterogeneous: a CPU host and a GPU work together", "Homogeneous: every unit is the same kind of core",
   "Distributed memory only", "SISD"], 0,
  "Pthreads and MPI run on CPU cores only (homogeneous). GPGPU mixes CPU and GPU.")

# ---------------------------------------------------------------- 10. Image processing basics
T = "imaging"
Q(T, "calc", "A 3 x 3 mean filter is applied to this neighbourhood. What is the new centre value?",
  ["204", "249", "1835", "221"], 0,
  "Sum = 1835, and 1835 / 9 = 203.9, which rounds to 204.",
  code="131  134  193\n251  249  221\n220  206  230")
Q(T, "concept", "Why must a kernel centred on a pixel have odd dimensions?",
  ["So there is a single centre pixel", "So it can be normalized", "Because images have odd sizes", "So the sum is zero"], 0,
  "3 x 3, 5 x 5 and so on all have a middle cell to place over the pixel.")
Q(T, "concept", "Why are smoothing kernels normalized?",
  ["So a region of constant intensity keeps the same value", "To make them sum to zero", "So they run faster", "To sharpen edges"], 0,
  "Dividing by the coefficient sum keeps brightness unchanged and avoids bias.")
Q(T, "calc", "A 5 x 5 kernel on a 100 x 80 image with no border handling. How big is the processable region?",
  ["96 x 76", "98 x 78", "100 x 80", "95 x 75"], 0,
  "Half-width m = 2, so (M - 2m) x (N - 2m) = 96 x 76, starting at (2, 2).")
Q(T, "concept", "Which border strategy did the lecture call the most useful?",
  ["Reflected indexing", "Circular indexing", "Truncating the image", "Truncating the kernel"], 0,
  "Reflect out-of-range indices back inside, as if the image were mirrored. Circular indexing is rarely used.")
Q(T, "concept", "Which pixels are the **4-neighbours** of (x, y)?",
  ["(x+1,y), (x-1,y), (x,y+1), (x,y-1)", "The four diagonal pixels", "All 8 surrounding pixels", "(x+2,y), (x-2,y), (x,y+2), (x,y-2)"], 0,
  "Up, down, left, right. Adding the 4 diagonals gives the 8-neighbours.")
Q(T, "concept", "How do you apply a greyscale algorithm to an RGB image, as the lecture suggests?",
  ["Run it on each channel separately", "Average the three channels first, always", "Only use the green channel", "It cannot be done"], 0,
  "The course algorithms extend to colour by processing red, green and blue independently.")
Q(T, "scenario", "A convolution writes its results back into the input image as it goes. What is wrong?",
  ["Later pixels read neighbours that were already changed", "Nothing, it saves memory", "It only fails at the borders", "It makes the image darker"], 0,
  "Always read from the input and write to a separate output. On a GPU this is also the kernel rule.")

# ---------------------------------------------------------------- 11. Sharpening and smoothing
T = "filters"
Q(T, "concept", "What does a **low-pass** filter do to an image?",
  ["Smooths it: removes quick changes such as noise", "Sharpens edges", "Inverts the colours", "Keeps only edges"], 0,
  "It passes slow changes (low spatial frequency) and removes quick ones. It is also called a high-cut filter.")
Q(T, "calc", "The kernel with 8 in the centre and -1 around it is applied to a flat region where every pixel is 50. What is the result?",
  ["0", "50", "400", "-50"], 0,
  "8 x 50 - 8 x 50 = 0. The coefficients sum to 0, so flat regions give 0 and edges give large values.")
Q(T, "concept", "In unsharp masking, what is the edge image g?",
  ["The original minus a blurred copy", "The blurred copy minus the original", "The original times k", "The median of the neighbourhood"], 0,
  "g = f - S(f). The sharpened image is f + k g.")
Q(T, "concept", "Unsharp masking is called a high-boost filter when:",
  ["k > 1", "k < 0.2", "k = 0", "the blur is Gaussian"], 0,
  "Reasonable sharpening values are 0.2 to 0.7. Above 1 it is high-boost.")
Q(T, "concept", "Which are known limitations of unsharp masking?",
  ["It amplifies noise", "It overshoots at sharp edges", "It removes impulse noise completely", "It needs the median of the image"], [0, 1],
  "It emphasizes high frequencies, which includes noise, and it makes edges taller than they were.")
Q(T, "concept", "What happens to a Gaussian filter as sigma increases?",
  ["More blur, and the kernel gets bigger", "Less blur", "It becomes a sharpening filter", "It stops being symmetric"], 0,
  "The weights spread out and the kernel runs from -[3 sigma] to [3 sigma].")
Q(T, "calc", "A 3 x 3 neighbourhood has eight pixels of 10 and one of 255. What do a mean filter and a median filter give?",
  ["Mean about 37, median 10", "Mean 10, median 37", "Both about 37", "Both 10"], 0,
  "Mean = (80 + 255) / 9 = 37.2. The sorted middle value is 10, so the spike disappears.")
Q(T, "concept", "Why is a median filter not a convolution?",
  ["It sorts the values and picks one, which no fixed weighted sum can do", "It uses a 5 x 5 window",
   "It is applied after a Gaussian", "It only works on colour images"], 0,
  "Convolution is a weighted sum. Order-statistic filters are non-linear.")
Q(T, "concept", "Which kind of noise is a median filter best at removing?",
  ["Impulse (salt and pepper) noise", "Gaussian noise", "Motion blur", "Read noise from cold sensors"], 0,
  "It works when the noisy pixels are less than half the neighbourhood. Mean and Gaussian filters suit Gaussian noise.")
Q(T, "concept", "An image is both noisy and blurry. What order does the lecture recommend?",
  ["Remove the noise first, then sharpen", "Sharpen first, then denoise", "Only sharpen", "Order does not matter"], 0,
  "Sharpening amplifies noise, so denoise before you sharpen.")
