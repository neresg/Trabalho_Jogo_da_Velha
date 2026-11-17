"""
jogo.py
=======
Software jogador de Jogo da Velha (interface de terminal).

Modos:
  1) Humano x Computador
  2) Computador x Computador

Em ambos o usuário informa QUEM COMEÇA. Quem começa joga com "X".
O computador decide com Minimax ou com Poda Alfa-Beta (à escolha) e, a cada
jogada, o programa mostra os passos (nós visitados) e o tempo gasto.

Como executar:   python jogo.py
"""

import sys

from algoritmos import (
    ALFABETA, MINIMAX, NOMES, VAZIO,
    casas_livres, escolher_jogada, novo_tabuleiro, oponente,
    valor_terminal, vencedor,
)

# Evita erro de acentuação em alguns terminais do Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# --------------------------------------------------------------------------
# Entrada e saída
# --------------------------------------------------------------------------
def br(valor, casas=0):
    """Formata número no padrão brasileiro: 1.234,56"""
    t = f"{valor:,.{casas}f}"
    return t.replace(",", "#").replace(".", ",").replace("#", ".")


def sinal(v):
    """+1, 0 ou -1 (sem '+0')."""
    return f"{v:+d}" if v else "0"


def imprimir_tabuleiro(tab):
    """Desenha o tabuleiro; casas vazias mostram o número da posição (1-9)."""
    def c(i):
        return tab[i] if tab[i] != VAZIO else str(i + 1)

    print()
    for linha in range(3):
        a, b, d = c(3 * linha), c(3 * linha + 1), c(3 * linha + 2)
        print(f"   {a} | {b} | {d}")
        if linha < 2:
            print("  ---+---+---")
    print()


def perguntar(texto, validas):
    """Lê uma opção do teclado até ser uma das opções válidas."""
    while True:
        try:
            resp = input(texto).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            sys.exit(0)
        if resp in validas:
            return resp
        print(f"  Opção inválida. Escolha entre: {', '.join(validas)}")


def escolher_algoritmo(rotulo):
    print(f"\nAlgoritmo para {rotulo}:")
    print("  1) Minimax")
    print("  2) Poda Alfa-Beta")
    return MINIMAX if perguntar("Opção: ", ("1", "2")) == "1" else ALFABETA


def jogada_humana(tab, simbolo):
    """Pede a casa (1-9) ao humano e valida."""
    livres = [i + 1 for i in casas_livres(tab)]
    while True:
        r = perguntar(f"Sua jogada ({simbolo}) - casa {livres}: ",
                      tuple(str(n) for n in range(1, 10)))
        if int(r) in livres:
            return int(r) - 1
        print("  Essa casa já está ocupada.")


# --------------------------------------------------------------------------
# Resumo estatístico
# --------------------------------------------------------------------------
def imprimir_resumo(historico):
    """Tabela com os passos e o tempo de cada jogada do computador."""
    if not historico:
        return
    print("\n" + "=" * 66)
    print("  ESTATÍSTICAS DAS JOGADAS DO COMPUTADOR")
    print("=" * 66)
    print(f"  {'Nº':>3} {'Algoritmo':<15} {'Casa':>5} {'Valor':>6} "
          f"{'Nós visitados':>14} {'Tempo (ms)':>11}")
    print("  " + "-" * 62)
    total_nos, total_tempo = {}, {}
    for n, (alg, d) in enumerate(historico, 1):
        print(f"  {n:>3} {NOMES[alg]:<15} {d.jogada + 1:>5} {sinal(d.valor):>6} "
              f"{br(d.nos):>14} {br(d.tempo * 1000, 3):>11}")
        total_nos[alg] = total_nos.get(alg, 0) + d.nos
        total_tempo[alg] = total_tempo.get(alg, 0.0) + d.tempo
    print("  " + "-" * 62)
    for alg in total_nos:
        print(f"  TOTAL {NOMES[alg]:<15} nós: {br(total_nos[alg]):>10}   "
              f"tempo: {br(total_tempo[alg] * 1000, 3)} ms")
    print("=" * 66)


