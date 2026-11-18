"""
Auditoria de circularidade e regressão limpa.

O BPC é a perda de compressão do modelo sobre o texto, em bits por caractere.
Qualquer variável que seja ela mesma uma medida de compressibilidade ou de
previsibilidade do texto explica o BPC por tautologia, não por achado.

Três camadas:

  CAMADA 1 — circulares, removidas.
    inf_razao_gzip            razão de compressão gzip: mesmo construto do BPC,
                              só trocando o compressor neural por um clássico.
    inf_entropia_char         entropia de caractere: literalmente bits por
                              caractere sob um modelo unigrama. É a definição.
    inf_entropia_palavra      o mesmo no nível da palavra.
    inf_entropia_palavra_norm idem, normalizada.

  CAMADA 2 — limítrofes, testadas separadamente.
    Medidas de repetição. Repetição é o que torna um texto comprimível, então
    elas tangenciam o alvo. Mas são propriedades estruturais que um revisor
    enxerga e um reescritor consegue mudar ("não se repita"), e entram como
    sinais de qualidade nos filtros do Gopher e do RefinedWeb. Por isso o
    modelo é rodado com e sem elas, e a decisão fica explícita.

  CAMADA 3 — legítimas.
    Tudo o mais. Raridade lexical, por exemplo, NÃO é circular: mede o
    vocabulário contra um corpus de referência externo, e não contra as
    estatísticas do próprio texto. "Textos de vocabulário incomum são mais
    difíceis de prever" é um achado, não uma tautologia.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.model_selection import train_test_split

import sys
sys.path.insert(0, "/home/claude/entrega_regressao")
import regressao_literatura as R

CAMADA_1 = ["inf_razao_gzip", "inf_entropia_char",
            "inf_entropia_palavra", "inf_entropia_palavra_norm"]

CAMADA_2 = ["qlt_frac_chars_top_2gram", "qlt_frac_chars_top_3gram",
            "qlt_frac_chars_dupe_5gram", "qlt_frac_linhas_duplicadas",
            "qlt_frac_paragrafos_duplicados"]


def main():
    base, feats, _ = R.montar_base()
    treino, val = train_test_split(base, test_size=0.5, random_state=R.SEMENTE)

    cenarios = {
        "Com tudo (versao anterior, CIRCULAR)": [],
        "Sem a camada 1 (compressao e entropia)": CAMADA_1,
        "Sem as camadas 1 e 2 (tambem sem repeticao)": CAMADA_1 + CAMADA_2,
    }

    md = ["# Auditoria de circularidade\n",
          "O BPC é a perda de compressão do modelo sobre o texto. Variáveis que são elas "
          "mesmas medidas de compressibilidade explicam o BPC por tautologia.\n"]
    w = md.append

    w("\n## Efeito de remover as variáveis circulares\n")
    w("\n| Conjunto candidato | nº de variáveis | R² na validação |")
    w("|---|---:|---:|")

    resultados = {}
    for nome, remover in cenarios.items():
        disponiveis = [f for f in feats if f not in remover]
        escolhidas, ranking = R.selecionar(treino, disponiveis, "Y_bpc", k=8,
                                           excluir_prefixos=("ort_",))
        m = smf.ols("Y_bpc ~ " + " + ".join(escolhidas), data=treino).fit()
        r2 = R.r2_fora(m, val, "Y_bpc")
        resultados[nome] = (escolhidas, ranking, m, r2)
        w(f"| {nome} | {len(disponiveis)} | {r2:.3f} |")

    for nome in ["Sem a camada 1 (compressao e entropia)",
                 "Sem as camadas 1 e 2 (tambem sem repeticao)"]:
        escolhidas, ranking, m, r2 = resultados[nome]
        w(f"\n## Modelo: {nome}\n")
        z = treino.copy()
        for c in escolhidas + ["Y_bpc"]:
            z[c] = (z[c] - z[c].mean()) / z[c].std()
        mz = smf.ols("Y_bpc ~ " + " + ".join(escolhidas), data=z).fit()
        w("\n| característica | β padronizado | p | direção |")
        w("|---|---:|---:|---|")
        for f in escolhidas:
            b = mz.params[f]
            w(f"| `{f}` | {b:+.3f} | {m.pvalues[f]:.4f} | "
              f"{'aumentar' if b > 0 else 'reduzir'} |")
        m_ctrl = smf.ols("Y_bpc ~ " + " + ".join(escolhidas) + " + log_tamanho + C(domain)",
                         data=treino).fit()
        w(f"\nR² no treino {m.rsquared:.3f} · **na validação {r2:.3f}** · "
          f"com tamanho e domínio junto {R.r2_fora(m_ctrl, val, 'Y_bpc'):.3f}\n")
        w("\nAs 12 mais fortes individualmente neste conjunto:\n")
        w("\n| característica | \\|t\\| |")
        w("|---|---:|")
        for f, t, p in ranking[:12]:
            w(f"| `{f}` | {t:.2f} |")

    # famílias sem as circulares
    w("\n## Famílias, já sem as variáveis circulares\n")
    limpas = [f for f in feats if f not in CAMADA_1]
    w("\n| Família | variáveis | R² na validação |")
    w("|---|---:|---:|")
    linhas_fam = []
    for nome, prefixo in R.FAMILIAS.items():
        membros = [f for f in limpas if f.startswith(prefixo)]
        if not membros:
            continue
        m = smf.ols("Y_bpc ~ " + " + ".join(membros), data=treino).fit()
        linhas_fam.append((nome, len(membros), R.r2_fora(m, val, "Y_bpc")))
    for nome, n, r2 in sorted(linhas_fam, key=lambda r: -r[2]):
        w(f"| {nome} | {n} | {r2:.3f} |")
    for nome, formula in [("*tamanho do texto (baseline)*", "log_tamanho"),
                          ("*domínio do site (baseline)*", "C(domain)")]:
        m = smf.ols(f"Y_bpc ~ {formula}", data=treino).fit()
        w(f"| {nome} | 1 | {R.r2_fora(m, val, 'Y_bpc'):.3f} |")

    open("auditoria_circularidade.md", "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
