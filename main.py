import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import time

# =========================
# 1. Movimento real (ground truth)
# =========================
def true_position(t):
    x = 10 * np.sin(t)
    y = 5 * np.cos(t)
    return np.array([x, y])


# =========================
# 2. Simulação de snapshots (rede)
# =========================
total_time = 10
dt_render = 0.01
snapshot_interval = 0.2  # baixa taxa (5 Hz)
latency = 0.1  # 100 ms

render_times = np.arange(0, total_time, dt_render)
snapshot_times = np.arange(0, total_time, snapshot_interval)

# posições recebidas da rede
snapshot_positions = np.array([true_position(t) for t in snapshot_times])


# =========================
# 3. Interpolação Linear
# =========================
def linear_interpolation(t, times, positions):
    if t <= times[0]:
        return positions[0]
    if t >= times[-1]:
        return positions[-1]

    for i in range(len(times) - 1):
        if times[i] <= t <= times[i + 1]:
            t0, t1 = times[i], times[i + 1]
            p0, p1 = positions[i], positions[i + 1]
            alpha = (t - t0) / (t1 - t0)
            return p0 + alpha * (p1 - p0)


# =========================
# 4. Interpolação Cubic Spline
# =========================
cs_x = CubicSpline(snapshot_times, snapshot_positions[:, 0])
cs_y = CubicSpline(snapshot_times, snapshot_positions[:, 1])


def spline_interpolation(t):
    return np.array([cs_x(t), cs_y(t)])


# =========================
# 5. Simulação com buffer (estilo jogo)
# =========================
buffer_delay = latency  # tempo "no passado"

linear_results = []
spline_results = []
true_results = []

linear_time = 0
spline_time = 0

for t in render_times:
    render_t = t - buffer_delay

    true_pos = true_position(render_t)

    # Linear
    start = time.time()
    lin_pos = linear_interpolation(render_t, snapshot_times, snapshot_positions)
    linear_time += time.time() - start

    # Spline
    start = time.time()
    spl_pos = spline_interpolation(render_t)
    spline_time += time.time() - start

    linear_results.append(lin_pos)
    spline_results.append(spl_pos)
    true_results.append(true_pos)

linear_results = np.array(linear_results)
spline_results = np.array(spline_results)
true_results = np.array(true_results)


# =========================
# 6. Métricas
# =========================

# Erro RMS
linear_error = np.linalg.norm(linear_results - true_results, axis=1)
spline_error = np.linalg.norm(spline_results - true_results, axis=1)

linear_rms = np.sqrt(np.mean(linear_error**2))
spline_rms = np.sqrt(np.mean(spline_error**2))

# Suavidade (aceleração)
def compute_acceleration(positions):
    velocity = np.diff(positions, axis=0)
    acceleration = np.diff(velocity, axis=0)
    return np.mean(np.linalg.norm(acceleration, axis=1))

linear_smoothness = compute_acceleration(linear_results)
spline_smoothness = compute_acceleration(spline_results)


# =========================
# 7. Resultados
# =========================
print("=== RESULTADOS ===")
print(f"Erro RMS Linear: {linear_rms:.4f}")
print(f"Erro RMS Spline: {spline_rms:.4f}")
print()
print(f"Tempo Linear: {linear_time:.6f}s")
print(f"Tempo Spline: {spline_time:.6f}s")
print()
print(f"Suavidade Linear (acc média): {linear_smoothness:.4f}")
print(f"Suavidade Spline (acc média): {spline_smoothness:.4f}")


# =========================
# 8. Gráficos
# =========================

# Trajetória
plt.figure()
plt.plot(true_results[:, 0], true_results[:, 1], label="Real")
plt.plot(linear_results[:, 0], linear_results[:, 1], '--', label="Linear")
plt.plot(spline_results[:, 0], spline_results[:, 1], ':', label="Spline")
plt.legend()
plt.title("Trajetória")
plt.xlabel("X")
plt.ylabel("Y")

# Erro ao longo do tempo
plt.figure()
plt.plot(render_times, linear_error, label="Erro Linear")
plt.plot(render_times, spline_error, label="Erro Spline")
plt.legend()
plt.title("Erro ao longo do tempo")
plt.xlabel("Tempo")
plt.ylabel("Erro")

plt.show()