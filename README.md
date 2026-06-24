
# 🎮 FPS Network Interpolation Simulator
Uma ferramenta de simulação matemática voltada para arquitetura de redes de jogos multiplayer. O projeto analisa, calcula e compara o comportamento de algoritmos de **Interpolação Linear** e **Spline Cúbica (Cubic Spline)** em cenários reais de rede com *latência, jitter* e *perda de pacotes (packet loss)*, utilizando o perfil de movimentação de jogos de FPS competitivos.

---

## 📌 Sumário
- [Recursos do Projeto](#-recursos-do-projeto)
- [Como Funciona](#-como-funciona)
- [Métricas Analisadas](#-métricas-analisadas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Execução](#-instalação-e-execução)

---

## 🚀 Recursos do Projeto

*   **Simulador de Movimento Competitivo:** Inclui geradores de caminhos contínuos (curvas e diagonais) e movimentos de alta frequência, mimetizando o famoso *"ADAD spam"* (estilo jitter/strafe lateral).
*   **Emulação de Redes Instáveis:** Aplica variáveis reais presentes em servidores multiplayer:
    *   **Latência (Ping):** Buffer delay configurável no cliente.
    *   **Jitter:** Variação estocástica gaussiana no intervalo de recebimento dos pacotes.
    *   **Packet Loss:** Descarte probabilístico de pacotes em trânsito.
*   **Modelos de Interpolação:** Implementação comparativa passo a passo entre aproximação linear padrão e funções Spline Cúbicas Naturais ($C^2$ Contínuo) através da biblioteca Scipy.
*   **Visualização Gráfica:** Renderização automatizada das trajetórias reconstruídas com os frames originais (snapshots) capturados do servidor e plotagem do erro dinâmico ao longo do tempo.

---

## 🛠️ Como Funciona

Em jogos multiplayer com arquitetura autoritativa (Cliente-Servidor), o servidor envia posições do jogador de tempos em tempos (*snapshots*). Para evitar que os oponentes se movam de forma "travada" na tela do cliente, aplicamos a **interpolação** utilizando um histórico armazenado em buffer (`buffer_delay`).

1. **O Servidor** calcula a posição real do jogador.
2. **A Rede** introduz atrasos irregulares (Jitter) e perde pacotes aleatoriamente.
3. **O Cliente** recebe estes snapshots incompletos e reconstrói o movimento de duas formas:
   * **Linear:** Liga os pontos por retas. É rápido, mas cria quinas bruscas.
   * **Spline Cúbica:** Cria curvas matemáticas suaves. No entanto, em mudanças bruscas de direção, pode gerar o efeito de **Overshoot** (quando o personagem "passa do ponto" esperado).

---

## 📊 Métricas Analisadas

O script avalia o desempenho dos algoritmos com base em 4 critérios fundamentais para o netcode de um jogo:

| Métrica | O que mede | Impacto no Jogo |
| :--- | :--- | :--- |
| **Erro RMS (Root Mean Square)** | A precisão geométrica média em relação à posição real do servidor. | **Hitbox Desalinhada:** Quanto maior o erro, mais o cliente vê o inimigo fora do lugar real. |
| **Tempo de Execução** | O custo computacional de processamento do algoritmo por frame. | **Desempenho:** Algoritmos muito lentos prejudicam a taxa de quadros (FPS) do cliente. |
| **Suavidade (Smoothness)** | A magnitude média da aceleração ao longo da curva gerada. | **Visual/Fluidez:** Números menores indicam uma transição mais fluida e agradável aos olhos. |
| **Overshoot (Ocorrências/Mag.)** | Quantas vezes e o quanto a interpolação ultrapassou a "bounding box" dos pacotes vizinhos. | **Previsibilidade:** Um overshoot alto faz o modelo "inventar" caminhos que o jogador nunca fez. |

---

## 📦 Pré-requisitos

O projeto exige **Python 3.10 ou superior**. As dependências necessárias para a reprodução matemática e plotagem gráfica são:

*   `numpy` (Processamento matricial e vetorial das coordenadas)
*   `scipy` (Módulos matemáticos avançados para geração da Spline Cúbica)
*   `matplotlib` (Geração dos gráficos de análise)

---

## 🔧 Instalação e Execução

1. **Clone o repositório:**
```bash
   git clone https://github.com/VitorBarateli/Calculo-Numerico-Interpolacao.git
   cd nome-do-repositorio
```
2. **Crie e ative um ambiente virtual (Recomendado):**
```bash
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
```
3. **Instale as dependências:**
```bash
   pip install -r requirements.txt
```
4. **Execute a simulação:**
```bash
   python main.py
```
