import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import time

# =========================================================
# 1. MOVIMENTO REAL (estilo FPS competitivo)
# =========================================================
def true_position_continuous(t):
    """
    Retorna a posição real do jogador no tempo t.

    O movimento simula um jogador em um jogo FPS com poucas mudanças
    abruptas de direção (direita, cima, esquerda, baixo e diagonal).

    Parâmetros:
    ----------
    t : float
        Tempo atual.

    Retorno:
    -------
    numpy.ndarray
        Vetor [x, y] representando a posição do jogador.
    """

    # direita
    if t < 2:
        return np.array([4*t, 0])

    # sobe abruptamente
    elif t < 4:
        return np.array([8, 5*(t-2)])

    # esquerda
    elif t < 6:
        return np.array([8 - 4*(t-4), 10])

    # desce
    elif t < 8:
        return np.array([0, 10 - 5*(t-6)])

    # diagonal
    else:
        return np.array([3*(t-8), 3*(t-8)])


# =========================================================
# 1.b. MOVIMENTO REAL (ADAD spam estilo FPS competitivo)
# =========================================================
def true_position_discontinuous(t):
    """
    Retorna a posição real do jogador no tempo t.

    O movimento simula um jogador em um jogo FPS com muita mudanças
    abruptas de direção (simula ADAD spam em um FPS competitivo).
    Isso gera movimentos de alta frequência por conta da alternância rapida entre esquerda e direita
    
    Parâmetros:
    ----------
    t : float
        Tempo atual.

    Retorno:
    -------
    numpy.ndarray
        Vetor [x, y] representando a posição do jogador.
    """

    # ADAD spam horizontal
    if t < 3:
        # frequência do spam
        freq = 5

        # amplitude lateral
        amp = 1.0

        # onda quadrada:
        # alterna instantaneamente entre -1 e +1
        x = amp if np.sin(2 * np.pi * freq * t) > 0 else -amp
        return np.array([x, 0])

    # sobe enquanto continua ADAD
    elif t < 6:
        freq = 6
        amp = 1.2
        x = amp if np.sin(2 * np.pi * freq * t) > 0 else -amp
        y = 3 * (t - 3)
        return np.array([x, y])

    # jitter horizontal
    elif t < 8:
        freq = 12
        amp = 0.8
        x = amp if np.sin(2 * np.pi * freq * t) > 0 else -amp
        return np.array([x, 9])

    # diagonal final
    else:
        d = t - 8
        return np.array([d * 2, 9 + d * 2])

# =========================================================
# 2. INTERPOLAÇÃO LINEAR
# =========================================================
def linear_interpolation(t, snapshot_times, positions):
    """
    Realiza interpolação linear entre snapshots.

    Para um tempo t, encontra o intervalo correspondente e
    interpola linearmente entre os dois pontos vizinhos.

    Parâmetros:
    ----------
    t : float
        Tempo no qual a posição será estimada.

    times : numpy.ndarray
        Tempos dos snapshots recebidos.

    positions : numpy.ndarray
        Posições associadas aos snapshots.

    Retorno:
    -------
    numpy.ndarray
        Posição interpolada [x, y].
    """

    if t <= snapshot_times[0]:
        return positions[0]

    if t >= snapshot_times[-1]:
        return positions[-1]

    for i in range(len(snapshot_times) - 1):
        if snapshot_times[i] <= t <= snapshot_times[i + 1]:
            t0, t1 = snapshot_times[i], snapshot_times[i + 1]
            p0, p1 = positions[i], positions[i + 1]
            alpha = (t - t0) / (t1 - t0)
            return p0 + alpha * (p1 - p0)

# =========================================================
# 3. INTERPOLAÇÃO POR SPLINE CÚBICA
# =========================================================
def create_spline(snapshot_times, snapshot_positions):
    """
    Cria funções de interpolação cubic spline para os eixos X e Y.

    Esta função constrói um interpolador baseado em CubicSpline
    a partir dos snapshots recebidos da simulação de rede.

    O resultado é um par de funções (cs_x, cs_y) que podem ser
    usadas para reconstruir a posição contínua do objeto ao longo do tempo.

    Parâmetros:
    ----------
    snapshot_times : numpy.ndarray
        Array com os tempos dos snapshots recebidos.

    snapshot_positions : numpy.ndarray
        Array de posições associadas a cada snapshot, no formato [x, y].

    Retorno:
    -------
    tuple
        (cs_x, cs_y)
        - cs_x: função spline para o eixo X
        - cs_y: função spline para o eixo Y
    """

    cs_x = CubicSpline(snapshot_times, snapshot_positions[:, 0], bc_type='natural')
    cs_y = CubicSpline(snapshot_times, snapshot_positions[:, 1], bc_type='natural')
    return cs_x, cs_y

