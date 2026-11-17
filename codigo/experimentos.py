"""
experimentos.py
===============
Coleta os dados usados no relatório (modo Humano x Computador) e gera os
gráficos e tabelas na pasta ../resultados.

Metodologia
-----------
O "humano" é simulado de forma EXAUSTIVA: em cada vez dele, são testadas
TODAS as casas livres. Assim, são percorridas todas as partidas possíveis
contra o computador (que joga de forma determinística). Em cada decisão do
computador, os DOIS algoritmos são executados sobre o mesmo tabuleiro, o que
garante uma comparação justa. O tempo de cada decisão é o menor entre
REPETICOES execuções (reduz o ruído do sistema operacional).

Dois cenários: "computador começa" e "humano começa".

Como executar:   python experimentos.py        (leva cerca de 1 minuto)
"""

import csv
import json
import os
import platform
import sys

import matplotlib
matplotlib.use("Agg")                      # gera imagens sem abrir janela
import matplotlib.pyplot as plt

from algoritmos import (
    ALFABETA, MINIMAX, NOMES, VAZIO,
    casas_livres, escolher_jogada, novo_tabuleiro, oponente, valor_terminal,
)

REPETICOES = 3
ALGORITMOS = (MINIMAX, ALFABETA)
CENARIOS = {
    "computador_comeca": ("Computador começa", "X"),
    "humano_comeca": ("Humano começa", "O"),
}
COR = {MINIMAX: "#1f77b4", ALFABETA: "#ff7f0e"}

PASTA_CODIGO = os.path.dirname(os.path.abspath(__file__))
PASTA_RES = os.path.join(PASTA_CODIGO, "..", "resultados")


# --------------------------------------------------------------------------
# Coleta
# --------------------------------------------------------------------------
def medir(tab, ia, algoritmo):
    """Executa a decisão REPETICOES vezes; nós são fixos, tempo = mínimo."""
    melhor_tempo, dec = None, None
    for _ in range(REPETICOES):
        dec = escolher_jogada(tab, ia, algoritmo)
        if melhor_tempo is None or dec.tempo < melhor_tempo:
            melhor_tempo = dec.tempo
    dec.tempo = melhor_tempo
    return dec


def explorar(tab, vez, comp, hist, decisoes, partidas):
    """Percorre todas as partidas possíveis contra o computador."""
    util = valor_terminal(tab, comp)
    if util is not None:
        partidas.append({
            "resultado": util,                       # do ponto de vista do computador
            "jogadas": sum(1 for v in tab if v != VAZIO),
            "nos": {a: sum(h[a].nos for h in hist) for a in ALGORITMOS},
            "tempo": {a: sum(h[a].tempo for h in hist) for a in ALGORITMOS},
        })
        return

    if vez == comp:
        dec = {a: medir(tab, comp, a) for a in ALGORITMOS}
        assert dec[MINIMAX].jogada == dec[ALFABETA].jogada, "algoritmos divergiram!"
        assert dec[MINIMAX].valor == dec[ALFABETA].valor
        decisoes.append({
            "indice": len(hist) + 1,                 # 1ª, 2ª, 3ª... jogada do computador
            "tabuleiro": "".join(tab).replace(" ", "_"),
            "jogada": dec[MINIMAX].jogada + 1,
            "valor": dec[MINIMAX].valor,
            "dec": dec,
        })
        tab[dec[MINIMAX].jogada] = comp
        explorar(tab, oponente(vez), comp, hist + [dec], decisoes, partidas)
        tab[dec[MINIMAX].jogada] = VAZIO
    else:
        for i in casas_livres(tab):                  # humano tenta TODAS as casas
            tab[i] = vez
            explorar(tab, oponente(vez), comp, hist, decisoes, partidas)
            tab[i] = VAZIO


