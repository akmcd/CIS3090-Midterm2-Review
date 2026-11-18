title: Image processing basics
source: Lecture 16
lead: An image is a matrix of numbers. Most filters compute each new pixel as a weighted sum of its neighbours, which is called convolution, and the image borders need special handling.

- What lecture 16 is about:
    - The image-processing ideas needed for A3: how images are stored, neighbourhoods, convolution and kernels, and what to do at the borders
    - Images are loaded with PIL (the Python Imaging Library) as a matrix of pixel values, which can be passed to Warp as a stream

- How images are stored:
    - **greyscale image**: one matrix of intensities, one number per pixel
    - **colour image**: three matrices (red, green, blue), or one matrix of 3-value vectors
    - **RGBA**: adds a fourth channel, **alpha**, for transparency
    - The examples use greyscale because one matrix is simpler
    - To process a colour image, run the same algorithm on each channel separately

- Filtering:
    - **filtering**: removing "impurities" from an image, such as noise. Also called image restoration or enhancement
    - It covers noise removal, sharpening and contrast enhancement
    - The word is also used loosely for effects such as a sepia tone

- Neighbourhoods:
    - A pixel's new value is computed from its old value and the pixels around it, its **neighbourhood**
    - **4-neighbours** of (x, y): (x+1, y), (x-1, y), (x, y+1), (x, y-1)
    - **8-neighbours**: the 4-neighbours plus the 4 diagonals (x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)
    - On the border of the image, some neighbours fall outside it
    - The 3 x 3 neighbourhood of (x, y):

        ```
        x-1,y-1   x-1,y   x-1,y+1
        x,y-1     x,y     x,y+1
        x+1,y-1   x+1,y   x+1,y+1
        ```

- Convolution:
    - **convolution**: the new value at a pixel is a weighted sum of the intensities in the neighbourhood around it
    - The weights come from a **convolution kernel**, also called a **mask** or **filter**: a small matrix the same size as the neighbourhood
    - A neighbourhood centred on a pixel must have odd dimensions: 3 x 3, 5 x 5, ...
    - Formula for a 3 x 3 kernel: `g(x, y) = sum over i, j in -1..1 of w(i, j) * f(x + i, y + j)`
    - `f` is the input image, `g` the output image, `w` the kernel

- The convolution process, step by step:
    - Step 1: Place the centre of the kernel over a pixel P in the input image
    - Step 2: Multiply each pixel in the k x k neighbourhood by the kernel coefficient on top of it
    - Step 3: Add up all the products
    - Step 4: Write the (normalized) sum into position P of the **output** image
    - Always read from the input and write to a separate output, so later pixels still see the original values

- Worked example:

    ::: eg 3 x 3 mean filter on the lecture's neighbourhood
    - Kernel: every coefficient is 1/9
    - Neighbourhood, centred on 249:

        ```
        131  134  193
        251  249  221
        220  206  230
        ```

    - Sum: 131 + 134 + 193 + 251 + 249 + 221 + 220 + 206 + 230 = 1835
    - 1835 / 9 = 203.9, which rounds to **204**
    - The centre pixel 249 becomes 204 in the output
    :::

- Kinds of kernel:
    - **omnidirectional**: responds the same whichever direction the intensity changes in
    - **uniform**: all coefficients have the same weight (the mean filter)
    - **nonuniform**: coefficients have different weights (pyramid, cone, Gaussian)

- Normalization:
    - Kernels are usually **normalized**: each coefficient is divided by the sum of all coefficients
    - The factor is often written outside the matrix, for example 1/9 in front of a matrix of 1s
    - In code the coefficients are often already divided
    - Why: a region of constant intensity should keep the same value after filtering
    - And it avoids bias: the original and filtered images should have the same total brightness
    - Sharpening kernels whose coefficients sum to 0 are the exception (lecture 17)

- Kernel shapes from the lecture:

| Kernel | Size | Divide by | Idea |
|---|---|---|---|
| rectangular (box) | 5 x 5 of 1s | 25 | uniform smoothing |
| circular (pill-box) | 5 x 5, corners 0 | 21 | uniform, roughly round |
| pyramidal | 5 x 5, 1 2 3 2 1 pattern, centre 9 | 81 | weight falls off linearly from the centre |
| cone | 5 x 5, centre 5 | 27 | weight falls off with distance, round |

- Image borders:
    - Near the border, part of the kernel would sit outside the image, so normal convolution is impossible there
    - This is true of any neighbourhood operation
    - A kernel with half-width m (m = 1 for 3 x 3, 2 for 5 x 5, 3 for 7 x 7) can only be centred on pixels at least m from every edge
    - On an M x N image the processable region is `(M - 2m) x (N - 2m)`, starting at (m, m)

| Kernel | m | Origin | Processable region |
|---|---|---|---|
| 3 x 3 | 1 | (1, 1) | (M-2) x (N-2) |
| 5 x 5 | 2 | (2, 2) | (M-4) x (N-4) |
| 7 x 7 | 3 | (3, 3) | (M-6) x (N-6) |

- Ways to handle the border:
    - **Copy the input pixels**: where convolution is impossible, copy the input value. The output has an unprocessed frame
    - **Truncate the image**: drop those pixels. The output is smaller than and offset from the input
    - **Truncate the kernel**: use a smaller, modified kernel at edges and corners. Correct, but adds a lot of complexity
    - **Reflected indexing**: if `x + i` falls outside the image, reflect it back inside, as if the image were mirrored at its edges. The lecture calls this the most useful option
    - **Circular indexing**: pretend the image repeats forever in every direction, so falling off the right edge wraps to the left. Rarely used in image processing

- Reflected indexing with numbers:

    ::: eg Reflecting at both ends of a row
    - Row of width 5, indices 0 to 4, kernel half-width 1
    - At x = 0 the kernel wants index -1. Reflect it to index 1
    - At x = 4 it wants index 5. Reflect it to index 3
    - So the row `10 20 30 40 50` is read as `20 | 10 20 30 40 50 | 40` at the edges
    - Some libraries reflect to index 0 instead (repeating the edge pixel). Check which one your assignment asks for
    :::

- Connecting this to GPGPU (lecture 15):
    - Each output pixel depends only on input pixels, never on other output pixels
    - That is exactly the kernel rule, so one thread per output pixel works
    - Each thread finds its (x, y), loops over the k x k neighbourhood of the input, and writes one output value
    - Writing into the input image instead would break the rule, because neighbouring threads would read half-updated values
    - The border handling is a branch, so pixels near the edge can cause some divergence, but only along a thin frame
