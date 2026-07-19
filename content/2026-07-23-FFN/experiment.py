import numpy as np


def silu(z: np.ndarray) -> np.ndarray:
    return z / (1 + np.exp(-z))


# A SwiGLU feed-forward network (FFN) operates independently on each token.
# x has shape [tokens, d_model]; hidden has shape [tokens, d_ff].
x = np.array([[1.0, -0.5], [0.2, 1.0]])
w_gate = np.array([[1.0, -1.0, 0.5], [0.5, 1.0, -1.0]])
w_up = np.array([[0.8, 0.4, 1.2], [-0.3, 0.9, 0.2]])
w_down = np.array([[0.6, -0.2], [0.1, 0.7], [0.5, 0.3]])

gate = silu(x @ w_gate)
up = x @ w_up
hidden = gate * up
y = hidden @ w_down

for index, row in enumerate(x):
    standalone_y = (silu(row @ w_gate) * (row @ w_up)) @ w_down
    np.testing.assert_array_equal(y[index], standalone_y)

# Perturbing one token cannot change the FFN output for the other token.
perturbed_x0 = x.copy()
perturbed_x0[0] += np.array([0.3, -0.4])
perturbed_y0 = (silu(perturbed_x0 @ w_gate) * (perturbed_x0 @ w_up)) @ w_down
np.testing.assert_array_equal(perturbed_y0[1], y[1])

perturbed_x1 = x.copy()
perturbed_x1[1] += np.array([-0.4, 0.3])
perturbed_y1 = (silu(perturbed_x1 @ w_gate) * (perturbed_x1 @ w_up)) @ w_down
np.testing.assert_array_equal(perturbed_y1[0], y[0])

for name, value in (("x", x), ("gate", gate), ("up", up), ("hidden", hidden), ("y", y)):
    print(f"{name} = {np.array2string(value, precision=3, suppress_small=True, floatmode='fixed')}")