def media(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def coletar():
    resumo = {
        "ambiente": {
            "python": platform.python_version(),
            "sistema": f"{platform.system()} {platform.release()}",
            "processador": platform.processor() or platform.machine(),
            "repeticoes_tempo": REPETICOES,
        },
        "cenarios": {},
    }
    linhas_decisoes = []

    for chave, (rotulo, comp) in CENARIOS.items():
        print(f"Coletando cenário: {rotulo} ...", flush=True)
        decisoes, partidas = [], []
        explorar(novo_tabuleiro(), "X", comp, [], decisoes, partidas)

        # --- por número da jogada do computador ---
        por_jogada = {a: [] for a in ALGORITMOS}
        for idx in sorted({d["indice"] for d in decisoes}):
            grupo = [d for d in decisoes if d["indice"] == idx]
            for a in ALGORITMOS:
                nos = [d["dec"][a].nos for d in grupo]
                tempos = [d["dec"][a].tempo * 1000 for d in grupo]
                por_jogada[a].append({
                    "indice": idx, "decisoes": len(grupo),
                    "nos_medio": media(nos), "nos_min": min(nos), "nos_max": max(nos),
                    "tempo_medio_ms": media(tempos), "tempo_max_ms": max(tempos),
                })

        # --- por partida completa ---
        por_partida = {
            a: {
                "nos_medio": media(p["nos"][a] for p in partidas),
                "nos_max": max(p["nos"][a] for p in partidas),
                "tempo_medio_ms": media(p["tempo"][a] * 1000 for p in partidas),
                "tempo_max_ms": max(p["tempo"][a] * 1000 for p in partidas),
            } for a in ALGORITMOS
        }

        # --- custo / qualidade da solução ---
        resultados = {
            "vitorias_computador": sum(p["resultado"] == 1 for p in partidas),
            "empates": sum(p["resultado"] == 0 for p in partidas),
            "derrotas_computador": sum(p["resultado"] == -1 for p in partidas),
        }
        tamanhos = {}
        for p in partidas:
            tamanhos[p["jogadas"]] = tamanhos.get(p["jogadas"], 0) + 1

        resumo["cenarios"][chave] = {
            "rotulo": rotulo,
            "partidas": len(partidas),
            "decisoes": len(decisoes),
            "decisoes_com_mesma_jogada": len(decisoes),   # assert acima garante
            "resultados": resultados,
            "duracao_media_jogadas": media(p["jogadas"] for p in partidas),
            "duracao_por_tamanho": {str(k): v for k, v in sorted(tamanhos.items())},
            "valor_primeira_jogada": decisoes[0]["valor"],
            "por_jogada": por_jogada,
            "por_partida": por_partida,
        }

        for d in decisoes:
            for a in ALGORITMOS:
                linhas_decisoes.append([
                    rotulo, NOMES[a], d["indice"], d["tabuleiro"], d["jogada"],
                    d["valor"], d["dec"][a].nos, f"{d['dec'][a].tempo * 1000:.4f}",
                ])

    return resumo, linhas_decisoes


# --------------------------------------------------------------------------
# Saídas: CSV, JSON e gráficos
# --------------------------------------------------------------------------
def salvar_tabelas(resumo, linhas_decisoes):
    os.makedirs(PASTA_RES, exist_ok=True)

    with open(os.path.join(PASTA_RES, "decisoes_detalhadas.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cenario", "algoritmo", "n_jogada_computador", "tabuleiro_antes",
                    "casa_escolhida", "valor_minimax", "nos_visitados", "tempo_ms"])
        w.writerows(linhas_decisoes)

    with open(os.path.join(PASTA_RES, "resumo_por_jogada.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cenario", "algoritmo", "n_jogada_computador", "qtd_decisoes",
                    "nos_medio", "nos_min", "nos_max", "tempo_medio_ms", "tempo_max_ms"])
        for c in resumo["cenarios"].values():
            for a in ALGORITMOS:
                for r in c["por_jogada"][a]:
                    w.writerow([c["rotulo"], NOMES[a], r["indice"], r["decisoes"],
                                f"{r['nos_medio']:.1f}", r["nos_min"], r["nos_max"],
                                f"{r['tempo_medio_ms']:.4f}", f"{r['tempo_max_ms']:.4f}"])

    with open(os.path.join(PASTA_RES, "resumo_por_partida.csv"), "w",
              newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cenario", "algoritmo", "partidas", "nos_medio_por_partida",
                    "nos_max_por_partida", "tempo_medio_ms_por_partida",
                    "tempo_max_ms_por_partida"])
        for c in resumo["cenarios"].values():
            for a in ALGORITMOS:
                p = c["por_partida"][a]
                w.writerow([c["rotulo"], NOMES[a], c["partidas"],
                            f"{p['nos_medio']:.1f}", p["nos_max"],
                            f"{p['tempo_medio_ms']:.3f}", f"{p['tempo_max_ms']:.3f}"])

    with open(os.path.join(PASTA_RES, "resumo.json"), "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)


def fmt(v):
    return f"{v:,.0f}".replace(",", ".")


def fmt_tempo(v):
    """Formata milissegundos com casas decimais adequadas ao tamanho."""
    if v >= 100:
        t = f"{v:.0f}"
    elif v >= 10:
        t = f"{v:.1f}"
    elif v >= 1:
        t = f"{v:.2f}"
    elif v >= 0.1:
        t = f"{v:.3f}"
    else:
        t = f"{v:.4f}"
    return t.replace(".", ",")


def grafico_por_jogada(resumo, campo, ylabel, titulo, arquivo, casas=0):
    """Barras agrupadas (Minimax x Alfa-Beta) por nº da jogada do computador."""
    fig, eixos = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, (chave, c) in zip(eixos, resumo["cenarios"].items()):
        n = len(c["por_jogada"][MINIMAX])
        largura = 0.38
        for k, a in enumerate(ALGORITMOS):
            xs = [i + (k - 0.5) * largura for i in range(n)]
            ys = [r[campo] for r in c["por_jogada"][a]]
            barras = ax.bar(xs, ys, largura, label=NOMES[a], color=COR[a])
            for b, y in zip(barras, ys):
                txt = fmt(y) if casas == 0 else fmt_tempo(y)
                ax.annotate(txt, (b.get_x() + b.get_width() / 2, y),
                            ha="center", va="bottom", fontsize=7,
                            xytext=(0, 2), textcoords="offset points", rotation=90)
        ax.set_yscale("log")
        ax.set_ylim(top=ax.get_ylim()[1] * 6)
        ax.set_xticks(range(n))
        ax.set_xticklabels([f"{r['indice']}ª" for r in c["por_jogada"][MINIMAX]])
        ax.set_xlabel("Jogada do computador na partida")
        ax.set_ylabel(ylabel + " (escala log)")
        ax.set_title(c["rotulo"])
        ax.grid(axis="y", alpha=0.3)
        ax.legend(loc="upper right")
    fig.suptitle(titulo, fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA_RES, arquivo), dpi=150)
    plt.close(fig)


