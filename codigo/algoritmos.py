"""
algoritmos.py
=============
Regras do Jogo da Velha e os dois algoritmos de busca adversarial pedidos
no trabalho: Minimax e Poda Alfa-Beta.

Convenções
----------
* O tabuleiro é uma lista de 9 posições (índices 0 a 8, lidos da esquerda
  para a direita, de cima para baixo). Cada posição guarda "X", "O" ou " ".
* "ia" é o símbolo do computador (o jogador MAX). O adversário é o MIN.
* Avaliação dos nós terminais (do ponto de vista do computador):
      +1  vitória do computador
      -1  derrota do computador
       0  empate
* "Passos" = número de nós da árvore de busca visitados (cada chamada da
  função recursiva conta 1 nó, inclusive o nó raiz e os nós terminais).
"""

import math
import time
from dataclasses import dataclass

VAZIO = " "
MINIMAX = "minimax"
ALFABETA = "alfabeta"
NOMES = {MINIMAX: "Minimax", ALFABETA: "Poda Alfa-Beta"}

# As 8 linhas possíveis de vitória (3 linhas, 3 colunas, 2 diagonais).
LINHAS_VITORIA = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


# --------------------------------------------------------------------------
# Regras do jogo
# --------------------------------------------------------------------------
def novo_tabuleiro():
    """Retorna um tabuleiro vazio (estado inicial)."""
    return [VAZIO] * 9


def vencedor(tab):
    """Retorna 'X' ou 'O' se alguém completou uma linha; senão None."""
    for a, b, c in LINHAS_VITORIA:
        if tab[a] != VAZIO and tab[a] == tab[b] == tab[c]:
            return tab[a]
    return None


def casas_livres(tab):
    """Lista de índices das casas ainda vazias (ações possíveis)."""
    return [i for i, v in enumerate(tab) if v == VAZIO]


def oponente(simbolo):
    """Retorna o símbolo do adversário."""
    return "O" if simbolo == "X" else "X"


def valor_terminal(tab, ia):
    """
    Função de utilidade. Retorna +1 / -1 / 0 se o estado é terminal
    (do ponto de vista do computador 'ia') ou None se o jogo continua.
    """
    v = vencedor(tab)
    if v is not None:
        return 1 if v == ia else -1
    if VAZIO not in tab:
        return 0
    return None


# --------------------------------------------------------------------------
# Contador de passos
# --------------------------------------------------------------------------
class Contador:
    """Conta quantos nós da árvore de busca foram visitados."""
    __slots__ = ("nos",)

    def __init__(self):
        self.nos = 0


# --------------------------------------------------------------------------
# Algoritmo 1: Minimax
# --------------------------------------------------------------------------
def minimax(tab, vez, ia, contador):
    """
    Minimax puro: explora TODA a árvore de jogo a partir do estado atual.
    'vez' é o jogador que joga neste nó. Retorna o valor minimax do nó.
    """
    contador.nos += 1
    util = valor_terminal(tab, ia)
    if util is not None:
        return util

    if vez == ia:                       # nó MAX
        melhor = -math.inf
        for i in casas_livres(tab):
            tab[i] = vez
            melhor = max(melhor, minimax(tab, oponente(vez), ia, contador))
            tab[i] = VAZIO
        return melhor

    melhor = math.inf                   # nó MIN
    for i in casas_livres(tab):
        tab[i] = vez
        melhor = min(melhor, minimax(tab, oponente(vez), ia, contador))
        tab[i] = VAZIO
    return melhor


# --------------------------------------------------------------------------
# Algoritmo 2: Minimax com Poda Alfa-Beta
# --------------------------------------------------------------------------
def alfa_beta(tab, vez, ia, alfa, beta, contador):
    """
    Minimax com poda alfa-beta.
      alfa = melhor valor já garantido para MAX no caminho até aqui
      beta = melhor valor já garantido para MIN no caminho até aqui
    Quando alfa >= beta, os demais filhos do nó não podem alterar a decisão
    e são descartados (poda).
    """
    contador.nos += 1
    util = valor_terminal(tab, ia)
    if util is not None:
        return util

    if vez == ia:                       # nó MAX
        melhor = -math.inf
        for i in casas_livres(tab):
            tab[i] = vez
            melhor = max(melhor, alfa_beta(tab, oponente(vez), ia, alfa, beta, contador))
            tab[i] = VAZIO
            alfa = max(alfa, melhor)
            if alfa >= beta:            # poda beta
                break
        return melhor

    melhor = math.inf                   # nó MIN
    for i in casas_livres(tab):
        tab[i] = vez
        melhor = min(melhor, alfa_beta(tab, oponente(vez), ia, alfa, beta, contador))
        tab[i] = VAZIO
        beta = min(beta, melhor)
        if alfa >= beta:                # poda alfa
            break
    return melhor


# --------------------------------------------------------------------------
# Decisão do computador (nó raiz)
# --------------------------------------------------------------------------
@dataclass
class Decisao:
    """Resultado de uma decisão do computador."""
    jogada: int      # índice (0-8) da casa escolhida
    valor: int       # valor minimax da jogada (+1, 0 ou -1)
    nos: int         # passos: nós visitados na busca
    tempo: float     # segundos gastos para decidir


def escolher_jogada(tab, ia, algoritmo):
    """
    Escolhe a melhor jogada para 'ia' usando o algoritmo informado
    (MINIMAX ou ALFABETA). Em caso de empate entre jogadas, fica com a
    primeira encontrada (ordem das casas 0..8), o que torna os dois
    algoritmos determinísticos e comparáveis: ambos escolhem a MESMA jogada.
    """
    if valor_terminal(tab, ia) is not None:
        raise ValueError("O jogo já terminou; não há jogada a escolher.")

    contador = Contador()
    contador.nos = 1                    # conta o nó raiz
    melhor_jogada, melhor_valor = None, -math.inf
    alfa = -math.inf

    inicio = time.perf_counter()
    for i in casas_livres(tab):
        tab[i] = ia
        if algoritmo == MINIMAX:
            v = minimax(tab, oponente(ia), ia, contador)
        elif algoritmo == ALFABETA:
            v = alfa_beta(tab, oponente(ia), ia, alfa, math.inf, contador)
        else:
            raise ValueError(f"Algoritmo desconhecido: {algoritmo}")
        tab[i] = VAZIO

        if v > melhor_valor:            # '>' estrito: mantém a 1ª melhor
            melhor_valor, melhor_jogada = v, i
        alfa = max(alfa, melhor_valor)  # (só tem efeito na poda alfa-beta)
    tempo = time.perf_counter() - inicio

    return Decisao(melhor_jogada, int(melhor_valor), contador.nos, tempo)
