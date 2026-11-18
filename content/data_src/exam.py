# Practice Exam A: 40 fresh questions, none repeated from the quiz bank. Same fields as bank.py.

EXAM = []


def Q(topic, kind, q, options, answer, why, code=None, ctx=None):
    EXAM.append(dict(topic=topic, kind=kind, q=q, options=options, answer=answer, why=why, code=code, ctx=ctx))


# ---------- MPI basics ----------
Q("concepts", "concept", "What does `MPI_Comm_size(MPI_COMM_WORLD, &comm_sz)` store in `comm_sz`?",
  ["The number of processes in the communicator", "This process's rank", "The size of the largest message", "The number of cores on the machine"], 0,
  "`MPI_Comm_rank` gives the rank. `MPI_Comm_size` gives how many processes mpiexec started.")
Q("concepts", "concept", "Lecture 09 compares a communicator to what?",
  ["A radio channel that processes listen on", "A shared whiteboard", "A queue of tasks", "A mutex"], 0,
  "Processes on different communicators do not pick up each other's messages, like different radio channels.")
Q("concepts", "scenario", "Why do the course programs have the other ranks send their greetings to rank 0 instead of printing them directly?",
  ["So the output appears in a fixed order", "Because only rank 0 is allowed to print", "To test MPI_Bcast", "Because printf is not thread-safe"], 0,
  "Every rank may print, but the order is nondeterministic. Funnelling the text through rank 0 fixes the order.")
Q("method", "calc", "This runs on 4 processes. How many lines are printed, and in what order?",
  ["3 lines, from ranks 1, 2, 3 in that order", "4 lines in any order", "3 lines in any order", "1 line"], 0,
  "Ranks 1 to 3 each send one value. Rank 0 receives from source 1, then 2, then 3, and prints each one, so the order is fixed.",
  code="if (rank != 0) {\n   MPI_Send(&rank, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);\n} else {\n   for (int q = 1; q < size; q++) {\n      MPI_Recv(&v, 1, MPI_INT, q, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);\n      printf(\"%d\\n\", v);\n   }\n}")
Q("method", "scenario", "Same program, but the receive uses `MPI_ANY_SOURCE` instead of `q`. What changes?",
  ["The three lines can come out in any order", "It hangs", "Only one line is printed", "Nothing at all"], 0,
  "Rank 0 still receives exactly 3 messages, but takes them in whatever order they arrive.")
Q("method", "scenario", "This runs on 3 processes. What is wrong with it?",
  ["Rank 2 sends a message that no receive matches", "Rank 0 receives twice", "The tags do not match", "Nothing"], 0,
  "Rank 0 receives only from rank 1. Rank 2's send has no partner: depending on buffering it either blocks forever or the message is lost. Sends and receives must pair up one to one.",
  code="if (rank > 0) MPI_Send(&x, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);\nif (rank == 0) { MPI_Recv(&y, 1, MPI_INT, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE); printf(\"%d\\n\", y); }")
Q("sendrecv", "concept", "Which of these must agree for a send to match a receive?",
  ["The communicator", "The tag (or the receive uses MPI_ANY_TAG)", "The variable names in the two programs", "The source and destination ranks"], [0, 1, 3],
  "Variable names never matter. Communicator, tag and the two ranks do, and the buffers must be compatible.")
Q("sendrecv", "concept", "Why is the element count a function call (`MPI_Get_count`) instead of a field of `MPI_Status`?",
  ["It depends on the datatype you ask about", "Status has no room for it", "It is only known after MPI_Finalize", "It is the same as status.MPI_TAG"], 0,
  "The same bytes are a different number of elements as MPI_CHAR or MPI_INT, and computing it costs a little.")
Q("sendrecv", "concept", "What does `MPI_Ssend` guarantee when it returns?",
  ["The matching receive has started", "The message was buffered", "Nothing more than MPI_Send", "The receiver has printed the data"], 0,
  "That is why swapping MPI_Send for MPI_Ssend is the test for an unsafe program.")
Q("collectives", "calc", "Four ranks each contribute `rank * 2` to `MPI_Allreduce` with `MPI_MAX`. What does rank 1 receive?",
  ["6", "2", "12", "0"], 0,
  "Contributions are 0, 2, 4, 6. The maximum is 6, and Allreduce gives it to every rank.")
Q("collectives", "concept", "Which collective gives every process the whole gathered array?",
  ["MPI_Allgather", "MPI_Gather", "MPI_Scatter", "MPI_Bcast"], 0,
  "Gather collects onto one destination. Allgather leaves the full array on everyone.")