def grafico_totais(resumo):
    """Média por partida completa: nós e tempo."""
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4.6))
    chaves = list(resumo["cenarios"])
    rotulos = [resumo["cenarios"][k]["rotulo"] for k in chaves]
    largura = 0.36
    for ax, campo, ylabel, casas in (
        (eixos[0], "nos_medio", "Nós visitados por partida", 0),
        (eixos[1], "tempo_medio_ms", "Tempo por partida (ms)", 2),
    ):
        for k, a in enumerate(ALGORITMOS):
            xs = [i + (k - 0.5) * largura for i in range(len(chaves))]
            ys = [resumo["cenarios"][c]["por_partida"][a][campo] for c in chaves]
            barras = ax.bar(xs, ys, largura, label=NOMES[a], color=COR[a])
            for b, y in zip(barras, ys):
                txt = fmt(y) if casas == 0 else fmt_tempo(y)
                ax.annotate(txt, (b.get_x() + b.get_width() / 2, y), ha="center",
                            va="bottom", fontsize=8, xytext=(0, 2),
                            textcoords="offset points")
        ax.set_yscale("log")
        ax.set_ylim(top=ax.get_ylim()[1] * 3)
        ax.set_xticks(range(len(chaves)))
        ax.set_xticklabels(rotulos)
        ax.set_ylabel(ylabel + " (escala log)")
        ax.grid(axis="y", alpha=0.3)
        ax.legend()
    fig.suptitle("Custo médio por partida completa (média sobre todas as partidas possíveis)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA_RES, "grafico3_totais_por_partida.png"), dpi=150)
    plt.close(fig)


def grafico_reducao(resumo):
    """Redução percentual de nós e de tempo obtida pela poda, por jogada."""
    fig, eixos = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
    for ax, (chave, c) in zip(eixos, resumo["cenarios"].items()):
        mm, ab = c["por_jogada"][MINIMAX], c["por_jogada"][ALFABETA]
        xs = [r["indice"] for r in mm]
        red_nos = [100 * (1 - b["nos_medio"] / m["nos_medio"]) for m, b in zip(mm, ab)]
        red_tmp = [100 * (1 - b["tempo_medio_ms"] / m["tempo_medio_ms"]) for m, b in zip(mm, ab)]
        ax.plot(xs, red_nos, "o-", color="#2ca02c", label="Redução de nós")
        ax.plot(xs, red_tmp, "s--", color="#d62728", label="Redução de tempo")
        for x, y in zip(xs, red_nos):
            ax.annotate(f"{y:.1f}%".replace(".", ","), (x, y), ha="center",
                        xytext=(0, 7), textcoords="offset points", fontsize=8)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{x}ª" for x in xs])
        ax.set_xlabel("Jogada do computador na partida")
        ax.set_title(c["rotulo"])
        ax.set_ylim(-15, 112)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", bbox_to_anchor=(1.0, 0.88))
    eixos[0].set_ylabel("Redução em relação ao Minimax (%)")
    fig.suptitle("Economia obtida pela poda alfa-beta", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA_RES, "grafico4_reducao_percentual.png"), dpi=150)
    plt.close(fig)