def spline_interpolation(t, snapshot_times, cs_x, cs_y):
    """
    Realiza interpolação usando cubic spline.

    Utiliza splines cúbicas naturais (C² contínuo) para gerar
    uma trajetória suave entre os pontos recebidos.

    O tempo é limitado ao intervalo dos snapshots disponíveis.

    Parâmetros:
    ----------
    t : float
        Tempo no qual a posição será estimada.

    snapshot_times : numpy.ndarray
        Array de tempos dos snapshots (usado para limitar o domínio da interpolação).

    cs_x : scipy.interpolate.CubicSpline
        Função spline cúbica para o eixo X.

    cs_y : scipy.interpolate.CubicSpline
        Função spline cúbica para o eixo Y.

    Retorno:
    -------
    numpy.ndarray
        Vetor [x, y] representando a posição interpolada no tempo t.
    """

    t = np.clip(t, snapshot_times[0], snapshot_times[-1])
    return np.array([cs_x(t), cs_y(t)])

# =========================================================
# 4. SUAVIDADE
# =========================================================
def acceleration(positions):
    """
    Calcula uma métrica de suavidade baseada na aceleração média.

    A aceleração é estimada como a segunda diferença das posições,
    e sua magnitude média é usada como indicador de suavidade.

    Parâmetros:
    ----------
    positions : numpy.ndarray
        Sequência de posições [x, y].

    Retorno:
    -------
    float
        Valor médio da magnitude da aceleração.
    """

    velocity = np.diff(positions, axis=0)
    acceleration = np.diff(velocity, axis=0)
    return np.mean(np.linalg.norm(acceleration, axis=1))

# =========================================================
# 5. OVERSHOOT
# =========================================================
def overshoot(interpolated_positions, render_times, snapshot_times, snapshot_positions, buffer_delay):
    """
    Calcula o overshoot real da interpolação.

    Overshoot ocorre quando a posição interpolada ultrapassa
    os limites definidos pelos snapshots vizinhos (bounding box local).

    Essa métrica detecta:
    - Curvas artificiais
    - Extrapolações locais
    - Comportamento irreal (importante em jogos multiplayer)

    Parâmetros:
    ----------
    interpolated_positions : numpy.ndarray
        Posições geradas pela interpolação.

    render_times : numpy.ndarray
        Tempos de renderização.

    snapshot_times : numpy.ndarray
        Tempos dos snapshots recebidos.

    snapshot_positions : numpy.ndarray
        Posições dos snapshots.

    buffer_delay : float
        Atraso (latência) aplicado na simulação de renderização.
        Representa o tempo entre o estado real do servidor e o estado
        observado pelo cliente, simulando network delay.

    Retorno:
    -------
    tuple
        (overshoot_count, overshoot_magnitude)

        overshoot_count : int
            Número de ocorrências de overshoot.

        overshoot_magnitude : float
            Soma das magnitudes de overshoot.
    """

    overshoot_count = 0
    overshoot_magnitude = 0

    for idx, t in enumerate(render_times):
        render_t = t - buffer_delay

        # ignorar fora do intervalo
        if (render_t <= snapshot_times[0] or render_t >= snapshot_times[-1]):
            continue

        # encontrar snapshots vizinhos
        for i in range(len(snapshot_times) - 1):
            if (snapshot_times[i] <= render_t <= snapshot_times[i + 1]):
                p0 = snapshot_positions[i]
                p1 = snapshot_positions[i + 1]

                interp = interpolated_positions[idx]

                # bounding box local
                min_x = min(p0[0], p1[0])
                max_x = max(p0[0], p1[0])

                min_y = min(p0[1], p1[1])
                max_y = max(p0[1], p1[1])

                overshoot = False

                dx = 0
                dy = 0

                if interp[0] < min_x:
                    overshoot = True
                    dx = min_x - interp[0]
                elif interp[0] > max_x:
                    overshoot = True
                    dx = interp[0] - max_x

                if interp[1] < min_y:
                    overshoot = True
                    dy = min_y - interp[1]
                elif interp[1] > max_y:
                    overshoot = True
                    dy = interp[1] - max_y

                if overshoot:
                    overshoot_count += 1
                    overshoot_magnitude += np.sqrt(dx**2 + dy**2)
                break
            
    return overshoot_count, overshoot_magnitude

