/*
 * heatDiffusionMpi.c
 *
 * Shared-memory (Pthreads) implementation of the Heat Diffusion case study.
 * See the lecture titles "Case study - heat distribution simulation (with pthreads)"
 * for a discussion of this algorithm 
 * 
 *
 * Build:   mpicc -O2 -Wall -lm -o heatDiffusionMpi heatDiffusionMpi.c
 * Run:     mpirun -np <ranks> ./heatDiffusionMpi [n] [k] [epsilon] [maxIters] [frameStride] [outdir] [format]
 *          format: "pgm" (default) or "txt" -- see heatDiffusionPthreads.c;
 *          same text format on both units, so frames can be diffed directly.
 *
 * Note that we have an argv chnage relative to Pthreads: thread count was argv[2] there.
 * Here, rank count comes from mpirun, not the program, so every remaining
 * argument shifts down by one slot.
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mpi.h>

// Shared globals for all threads

int     n;                  /* grid is n x n */
int     hotLo, hotHi;       /* hot block occupies [hotLo, hotHi) x [hotLo, hotHi) */
double  epsilon;
int     maxIters;
int     frameStride;
char    outDir[512];
int     textFrames = 0;     /* 0 = PGM (default), 1 = plain-text frames */

#define IDX(i, j) ((i) * n + (j))

