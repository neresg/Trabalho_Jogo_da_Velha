"""
testes.py
=========
Testes automáticos que verificam a correção dos algoritmos.

Como executar:   python testes.py
"""

from algoritmos import (
    ALFABETA, MINIMAX, VAZIO,
    casas_livres, escolher_jogada, novo_tabuleiro, oponente,
    valor_terminal, vencedor,
)


def teste_vencedor_e_utilidade():
    t = list("XXXOO    ")
    assert vencedor(t) == "X"
    assert valor_terminal(t, "X") == 1
    assert valor_terminal(t, "O") == -1
    empate = list("XOXXOOOXX")
    assert vencedor(empate) is None and valor_terminal(empate, "X") == 0
    assert valor_terminal(novo_tabuleiro(), "X") is None
    print("OK  regras e função de utilidade (+1 / -1 / 0)")


def teste_arvore_completa():
    d = escolher_jogada(novo_tabuleiro(), "X", MINIMAX)
    assert d.nos == 549946, d.nos
    assert d.valor == 0                      # jogo perfeito termina empatado
    print(f"OK  Minimax no tabuleiro vazio visita {d.nos} nós (árvore completa)")


def teste_bloqueia_e_vence():
    # O computador (X) tem 2 em linha: deve fechar a vitória na casa 2.
    t = list("XX OO    ")
    for alg in (MINIMAX, ALFABETA):
        assert escolher_jogada(t[:], "X", alg).jogada == 2
    # O humano (X) ameaça vencer: o computador (O) precisa bloquear na casa 2.
    t = list("XX  O    ")
    for alg in (MINIMAX, ALFABETA):
        assert escolher_jogada(t[:], "O", alg).jogada == 2
    print("OK  vence quando pode e bloqueia quando precisa")


def percorrer(tab, vez, comp, estat):
    """Testa TODAS as partidas possíveis contra o computador."""
    u = valor_terminal(tab, comp)
    if u is not None:
        estat["partidas"] += 1
        estat["derrotas"] += (u == -1)
        return
    if vez == comp:
        d_mm = escolher_jogada(tab, comp, MINIMAX)
        d_ab = escolher_jogada(tab, comp, ALFABETA)
        assert d_mm.jogada == d_ab.jogada and d_mm.valor == d_ab.valor
        assert d_ab.nos <= d_mm.nos
        estat["decisoes"] += 1
        tab[d_mm.jogada] = comp
        percorrer(tab, oponente(vez), comp, estat)
        tab[d_mm.jogada] = VAZIO
    else:
        for i in casas_livres(tab):
            tab[i] = vez
            percorrer(tab, oponente(vez), comp, estat)
            tab[i] = VAZIO


def teste_nunca_perde_e_algoritmos_concordam():
    for comp, rotulo in (("X", "computador começa"), ("O", "humano começa")):
        est = {"partidas": 0, "derrotas": 0, "decisoes": 0}
        percorrer(novo_tabuleiro(), "X", comp, est)
        assert est["derrotas"] == 0
        print(f"OK  {rotulo}: {est['partidas']} partidas possíveis, "
              f"computador nunca perdeu; Minimax e Alfa-Beta escolheram a "
              f"mesma jogada nas {est['decisoes']} decisões")


if __name__ == "__main__":
    teste_vencedor_e_utilidade()
    teste_arvore_completa()
    teste_bloqueia_e_vence()
    teste_nunca_perde_e_algoritmos_concordam()
    print("\nTodos os testes passaram.")
