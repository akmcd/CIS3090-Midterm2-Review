title: GPGPU and Warp

- What lecture 15 is about:
    - Why GPUs exist, how their hardware differs from a CPU, and the stream programming model
    - How to write a first GPU kernel with Nvidia Warp
    - **GPU** (graphics processing unit): a processor with thousands of simple cores, built for graphics
    - **GPGPU** (general-purpose computing on GPUs): using that hardware for other work

- Why GPUs exist:
    - A game at 1920 x 1080 has about 2 million pixels per frame
    - At 60 frames per second that is about 120 million pixel colours per second
    - Each pixel needs several matrix and vector operations, and each of those takes dozens of CPU instructions
    - No CPU keeps up with that for a modern game, so dedicated hardware was built
    - 3D rendering is all coordinates and vectors (3 or 4 components) and transformation matrices: rotation, translation, scaling, projection
    - The same operation on huge amounts of data: it "feels a bit SIMD-y"

- What GPUs give up:
    - They are optimized for one thing: basic matrix and vector arithmetic
    - They skip complex branch logic and cache management, and spend most transistors on processing units
    - CPUs have about 2 to 96 cores (over 250 at the top end). GPUs have hundreds to thousands, over 10,000 on high-end cards
    - More cores means more pixels at once, so higher resolution or higher frame rate

- What GPGPU is used for:
    - Physics simulations: objects are points (vectors), forces are vectors and matrices
    - Machine learning: training adjusts network weights, which can be written as vector operations. GPGPU largely enabled the ML boom of the last 15 to 20 years
    - Image processing: pixels are points, and many image operations are matrices (lectures 16 and 17)
    - Also robotics, audio and video, science and finance

- The stream programming model:
    - **stream**: an ordered set of data of one type, expected to have thousands of elements or more
    - It can be simple (floats) or complex (points, triangles, matrices)
    - Operations on streams: copy them, index into them with another stream, and run **kernels** on them
    - **kernel**: a small function applied to entire streams. It takes one or more streams in and produces one or more streams out
    - The word comes from mathematics, and image processing uses it for a filter matrix (lecture 16)

- Kinds of kernel operation:
    - **map**: evaluate a function on every element, the most common use
    - **expansion**: more than one output element per input element
    - **reduction**: several elements combine into one output element
    - **filter**: only some input elements are output
    - Each step of a rendering pipeline can be one or more kernels, and several can be fused into one

- The rule that makes kernels parallel:
    - A kernel's outputs depend only on its inputs
    - Inside a kernel you may read any element of the input arrays and write one output
    - Your output may not depend on another thread's output
    - So everything a kernel needs is known when it is written, and each element can run on its own core
    - This is why a kernel that reads like a serial loop body can run on data-parallel hardware

- The GPGPU pattern:
    - Arrange the problem so the input is a stream
    - Write one or more kernels that operate on it. Several kernels run in sequence, only one is applied to a stream at a time
    - Load the data and the kernel, and run

- SIMD against SIMT:
    - **SIMD**: one thread with very wide registers. One fetch and decode, one register file, several execution lanes
    - **SIMT** (single instruction, multiple threads): many threads running in lockstep. One program counter, but each thread has its own register file
    - Multi-core CPU: multiple independent threads. x86 SSE vector unit: one thread with a wide data path. GPU: multiple lockstep threads

| | Threads | Program counters | Register files |
|---|---|---|---|
| Multi-core CPU (MIMD) | many, independent | one each | one each |
| Vector unit (SIMD) | one | one | one, very wide |
| GPU (SIMT) | many, in lockstep | one per group | one per thread |

- GPU hardware hierarchy:
    - **shading unit**: a small, simple unit that runs floating-point operations. Nvidia calls them CUDA cores
    - A shading unit often runs more than one SIMT thread
    - **compute unit**: a group of shading units, usually dozens and up to 128 or more
    - A GPU is many compute units

::: warn Branch divergence
- Threads in a lockstep group share one instruction stream
- If they take different branches of an `if`, the group runs both paths and masks off the threads that should not be active
- So divergent code costs the time of both branches added together
- Best practice: one flat data buffer, one kernel, uniform work on every element
:::