Q("collectives", "scenario", "After `MPI_Gather` with a chunk of 2 from each of 3 ranks, in what order are the chunks stored on the destination?",
  ["Rank 0's chunk first, then rank 1's, then rank 2's", "In the order they arrive", "Reverse rank order", "Destination's chunk last"], 0,
  "Gather places chunks in rank order, regardless of arrival order.")
Q("collectives", "concept", "Which statement about `MPI_Barrier` is true?",
  ["No process returns from it until every process has entered it", "It sends data to rank 0", "Only rank 0 calls it", "It is required before every collective"], 0,
  "It synchronizes without moving data. The heat program uses it once, to start the timers together.")
Q("trapezoid", "calc", "a = 1, b = 3, n = 8. What is h?",
  ["0.25", "0.5", "2", "0.125"], 0,
  "h = (b - a) / n = 2 / 8 = 0.25.")
Q("trapezoid", "concept", "In the parallel trapezoid design, which job is aggregated onto rank 0?",
  ["Reading the input, summing the results and printing", "Computing every trapezoid", "Choosing h", "Nothing, all ranks are identical"], 0,
  "Every rank computes its slice. Rank 0 also handles input, the sum and the output.")

# ---------- Case studies ----------
Q("odd_even", "calc", "Start with `5 9 4 3`. What is the list after the first (even) phase of odd-even transposition sort?",
  ["5 9 3 4", "5 4 9 3", "3 4 5 9", "9 5 4 3"], 0,
  "Even phase compare-swaps (5,9) and (4,3). Only the second pair swaps.")
Q("odd_even", "concept", "In the MPI odd-even sort, what is the first thing every rank does with its block?",
  ["Sorts it locally with qsort", "Sends it to rank 0", "Splits it in half", "Waits at a barrier"], 0,
  "The local sort needs no communication. After that, every phase is exchange and merge.")
Q("odd_even", "concept", "In an even phase, which ranks call `Merge_keep_high`?",
  ["Odd ranks", "Even ranks", "Rank 0 only", "The last rank only"], 0,
  "In an even phase, pairs are (0,1), (2,3): the odd rank is the higher member and keeps the high half.")
Q("odd_even", "scenario", "The naive Send-then-Recv odd-even sort passes every test with 16 numbers. What should you conclude?",
  ["Nothing yet: it may only work because small messages are buffered", "It is correct", "MPI_Send is synchronous", "Barriers would make it faster"], 0,
  "The bug is latent. Large blocks are not buffered and the pairs deadlock.")
Q("heat", "calc", "N = 20, 3 ranks. How many rows does each rank own?",
  ["6, 6, 6", "7, 7, 6", "6, 6, 8", "5, 5, 8"], 0,
  "updatable_rows = 18, base = 6, rem = 0. Every rank gets 6.")
Q("heat", "calc", "N = 16, 4 ranks. What is the total of all `recv_counts` in the Gatherv, and why is it not 256?",
  ["224: rows 0 and 15 are fixed and never sent", "256: every row is sent", "192: the ghost rows are not sent", "240: only row 0 is missing"], 0,
  "14 updatable rows x 16 columns = 224. The edge rows already sit in rank 0's calloc'd grid.")
Q("heat", "concept", "A rank with `my_rows` owned rows allocates how many rows per grid buffer?",
  ["my_rows + 2", "my_rows", "N", "my_rows + 1"], 0,
  "One ghost row above and one below.")
Q("heat", "scenario", "One rank fails a malloc and simply returns from main. What happens to the others?",
  ["They hang at the next collective or exchange", "They finish normally", "MPI restarts that rank", "They all exit at once"], 0,
  "That is why the code calls MPI_Abort, which stops every process.")
Q("heat", "concept", "In lecture 13's pthreads-to-MPI summary, what replaced \"barrier, reduction, barrier\"?",
  ["One MPI_Allreduce", "Two MPI_Barrier calls", "MPI_Gatherv", "A mutex"], 0,
  "Allreduce combines the local maxima, delivers the result to everyone, and nobody leaves early.")

# ---------- Performance ----------
Q("performance", "calc", "80% of a program parallelizes. What does Amdahl's law give on 8 cores?",
  ["About 3.33", "8", "6.4", "5"], 0,
  "1 / (0.8/8 + 0.2) = 1 / 0.3 = 3.33.")
