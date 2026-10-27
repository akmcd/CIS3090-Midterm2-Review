title: The trapezoidal rule

- The goal:
    - Estimate the area under a curve f(x) between x = a and x = b
    - Split the interval into n equal strips and replace each strip's curve with a straight line, which makes a trapezoid
    - The course function is `f(x) = x*x`, and the true area from 0 to 3 is exactly 9

- The maths:
    - **h** is the width of every trapezoid: `h = (b - a) / n`
    - Area of one trapezoid: `(h / 2) * (f(x_i) + f(x_i+1))`
    - Whole estimate: `h * [ f(a)/2 + f(x_1) + ... + f(x_n-1) + f(b)/2 ]`
    - The middle points are counted twice (once for each neighbouring trapezoid), and the two end points once, which is why those two are halved
    - On a convex curve each trapezoid overestimates, on a concave curve it underestimates
    - As the trapezoids get narrower, the errors average out

- The serial code (this is `Trap` in every course version):

    {{code mpi_SendRec.c 141-157}}

    - Line 149: start with the two halved end points
    - Lines 150 to 153: add `f(x)` for each middle point
    - Line 154: multiply by `h` once at the end

- Designing the parallel version (lecture 11 follows these four steps):
    - **Partition**: give each process one slice of the interval
    - **Communicate**: everyone needs `a`, `b`, `n`, and the partial results must be added together
    - **Aggregate**: [[r0]] also does the input, the summing and the output
    - **Map**: [[r0]] sums, [[rx]] compute a slice and send the result to rank 0

- Each rank's slice:
    - `h = (b-a)/n` is the same on every rank
    - `local_n = n/comm_sz` is the number of trapezoids per rank
    - `local_a = a + my_rank*local_n*h` is where this rank's slice starts
    - `local_b = local_a + local_n*h` is where it ends
    - Each rank calls `Trap(local_a, local_b, local_n, h)` on its own slice
    - Example: a = 0, b = 3, n = 1024 on 4 ranks gives local_n = 256, so [[r2]] covers 1.5 to 2.25
    - The Trapezoid trace page lets you try other numbers

- The assumption that is easy to forget:
    - The code assumes `n` divides evenly by `comm_sz`
    - Integer division truncates, so leftover trapezoids are never computed
    - With n = 1024 on 3 ranks, `local_n` is 341 and only 1023 trapezoids are covered
    - The program then prints 8.9737 instead of about 9.0000 (checked by running it)
    - The slides say they assume even division to keep examples short
    - Textbook exercise 3.2 asks you to fix it

- The three versions in the course:
    - **Program 3.2**, the textbook's first version: a = 0, b = 3, n = 1024 hard-coded, results summed with a loop of Send and Recv
    - **mpi_trap2**, shipped here as `mpi_SendRec.c`: keyboard input sent to each rank with `MPI_Send`, results summed with a loop of `MPI_Recv`
    - **mpi_trap3**, shipped here as `mpi_Bcast.c`: `MPI_Bcast` for the input and `MPI_Reduce` for the sum
    - `mpi_trap4` uses MPI derived datatypes, which lecture 11 says have not been covered

- What changes between versions 2 and 3:
    - Input: three `MPI_Send` calls per other rank become three `MPI_Bcast` calls
    - Sum: an if/else with a loop becomes one `MPI_Reduce`
    - The maths and the `Trap` function do not change
    - Result for a = 0, b = 3, n = 1024 on 4 ranks is `9.000004291534424e+00` in both
    - It is a little above 9 because x squared is convex, so every trapezoid overestimates