- Homogeneous against heterogeneous computing:
    - **homogeneous**: every execution unit is the same type. Pthreads and MPI both run on CPU cores
    - MPI nodes can differ a little, but the code must run on all of them: Intel with AMD is fine (both x86), Intel with ARM is not
    - **heterogeneous**: different kinds of processor work together. GPGPU is the example
    - **host**: the CPU side. It starts the program, loads the data stream and the compiled kernels, sends both to the GPU, runs the kernels and copies the results back

- The new cost: copying to the GPU:
    - Once data is on the GPU, kernels get direct memory access, like threads (and data races are possible)
    - But on most systems the CPU and GPU have separate memories, like distributed memory
    - Moving data to the GPU is a copy over the bus, and it is expensive
    - For small problems the copy can dominate, so a naive GPU port can be slower than the CPU version

- GPGPU libraries:
    - **CUDA**: Nvidia's proprietary platform. Only runs on Nvidia GPUs, and is the industry favourite
    - **OpenCL**: an open standard that runs on many platforms. Used where Nvidia hardware is not guaranteed, but declining
    - In both, the CPU code is C and the kernel is written in a separate kernel language
    - **Nvidia Warp**: the course's choice. Free, open source, and both the CPU code and the kernel are Python

- Why Warp:
    - Warp converts the Python to C++ and CUDA and compiles it at run time (just-in-time, JIT)
    - The same code runs on an Nvidia GPU in parallel, or on the CPU as a single serial thread
    - The course Docker container uses `device = "cpu"`, so you learn the model without the speedup
    - It hides compute units and the communication between them: you only deal with streams and kernels
    - The course pins Warp 1.16 (the newest release is past 1.20)

- The five CPU-side steps:
    - Step 1: Load or create the data, for example as a NumPy array
    - Step 2: Convert it to a Warp array with `wp.array()`
    - Step 3: Create an output Warp array filled with zeros with `wp.zeros()`
    - Step 4: Launch the kernel with `wp.launch()`
    - Step 5: Convert the output back with `.numpy()`

- Example: adding two arrays (Z = X + Y):
    - The course's `arrAdd.py` is not in the project files, so this is the program put together from the slide code (slides 38 to 43)
    - It is saved in `examples/extras/arrAdd.py`

    ```python
    import numpy as np
    import warp as wp

    device = "cpu"

    @wp.kernel
    def addArrays(x: wp.array(dtype=float),
                  y: wp.array(dtype=float),
                  z: wp.array(dtype=float)):
        tid = wp.tid()              # this thread's index
        z[tid] = x[tid] + y[tid]    # one element per thread

    hostX = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], dtype=np.float32)
    hostY = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], dtype=np.float32)

    x = wp.array(hostX, dtype=float, device=device)
    y = wp.array(hostY, dtype=float, device=device)
    z = wp.zeros(len(hostX), dtype=float, device=device)

    wp.launch(kernel=addArrays, dim=len(z), inputs=[x, y], outputs=[z], device=device)
    print(z.numpy())
    ```

::: run Real run with Warp 1.16.0 on the CPU
$ python3 arrAdd.py
Module __main__ 00c7d99 load on device 'cpu' took 3905.18 ms  (compiled)
[ 3.  5.  7.  9. 11. 13. 15. 17. 19. 21. 23. 25.]
:::

- Reading the example line by line:
    - `@wp.kernel` marks the function as a GPU kernel
    - Warp is statically typed, so every parameter needs a type: `wp.array(dtype=float)`
    - A kernel returns nothing. It writes its results into an output array that is passed in, here `z`
    - You write the body for **one** element. Warp launches one thread per element
    - `wp.tid()` gives the thread's index, the way `my_rank` does in MPI or the thread id in pthreads
    - `np.float32` is used on the host because 32-bit floats are what the GPU works with
    - `dim=len(z)` launches 12 threads, one per element
    - The slides describe `wp.launch` as taking 4 arguments, but the example also passes `outputs=[z]`
    - The first run takes seconds because Warp is compiling the kernel. Later runs reuse the compiled module

- Warp calls used so far:

| Call | What it does |
|---|---|
| `@wp.kernel` | marks a Python function as a kernel |
| `wp.array(data, dtype=float, device=device)` | copies a NumPy array into a Warp array |
| `wp.zeros(n, dtype=float, device=device)` | makes a Warp array of n zeros for output |
| `wp.tid()` | inside a kernel: this thread's index |
| `wp.launch(kernel=..., dim=..., inputs=[...], outputs=[...], device=...)` | runs the kernel on `dim` threads |
| `arr.numpy()` | copies a Warp array back to a NumPy array |