Q("performance", "calc", "Speedup on 16 cores is 10.8. What is the efficiency?",
  ["0.675", "1.48", "0.81", "10.8"], 0,
  "E = 10.8 / 16 = 0.675.")
Q("performance", "concept", "Which are disadvantages of vector processors, according to lecture 14?",
  ["They handle irregular data structures badly", "They are hard to scale: longer vectors stop helping", "Compilers cannot vectorize loops", "They waste loaded data"], [0, 1],
  "Compilers are good at vectorizing, and every loaded element is used, which gives high memory bandwidth.")
Q("performance", "concept", "What is a **grid**, as opposed to a cluster?",
  ["Many clusters spread over a large geographic area, often with mixed hardware", "A cluster on one switch",
   "A single NUMA machine", "A GPU's compute units"], 0,
  "Grids are often heterogeneous: different hardware and operating systems.")
Q("performance", "concept", "What does Amdahl's law say about super-linear speedup (S > p)?",
  ["It cannot come from parallelism alone: the formula never exceeds p", "It is common for large p", "It happens when the serial fraction is negative", "It is required for efficiency 1"], 0,
  "With a parallel fraction of 1 the formula gives exactly p. Measured S > p has other causes, such as caches.")

# ---------- GPUs ----------
Q("gpgpu", "calc", "About how many pixel colours per second does a 1920 x 1080 game at 60 FPS need?",
  ["About 120 million", "About 2 million", "About 60 thousand", "About 2 billion"], 0,
  "1920 x 1080 is about 2 million pixels, times 60 frames is about 120 million.")
Q("gpgpu", "concept", "What do GPUs give up to fit thousands of cores?",
  ["Complex branch logic and cache management", "Floating-point units", "Memory", "Parallelism"], 0,
  "Most transistors go to processing units, so control logic is simple.")
Q("gpgpu", "concept", "What does `wp.launch(kernel=addArrays, dim=len(z), ...)` with 12-element arrays do?",
  ["Runs the kernel on 12 threads, one per element", "Runs the kernel once over all 12 elements", "Runs it 12 times on the CPU in order, always", "Launches 12 GPUs"], 0,
  "dim is the number of threads. Each thread finds its element with wp.tid().")
Q("gpgpu", "concept", "Why does the first run of a Warp program take several seconds?",
  ["Warp compiles the Python kernel to C++/CUDA at run time", "The GPU warms up", "NumPy loads slowly", "MPI starts"], 0,
  "It is just-in-time compilation. Later runs reuse the compiled module.")
Q("gpgpu", "concept", "Which kernel operation outputs only some of its input elements?",
  ["Filter", "Map", "Expansion", "Reduction"], 0,
  "Map: one per element. Expansion: more out than in. Reduction: several combine into one.")

# ---------- Images ----------
Q("imaging", "concept", "What does an RGBA image add to RGB?",
  ["An alpha channel for transparency", "A second red channel", "Brightness", "An extra resolution level"], 0,
  "A for alpha.")
Q("imaging", "calc", "Row `10 20 30 40 50`, kernel half-width 1, reflected indexing as described on the site. Which value is read for index -1?",
  ["20", "10", "50", "0"], 0,
  "Index -1 reflects to index 1, which holds 20.")
Q("imaging", "concept", "The pyramidal 5 x 5 kernel has rows `1 2 3 2 1`, `2 4 6 4 2`, `3 6 9 6 3`, `2 4 6 4 2`, `1 2 3 2 1`. What is its normalization factor?",
  ["1/81", "1/25", "1/9", "1/27"], 0,
  "The coefficients sum to 81.")
Q("filters", "calc", "Three columns of 10, 10, 50 under the 8-centre high-pass kernel. What is the response?",
  ["-120", "0", "120", "40"], 0,
  "Centre 8 x 10 = 80. Neighbours: 10+10+50 above, 10+50 beside, 10+10+50 below = 200. 80 - 200 = -120.",
  code="10  10  50\n10  10  50\n10  10  50")
Q("filters", "concept", "Which filter is isotropic and gives more weight to central pixels than to the edges of the window?",
  ["Gaussian", "Box (mean)", "Median", "High-pass"], 0,
  "The Gaussian weights fall off with distance and are rotationally symmetric.")
Q("filters", "scenario", "A median filter is applied repeatedly with a large window. What effect can appear?",
  ["Posterization: flat patches with hard boundaries", "Overshoot at edges", "Brighter noise", "A sepia tone"], 0,
  "Repeated median filtering flattens regions into patches. The lecture notes it can look cool.")
