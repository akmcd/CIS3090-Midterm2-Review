import numpy as np
import warp as wp

device = "cpu"

@wp.kernel
def addArrays(x: wp.array(dtype=float),
              y: wp.array(dtype=float),
              z: wp.array(dtype=float)):
    # thread index
    tid = wp.tid()
    # compute the sum
    z[tid] = x[tid] + y[tid]

hostX = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], dtype=np.float32)
hostY = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13], dtype=np.float32)

x = wp.array(hostX, dtype=float, device=device)
y = wp.array(hostY, dtype=float, device=device)

numElements = len(hostX)
z = wp.zeros(numElements, dtype=float, device=device)

wp.launch(kernel=addArrays,
          dim=len(z),
          inputs=[x, y],
          outputs=[z],
          device=device)

print(z.numpy())
