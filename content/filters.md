title: Sharpening, blurring and denoising

- What lecture 17 is about:
    - The fundamental filters: sharpening (high-pass, unsharp masking) and smoothing (mean, Gaussian, median)
    - All but the median are convolutions with the kernels from lecture 16

- Why images need fixing:
    - **blur**: details are smoothed out. Causes: out-of-focus optics, lens aberrations, atmospheric turbulence, camera motion during long exposures
    - **noise**: artifacts added when the image is captured
    - Noise comes from variation in photon counts and from the sensor itself (**read noise**)
    - Sensor noise gets worse as temperature rises, and as sensitivity is raised in low light

- Low-pass and high-pass:
    - "Low" and "high" refer to spatial frequency: how quickly intensity changes across the image
    - **low-pass filter (LPF)**: lets slow changes through and removes quick ones. Smooths, removes noise. Also called a "high-cut" filter
    - **high-pass filter (HPF)**: the image minus its low-pass version. Keeps sudden changes like edges, suppresses gradual ones
    - **high-boost filter**: part of the high-pass result added back to the image
    - Quick, closely spaced changes can be unwanted (noise) or wanted (fine detail). A filter cannot tell them apart

- Simple sharpening:
    - A high-pass kernel mixes positive and negative values
    - Omnidirectional version: positive at the centre, negative around it, coefficients summing to **0**

        ```
        -1  -1  -1
        -1   8  -1
        -1  -1  -1
        ```

- Why the sum is 0:
    - Over a flat region every pixel is equal, so 8v - 8v = 0
    - Over a slow change the result is small
    - Over a sharp change the result is large
    - Example: three columns of 10, 10, 50 give -120. Columns 10, 50, 50 give +120. Flat 50 everywhere gives 0
    - So the output is an edge map. It is not normalized like a smoothing kernel, because its sum is 0

- Caveats of sharpening:
    - Noise is high-frequency, so sharpening makes noise more visible
    - In practice, remove noise first, then sharpen

- Unsharp masking:
    - Introduced by Schreiber in 1970 to improve newspaper wirephotos, based on a darkroom technique of sandwiching a blurred positive with the negative
    - Idea: subtract a blurred copy from the image, which removes the low frequencies and leaves the edges
    - Unlike the single-kernel filters, it is a multi-step method
    - Step 1, edge image: `g(x, y) = f(x, y) - S(f(x, y))`, where `S(f)` is a blurred version of `f`
    - Step 2, add it back: `f_UM(x, y) = f(x, y) + k * g(x, y)`
    - `k` is a scaling constant. Reasonable values are 0.2 to 0.7, larger means sharper
    - With k > 1 it is called a **high-boost** filter

- Unsharp masking with numbers (a 1D edge):
    - Input row: `10 10 10 10 50 50 50 50`
    - Blur with a 3-wide mean (edges repeated): `10 10 10 23.3 36.7 50 50 50`
    - Edge image g = input - blur: `0 0 0 -13.3 13.3 0 0 0`
    - Result with k = 0.5: `10 10 10 3.3 56.7 50 50 50`
    - The dark side of the edge dips below 10 and the bright side rises above 50: that is **overshoot**

- Limits of unsharp masking:
    - **noise sensitivity**: it emphasizes high frequencies, and noise is high frequency
    - **overshoot**: wide, abrupt brightness changes get an exaggerated rim
    - It makes an edge steeper by making it taller. Many sharpening methods share this trait
    - In the lecture's example, the square elements look brighter than in the original

- Denoising in general:
    - Noise filters are smoothing (low-pass) filters
    - Two families: **mean-based** (mean, Gaussian) and **order-statistic** (median and other rank filters)

- Mean filter (box filter):
    - Replace each pixel with the average of its neighbourhood. Also called sliding mean or box filter
    - 3 x 3: sum the 9 values and divide by 9. 5 x 5: sum 25 and divide by 25
    - It reduces noise because noise is sharp transitions, but edges are sharp transitions too, so edges blur
    - It is the opposite of sharpening
    - Larger kernels, or applying a small kernel repeatedly, smooth more
    - Effective against Gaussian noise

- Gaussian filter:
    - A smoothing filter with a nonuniform kernel built from a 2D Gaussian function
    - `w(i, j) = e^(-(i^2 + j^2) / (2 sigma^2))` for i, j from -[3 sigma] to [3 sigma]
    - [3 sigma] means the integer part of 3 sigma. Beyond 3 sigma the weights are negligible
    - Coefficients shrink with distance from the centre, so central pixels count more than the edges of the neighbourhood
    - Larger sigma: a wider spread, more blur, and a bigger kernel
    - **isotropic** (rotationally symmetric): no direction is smoothed more than another
    - With sigma^2 = 1 the kernel is 7 x 7. Normalized and multiplied by 1000 its centre row is `2 22 97 159 97 22 2`, and its centre is 159
    - Other common values: sigma^2 = 2/3 and sigma^2 = 2
    - Compared with a mean filter of similar size, edges blur less, because far-away pixels count less

- Rank (order-statistic) filters:
    - Non-linear filters: list the neighbourhood's values, sort them, and pick the value at a chosen position
    - Positions include the median, lower quartile and upper quartile
    - Because sorting is not a weighted sum, a rank filter is **not** a convolution and has no kernel matrix

- Median filter:
    - Replace the pixel with the middle value of its sorted neighbourhood
    - Lecture example (5 x 5): the sorted 25 values are `9 11 21 23 23 23 27 34 45 46 87 90 98 100 103 104 104 104 105 105 106 108 109 110 112`
    - The 13th value is the median: **98**
    - Used to remove **impulse noise** (salt and pepper: isolated very bright or very dark pixels)
    - It works when the noisy pixels are less than half the neighbourhood, because the median then comes from the clean majority
    - Example: a 3 x 3 of eight 10s and one 255. The mean is 37.2 (the spike smears out), the median is 10 (the spike is gone)

- Median filter strengths and weaknesses:
    - It does not compress the brightness range inside the neighbourhood, so sharp and straight edges survive
    - It is non-specific: any structure smaller than half the neighbourhood is removed, real or noise
    - So thin lines and small objects disappear too
    - Repeated application causes **posterization**: flat patches of colour with hard boundaries

- Choosing a filter:

| Problem | Filter | Why |
|---|---|---|
| Gaussian noise | mean or Gaussian | averaging cancels random variation |
| Impulse (salt and pepper) noise | median | the outlier never becomes the middle value |
| Keep edges while denoising | median | no averaging across the edge |
| Blurry image | unsharp masking | adds the edge image back |
| Noisy and blurry | denoise first, then sharpen | sharpening amplifies noise |