def anunciar_resultado(tab, nomes):
    """nomes: dict símbolo -> descrição do jogador."""
    v = vencedor(tab)
    if v:
        print(f">>> {nomes[v]} venceu a partida!")
    else:
        print(">>> Empate (deu velha)!")


# --------------------------------------------------------------------------
# Modo 1: Humano x Computador
# --------------------------------------------------------------------------
def modo_humano_x_computador():
    algoritmo = escolher_algoritmo("o COMPUTADOR")
    print("\nQuem começa a partida? (quem começa joga com X)")
    print("  1) Humano")
    print("  2) Computador")
    humano_comeca = perguntar("Opção: ", ("1", "2")) == "1"

    humano = "X" if humano_comeca else "O"
    ia = oponente(humano)
    nomes = {humano: f"Você ({humano})", ia: f"Computador ({ia})"}

    tab, vez, historico = novo_tabuleiro(), "X", []
    print(f"\nVocê joga com {humano}; o computador joga com {ia} "
          f"usando {NOMES[algoritmo]}.")
    imprimir_tabuleiro(tab)

    while valor_terminal(tab, ia) is None:
        if vez == humano:
            tab[jogada_humana(tab, humano)] = humano
        else:
            d = escolher_jogada(tab, ia, algoritmo)
            tab[d.jogada] = ia
            historico.append((algoritmo, d))
            print(f"Computador ({ia}) jogou na casa {d.jogada + 1}  "
                  f"[{br(d.nos)} nós visitados, {br(d.tempo * 1000, 3)} ms]")
        imprimir_tabuleiro(tab)
        vez = oponente(vez)

    anunciar_resultado(tab, nomes)
    imprimir_resumo(historico)


# --------------------------------------------------------------------------
# Modo 2: Computador x Computador
# --------------------------------------------------------------------------
def modo_computador_x_computador():
    alg1 = escolher_algoritmo("o COMPUTADOR 1")
    alg2 = escolher_algoritmo("o COMPUTADOR 2")
    print("\nQuem começa a partida? (quem começa joga com X)")
    print("  1) Computador 1")
    print("  2) Computador 2")
    c1_comeca = perguntar("Opção: ", ("1", "2")) == "1"

    simb = {1: "X" if c1_comeca else "O"}
    simb[2] = oponente(simb[1])
    algs = {simb[1]: alg1, simb[2]: alg2}
    nomes = {simb[1]: f"Computador 1 ({simb[1]}, {NOMES[alg1]})",
             simb[2]: f"Computador 2 ({simb[2]}, {NOMES[alg2]})"}

    tab, vez, historico = novo_tabuleiro(), "X", []
    print(f"\n{nomes['X']}  contra  {nomes['O']}")
    imprimir_tabuleiro(tab)

    while valor_terminal(tab, "X") is None:
        d = escolher_jogada(tab, vez, algs[vez])
        tab[d.jogada] = vez
        historico.append((algs[vez], d))
        print(f"{nomes[vez]} jogou na casa {d.jogada + 1}  "
              f"[{br(d.nos)} nós, {br(d.tempo * 1000, 3)} ms]")
        imprimir_tabuleiro(tab)
        vez = oponente(vez)

    anunciar_resultado(tab, nomes)
    imprimir_resumo(historico)


# --------------------------------------------------------------------------
# Menu principal
# --------------------------------------------------------------------------
def main():
    print("=" * 66)
    print("   JOGO DA VELHA  -  Minimax e Poda Alfa-Beta")
    print("   Inteligência Artificial - IFPI Campus Picos")
    print("=" * 66)
    while True:
        print("\nMenu principal")
        print("  1) Humano x Computador")
        print("  2) Computador x Computador")
        print("  0) Sair")
        op = perguntar("Opção: ", ("0", "1", "2"))
        if op == "0":
            print("Até logo!")
            return
        if op == "1":
            modo_humano_x_computador()
        else:
            modo_computador_x_computador()


if __name__ == "__main__":
    main()