# =========================================================
# 6. SIMULAÇÃO PRINCIPAL
# =========================================================
def main():
    # ---------------- CONFIGURAÇÃO DA REDE ----------------
    total_time = 10
    dt_render = 0.01

    snapshot_interval = 0.1
    latency = 0.1
    jitter_std = 0.03
    packet_loss_rate = 0.3
    
    render_times = np.arange(0, total_time, dt_render)

    # ---------------- SNAPSHOTS COM JITTER ----------------
    snapshot_times = []
    t = 0

    while t < total_time:
        jitter = np.random.normal(0, jitter_std)
        interval = max(0.03, snapshot_interval + jitter)
        t += interval
        snapshot_times.append(t)

    snapshot_times = np.array(snapshot_times)

    # ---------------- PACKET LOSS ----------------
    mask = np.random.rand(len(snapshot_times)) > packet_loss_rate
    snapshot_times = snapshot_times[mask]

    # ---------------- POSIÇÕES DOS SNAPSHOTS ----------------
    lista = []

    for t in snapshot_times:
        lista.append(true_position_continuous(t))

    snapshot_positions = np.array(lista)

    # ---------------- SPLINE ----------------
    cs_x, cs_y = create_spline(snapshot_times, snapshot_positions)

    # ---------------- SIMULAÇÃO CLIENTE ----------------
    buffer_delay = latency

    linear_results = []
    spline_results = []
    true_results = []

    linear_time = 0
    spline_time = 0

    for t in render_times:
        render_t = t - buffer_delay
        true_pos = true_position_continuous(max(render_t, 0))

        # Linear
        start = time.time()
        lin_pos = linear_interpolation(render_t, snapshot_times, snapshot_positions)
        linear_time += time.time() - start

        # Spline
        start = time.time()
        spl_pos = spline_interpolation(render_t, snapshot_times, cs_x, cs_y)
        spline_time += time.time() - start

        # Resultados
        linear_results.append(lin_pos)
        spline_results.append(spl_pos)
        true_results.append(true_pos)


    linear_results = np.array(linear_results)
    spline_results = np.array(spline_results)
    true_results = np.array(true_results)

    # ---------------- MÉTRICAS ----------------
    # Erro
    linear_error = np.linalg.norm(linear_results - true_results, axis=1)
    spline_error = np.linalg.norm(spline_results - true_results, axis=1)

    # Suavidade (aceleração média)
    linear_rms = np.sqrt(np.mean(linear_error**2))
    spline_rms = np.sqrt(np.mean(spline_error**2))

    # Overshoot
    linear_smoothness = acceleration(linear_results)
    spline_smoothness = acceleration(spline_results)

    linear_overshoot_count, linear_overshoot_mag = overshoot(linear_results, render_times, snapshot_times, snapshot_positions, buffer_delay)
    spline_overshoot_count, spline_overshoot_mag = overshoot(spline_results, render_times, snapshot_times, snapshot_positions, buffer_delay)

    # ---------------- RESULTADOS ----------------
    print("\n=== RESULTADOS ===\n")

    print(f"Erro RMS Linear:  {linear_rms:.4f}")
    print(f"Erro RMS Spline: {spline_rms:.4f}")

    print()

    print(f"Tempo Linear:  {linear_time:.6f}s")
    print(f"Tempo Spline: {spline_time:.6f}s")

    print()

    print(f"Suavidade Linear:  {linear_smoothness:.6f}")
    print(f"Suavidade Spline: {spline_smoothness:.6f}")

    print()

    print("=== OVERSHOOT ===")

    print(f"Linear -> Ocorrências: {linear_overshoot_count}")
    print(f"Linear -> Magnitude:   {linear_overshoot_mag:.6f}")

    print()

    print(f"Spline -> Ocorrências: {spline_overshoot_count}")
    print(f"Spline -> Magnitude:   {spline_overshoot_mag:.6f}")

    # ---------------- GRÁFICOS ----------------
    # Trajetória completa
    plt.figure(figsize=(8, 6))

    # trajetória real
    plt.plot(
        true_results[:, 0],
        true_results[:, 1],
        label='Real',
        linewidth=3,
        color='skyblue'
    )

    # linear
    plt.plot(
        linear_results[:, 0],
        linear_results[:, 1],
        '--',
        label='Linear',
        color='red'
    )

    # spline
    plt.plot(
        spline_results[:, 0],
        spline_results[:, 1],
        ':',
        label='Spline',
        color='blue'
    )

    plt.scatter(
        snapshot_positions[:, 0],
        snapshot_positions[:, 1],
        s=20,
        label='Snapshots',
        color='black'
    )

    plt.title('Trajetória do Jogador')

    plt.xlabel('X')
    plt.ylabel('Y')

    plt.legend()

    plt.grid(True)

    # Erro ao longo do tempo
    plt.figure(figsize=(8, 4))

    # linear
    plt.plot(
        render_times,
        linear_error,
        label='Erro Linear',
        color='red'
    )

    # spline
    plt.plot(
        render_times,
        spline_error,
        label='Erro Spline',
        color='blue'
    )

    plt.title('Erro ao Longo do Tempo')

    plt.xlabel('Tempo')
    plt.ylabel('Erro')

    plt.legend()

    plt.grid(True)

    plt.show()

if __name__ == "__main__":
    main()