title: Parallel hardware and performance

- What lecture 14 is about:
    - Part 1: a map of parallel hardware, so you can name what kind of machine you are on
    - Part 2: speedup, efficiency, overhead and Amdahl's law. This is where the exam calculations come from
    - Textbook: section 2.3 (part 1) and sections 2.6.1 to 2.6.2 (part 2)

- Flynn's taxonomy:
    - Classifies a machine by how many instruction streams and data streams it runs at once
    - **SISD** (single instruction, single data): the serial von Neumann machine, one core
    - **SIMD** (single instruction, multiple data): one control unit drives many ALUs, all doing the same instruction on different data
    - **MISD** (multiple instruction, single data): almost no real systems
    - **MIMD** (multiple instruction, multiple data): independent cores, each with its own ALU, running asynchronously at their own pace
    - **ALU** (arithmetic logic unit): the part of a core that does the arithmetic

- SIMD in more detail:
    - With m ALUs, arithmetic can run up to m times faster
    - Traditional SIMD ALUs are synchronized and tied to the controller, they cannot store their own instructions
    - Good for simple loops over large arrays (data parallelism), not much else
    - **vector processor**: an example of SIMD. Vector registers hold 4 to 256 elements, and one operation applies to all of them
    - Vector pros: fast and easy, compilers vectorize loops well, high memory bandwidth because every loaded element is used
    - Vector cons: poor with irregular data structures (anything that is not an array), and hard to scale since longer vectors stop helping
    - Lecture 15 adds SIMT, the GPU's version of this idea

- MIMD comes in two memory models:
    - **shared memory**: all cores see one memory over an interconnect (pthreads)
    - **distributed memory**: each core has its own memory, and they talk over a network (MPI)

- Shared memory: UMA and NUMA:
    - **UMA** (uniform memory access): one big memory, every core has the same access time. Easier to program
    - **NUMA** (nonuniform memory access): each chip has its own local memory. Local access is fast, reaching another chip's memory is slower
    - NUMA exists because it allows much more total memory than UMA

- Distributed memory systems:
    - **cluster**: a collection of computers (nodes) on a commodity network such as Ethernet
    - Each node is usually a shared-memory machine, so a cluster is a **hybrid** system
    - **grid**: many clusters spread over a large geographic area, often **heterogeneous** (different hardware and operating systems)

- Shared-memory interconnects:
    - **bus**: one set of shared wires. Cheap and flexible, but more processors means more waiting for memory
    - **crossbar switch**: switches pick one of many paths, so different CPUs can reach different memory modules at the same time
    - The only crossbar conflict is two processors wanting the same memory module
    - A crossbar is faster than a bus but expensive

| | Bus | Crossbar |
|---|---|---|
| Paths | one, shared | many, chosen by switches |
| Cost | low | high |
| As processors are added | more waiting | still parallel, unless two want the same module |

- Speedup:
    - **speedup**: `S = T_serial / T_parallel`
    - Speedup depends less on input size than run time does, so it is the easier number to compare
    - **linear speedup**: `S = p`. The best case, with p cores running p times faster
    - It rarely happens. Thread management, critical sections, mutex calls, network I/O and file I/O all slow a parallel program
    - These overheads grow as threads or processes are added

- Efficiency:
    - **efficiency**: `E = S / p = T_serial / (p x T_parallel)`
    - How much useful speedup each core contributes, or the fraction of time each core spends on the actual problem
    - Lecture example:

| p | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| S | 1 | 1.9 | 3.6 | 6.5 | 10.8 |
| E | 1 | 0.95 | 0.9 | 0.81 | 0.675 |

- Reading the efficiency table:
    - S keeps rising but E keeps falling
    - Each extra processor helps, but less than the one before
    - Example: 6.5 / 8 = 0.8125, which the lecture rounds to 0.81

- Overhead:
    - Real parallel time: `T_parallel = T_serial / p + T_overhead`
    - The ideal case is the first term alone
    - When the problem grows, overhead usually grows more slowly than `T_serial`
    - Then both speedup and efficiency go up, because overhead is a smaller share of the work
    - This is why bigger problems parallelize better

- Amdahl's law:
    - Even with zero overhead, the part of the program that cannot be parallelized caps the speedup
    - `S = 1 / (parallel_fraction / p + serial_fraction)`, where the two fractions add up to 1
    - As p grows without limit, `parallel_fraction / p` goes to 0, so S approaches `1 / serial_fraction`

- Amdahl worked example (lecture):
    - `T_serial = 20` s and 90% can be parallelized perfectly
    - Parallel part: `0.9 x 20 / p = 18 / p` s. Serial part: `0.1 x 20 = 2` s, whatever p is
    - `T_parallel = 18/p + 2`, so `S = 20 / (18/p + 2) = 1 / (0.9/p + 0.1)`

| p | 1 | 2 | 4 | 8 | 16 |
|---|---|---|---|---|---|
| S | 1 | 1.82 | 3.08 | 4.71 | 6.4 |
| E | 1 | 0.91 | 0.77 | 0.59 | 0.40 |

- About that table:
    - The lecture shows 3.07 and 4.7, it cuts the decimals off. 1 / (0.225 + 0.1) = 3.077, so 3.08 when rounded
    - Even at p = 16 the speedup is only 6.4, and the limit is 10

- The speedup ceiling:

| Parallel fraction | 50% | 90% | 95% | 99% |
|---|---|---|---|---|
| Serial fraction | 0.5 | 0.1 | 0.05 | 0.01 |
| Max speedup (1 / serial) | 2 | 10 | 20 | 100 |

- Using Amdahl's law in practice:
    - Time the serial part over several trial runs and work out what fraction of the run it is
    - That gives the maximum useful number of cores, so you can decide what hardware or cloud capacity is worth buying
    - With a parallel fraction of 1 and serial fraction of 0, S = p: linear speedup

::: note Super-linear speedup
- The lecture says Amdahl's law shows super-linear speedup (S > p) will not happen "as a result of parallelization"
- That is true of the formula: S can never exceed p in it
- In real runs S > p is sometimes measured for other reasons, for example the data fits in the combined caches of many cores but not one
- So read the claim as "parallelism alone cannot give you more than p"
:::

- Quick calculation drill:
    - 80% parallel, p = 8: `1 / (0.8/8 + 0.2) = 1 / 0.3 = 3.33`, E = 3.33 / 8 = 0.42
    - 80% parallel, p as large as you like: `1 / 0.2 = 5`
    - Measured `T_serial = 12` s, `T_parallel = 4` s on 4 cores: S = 3, E = 0.75