def grafico_resultados(resumo):
    """Distribuição (%) dos resultados das partidas (qualidade da solução)."""
    fig, ax = plt.subplots(figsize=(9, 3.8))
    chaves = list(resumo["cenarios"])
    rotulos = [resumo["cenarios"][k]["rotulo"] for k in chaves]
    categorias = (("vitorias_computador", "Vitória do computador (+1)", "#2ca02c"),
                  ("empates", "Empate (0)", "#7f7f7f"),
                  ("derrotas_computador", "Derrota do computador (-1)", "#d62728"))
    base = [0.0] * len(chaves)
    for campo, nome, cor in categorias:
        absolutos = [resumo["cenarios"][k]["resultados"][campo] for k in chaves]
        totais = [resumo["cenarios"][k]["partidas"] for k in chaves]
        pct = [100 * a / t for a, t in zip(absolutos, totais)]
        ax.barh(rotulos, pct, left=base, label=nome, color=cor, height=0.5)
        for i, (a, p) in enumerate(zip(absolutos, pct)):
            if a == 0:
                continue
            txt = f"{a} ({p:.1f}%)".replace(".", ",")
            if p >= 8:
                ax.text(base[i] + p / 2, i, txt, ha="center", va="center",
                        color="white", fontweight="bold", fontsize=9)
            else:
                ax.text(base[i] + p / 2, i + 0.3, txt, ha="center", va="bottom",
                        color="black", fontsize=9)
        base = [b + p for b, p in zip(base, pct)]
    ax.set_xlim(0, 100)
    ax.set_xlabel("% das partidas possíveis")
    ax.set_title("Resultado de todas as partidas possíveis contra o computador",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(PASTA_RES, "grafico5_resultados_das_partidas.png"), dpi=150)
    plt.close(fig)


def main():
    resumo, linhas = coletar()
    salvar_tabelas(resumo, linhas)
    grafico_por_jogada(resumo, "nos_medio", "Nós visitados (média)",
                       "Passos (nós visitados) por jogada do computador",
                       "grafico1_nos_por_jogada.png")
    grafico_por_jogada(resumo, "tempo_medio_ms", "Tempo (ms, média)",
                       "Tempo de decisão por jogada do computador",
                       "grafico2_tempo_por_jogada.png", casas=2)
    grafico_totais(resumo)
    grafico_reducao(resumo)
    grafico_resultados(resumo)
    print(f"\nPronto! Arquivos gerados em: {os.path.abspath(PASTA_RES)}")


if __name__ == "__main__":
    main()