int isFixed(int i, int j);
void initLocalGrid(double *g, int rowStart, int myRows);
void writePgmFrame(const double *g, int frameNum);
void writeTxtFrame(const double *g, int frameNum);
void buildDecompositionTables(int commSz, int updatableRows,
                               int *rowStartTbl, int *rowCountTbl);

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    int myRank, commSz;
    MPI_Comm_rank(MPI_COMM_WORLD, &myRank);
    MPI_Comm_size(MPI_COMM_WORLD, &commSz);

    // Default simulation parameters

    n           = (argc > 1) ? atoi(argv[1]) : 514;
    int k       = (argc > 2) ? atoi(argv[2]) : 96;
    epsilon     = (argc > 3) ? atof(argv[3]) : 1e-4;
    maxIters    = (argc > 4) ? atoi(argv[4]) : 50000;
    frameStride = (argc > 5) ? atoi(argv[5]) : 20;
    snprintf(outDir, sizeof(outDir), "%s", (argc > 6) ? argv[6] : "frames");
    textFrames  = (argc > 7) ? (strcmp(argv[7], "txt") == 0) : 0;

    /* 
     * Every rank parses argv independently.
     * mpirun provides it to all ranks in practice, though  the MPI standard 
     * does not guarantee this. 
     * Every rank also evaluates the checks below identically, so
     * validation failures are detected everywhere at once. However, only rank 0
     * prints (since it's guaranteed to access STDOUT on user's machine)
     */

    if (n < 3) {
        if (myRank == 0) fprintf(stderr, "N must be >= 3\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    int updatableRows = n - 2;
    if (commSz < 1 || commSz > updatableRows) {
        if (myRank == 0) {
            fprintf(stderr, "comm_sz must be between 1 and N-2 (updatable rows); got %d\n", commSz);
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    hotLo = (n - k) / 2;
    hotHi = hotLo + k;
    if (hotLo <= 0 || hotHi >= n - 1) {
        if (myRank == 0) {
            fprintf(stderr, "hot block (K=%d) doesn't fit inside boundary for N=%d\n", k, n);
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    if (myRank == 0) {
        char cmd[600];
        snprintf(cmd, sizeof(cmd), "mkdir -p %s", outDir);
        if (system(cmd) != 0) {
            fprintf(stderr, "warning: could not create output dir %s\n", outDir);
        }
    }

    // row-strip decomposition over updatable rows [1, n-2]
    int *rowStartTbl = calloc((size_t)commSz, sizeof(int));
    int *rowCountTbl = calloc((size_t)commSz, sizeof(int));
    if (!rowStartTbl || !rowCountTbl) {
        fprintf(stderr, "rank %d: allocation failure (decomposition tables)\n", myRank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    buildDecompositionTables(commSz, updatableRows, rowStartTbl, rowCountTbl);

    int rowStart = rowStartTbl[myRank];   /* inclusive: first global row this rank owns */
    int myRows   = rowCountTbl[myRank];

    // MPI_PROC_NULL for the top / bottom rows
    int upNeighbour   = (myRank == 0)           ? MPI_PROC_NULL : myRank - 1;
    int downNeighbour = (myRank == commSz - 1) ? MPI_PROC_NULL : myRank + 1;

    /* Gatherv descriptor
     * Every rank computes it for simplicity, but
     * only rank 0's call actually uses recvCounts/displs/recvbuf. 
     */
    int *recvCounts = malloc(sizeof(int) * (size_t)commSz);
    int *displs     = malloc(sizeof(int) * (size_t)commSz);
    if (!recvCounts || !displs) {
        fprintf(stderr, "rank %d: allocation failure (gatherv tables)\n", myRank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    for (int r = 0; r < commSz; r++) {
        recvCounts[r] = rowCountTbl[r] * n;
        displs[r]     = rowStartTbl[r] * n;
    }

    double *curGrid  = malloc(sizeof(double) * (size_t)(myRows + 2) * (size_t)n);
    double *nextGrid = malloc(sizeof(double) * (size_t)(myRows + 2) * (size_t)n);
    if (!curGrid || !nextGrid) {
        fprintf(stderr, "rank %d: allocation failure (grid buffers)\n", myRank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    initLocalGrid(curGrid, rowStart, myRows);
    memcpy(nextGrid, curGrid, sizeof(double) * (size_t)(myRows + 2) * (size_t)n);

    // rank 0 only: full-grid assembly buffer for Gatherv + PGM output.
    double *fullGrid = NULL;
    if (myRank == 0) {
        fullGrid = calloc((size_t)n * (size_t)n, sizeof(double));
        if (!fullGrid) {
            fprintf(stderr, "rank 0: allocation failure (full_grid)\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
    }

    // Timing variables
    double computeTime = 0.0, commTime = 0.0, reduceTime = 0.0, outputTime = 0.0;

    MPI_Barrier(MPI_COMM_WORLD);
    double tStart = MPI_Wtime();

    int iteration = 0;
    int converged = 0;

    while (1) {
        // halo exchange on curGrid
        double t0 = MPI_Wtime();
        MPI_Sendrecv(&curGrid[IDX(1, 0)],           n, MPI_DOUBLE, upNeighbour,   0,
                     &curGrid[IDX(0, 0)],            n, MPI_DOUBLE, upNeighbour,   0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        MPI_Sendrecv(&curGrid[IDX(myRows, 0)],      n, MPI_DOUBLE, downNeighbour, 0,
                     &curGrid[IDX(myRows + 1, 0)],   n, MPI_DOUBLE, downNeighbour, 0,
                     MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        double t1 = MPI_Wtime();
        commTime += t1 - t0;

        // compute phase
        double localMax = 0.0;
        for (int localI = 1; localI <= myRows; localI++) {
            int globalI = rowStart - 1 + localI;
            for (int j = 1; j < n - 1; j++) {
                if (isFixed(globalI, j)) {
                    nextGrid[IDX(localI, j)] = curGrid[IDX(localI, j)];  /* fixed cells never change */
                    continue;
                }
                double val = 0.25 * (curGrid[IDX(localI - 1, j)] + curGrid[IDX(localI + 1, j)] +
                                      curGrid[IDX(localI, j - 1)] + curGrid[IDX(localI, j + 1)]);
                nextGrid[IDX(localI, j)] = val;
                double diff = fabs(val - curGrid[IDX(localI, j)]);
                if (diff > localMax) localMax = diff;
            }
        }
        double t2 = MPI_Wtime();
        computeTime += t2 - t1;

        // global convergence check
        double globalMax;
        MPI_Allreduce(&localMax, &globalMax, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
        double t3 = MPI_Wtime();
        reduceTime += t3 - t2;

        // swap curGrid with nextGrid so 'curGrid' is the freshly computed frame 
        double *tmp = curGrid;
        curGrid = nextGrid;
        nextGrid = tmp;

        /* 
         * Frame write. Every rank evaluates this branch identically, so the
         * Gatherv call below is always a valid collective call. 
         */
        if (iteration % frameStride == 0) {
            MPI_Gatherv(&curGrid[IDX(1, 0)], myRows * n, MPI_DOUBLE,
                        fullGrid, recvCounts, displs, MPI_DOUBLE,
                        0, MPI_COMM_WORLD);
            if (myRank == 0) {
                if (textFrames) writeTxtFrame(fullGrid, iteration / frameStride);
                else writePgmFrame(fullGrid, iteration / frameStride);
            }
        }
        double t4 = MPI_Wtime();
        outputTime += t4 - t3;

        if (globalMax < epsilon || iteration >= maxIters - 1) {
            converged = 1;
        }
        iteration++;

        if (converged) break;
    }

    double tEnd = MPI_Wtime();
    double elapsed = tEnd - tStart;

    //Compute the timings using MPI tools
    double maxCompute, maxComm, maxReduce, maxOutput, maxElapsed;
    MPI_Reduce(&computeTime, &maxCompute, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&commTime,    &maxComm,    1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&reduceTime,  &maxReduce,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&outputTime,  &maxOutput,  1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&elapsed,     &maxElapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (myRank == 0) {
        printf("N=%d ranks=%d K=%d eps=%g -> %d iterations, %.3f sec, %d frames -> %s/\n",
               n, commSz, k, epsilon, iteration, maxElapsed, iteration / frameStride + 1, outDir);
        printf("compute=%.3f comm=%.3f allreduce=%.3f output=%.3f\n",
               maxCompute, maxComm, maxReduce, maxOutput);
    }

    free(curGrid);
    free(nextGrid);
    free(rowStartTbl);
    free(rowCountTbl);
    free(recvCounts);
    free(displs);
    if (fullGrid) free(fullGrid);

    MPI_Finalize();
    return 0;
}

int isFixed(int i, int j) {
    if (i == 0 || i == n - 1 || j == 0 || j == n - 1) return 1;           /* boundary */
    if (i >= hotLo && i < hotHi && j >= hotLo && j < hotHi) return 1;     /* hot block */
    return 0;
}

/* 
 * Initializes local rows 0..myRows+1 (ghost rows included) from global
 * coordinates. Ghost rows at the two ends land on the true global
 * boundary (row 0 or row n-1) and get the correct cold value permanently.
 * Ghost rows in the interior get a transient value here that
 * is irrelevant, since halo exchange overwrites them before first use. 
 */
void initLocalGrid(double *g, int rowStart, int myRows) {
    for (int localI = 0; localI <= myRows + 1; localI++) {
        int globalI = rowStart - 1 + localI;
        for (int j = 0; j < n; j++) {
            if (globalI == 0 || globalI == n - 1 || j == 0 || j == n - 1) {
                g[IDX(localI, j)] = 0.0;   /* cold boundary */
            } else if (globalI >= hotLo && globalI < hotHi && j >= hotLo && j < hotHi) {
                g[IDX(localI, j)] = 1.0;   /* hot block */
            } else {
                g[IDX(localI, j)] = 0.0;   /* plate starts cold everywhere else */
            }
        }
    }
}

// Save individual sumulation/animation frame
void writePgmFrame(const double *g, int frameNum) {
    char path[600];
    snprintf(path, sizeof(path), "%s/frame_%05d.pgm", outDir, frameNum);
    FILE *f = fopen(path, "wb");
    if (!f) {
        fprintf(stderr, "warning: could not open %s for writing\n", path);
        return;
    }
    fprintf(f, "P5\n%d %d\n255\n", n, n);
    unsigned char *row = malloc((size_t)n);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            double v = g[IDX(i, j)];
            if (v < 0.0) v = 0.0;
            if (v > 1.0) v = 1.0;
            row[j] = (unsigned char)(v * 255.0 + 0.5);
        }
        fwrite(row, 1, (size_t)n, f);
    }
    free(row);
    fclose(f);
}

/* 
 * Text-based frame dump
 * Added for sanity-checking and to get data for lecture slides
 */
void writeTxtFrame(const double *g, int frameNum) {
    char path[600];
    snprintf(path, sizeof(path), "%s/frame_%05d.txt", outDir, frameNum);
    FILE *f = fopen(path, "w");
    if (!f) {
        fprintf(stderr, "warning: could not open %s for writing\n", path);
        return;
    }
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            // Output used to generate the data for Pthread vs MPI diagnostics
            // fprintf(f, j == 0 ? "%.17g" : " %.17g", g[IDX(i, j)]);

            // Output used to generate the data in lecture slides
            fprintf(f, j == 0 ? "%.0g" : " %.0g", roundf(9*g[IDX(i, j)]));
        }
        fprintf(f, "\n");
    }
    fclose(f);
}

/* 
 * Distribute work between MPI rnaks:
 * Fills rowStartTbl[r] / rowCountTbl[r] for every rank r, using the
 * same base + (r < rem ? 1 : 0) formula as the Pthreads tArgs[] loop. 
 */
void buildDecompositionTables(int commSz, int updatableRows,
                               int *rowStartTbl, int *rowCountTbl) {
    int base = updatableRows / commSz;
    int rem  = updatableRows % commSz;
    int row = 1;
    for (int r = 0; r < commSz; r++) {
        int rowsForR = base + (r < rem ? 1 : 0);
        rowStartTbl[r] = row;
        rowCountTbl[r] = rowsForR;
        row += rowsForR;
    }
}
