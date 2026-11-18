"""
Confere se cada prompt de injection mexeu na variável que deveria mexer.

Sem esta checagem não dá para distinguir "a característica não afeta o BPC" de
"o prompt não mudou a característica". Rode antes de gastar GPU calculando o BPC.

Entrada:
  --originais   textos_para_reescrita.jsonl   (campos: indice, text)
  --reescritos  um JSONL com indice, prompt, texto_reescrito

Saída: uma tabela por prompt com a variação média de cada uma das 5 variáveis,
em desvios-padrão da amostra original. A diagonal deve ser forte.
"""
import argparse
import json
import re
from collections import Counter

import numpy as np
import pandas as pd
import spacy
from wordfreq import zipf_frequency

VARIAVEIS = {
    "qlt_frac_linhas_pontuacao_final": ("P1", "aumentar"),
    "coe_frac_vizinhas_com_substantivo_comum": ("P2", "aumentar"),
    "qlt_frac_chars_nao_alfanum": ("P3", "reduzir"),
    "rar_zipf_desvio": ("P4", "reduzir"),
    "qlt_razao_simbolo_palavra": ("P5", "reduzir"),
}

PONTUACAO_FINAL = (".", "!", "?", '"', "'", "”")


def razao(a, b):
    return a / b if b else 0.0


def cinco_variaveis(doc, texto):
    palavras = [t.text for t in doc if t.is_alpha]
    linhas = [ln for ln in texto.split("\n") if ln.strip()]
    sentencas = [s for s in doc.sents if any(t.is_alpha for t in s)]

    # coesao: pares de sentencas vizinhas que compartilham um substantivo
    subs_por_sent = [{t.lemma_.lower() for t in s if t.pos_ in ("NOUN", "PROPN")}
                     for s in sentencas]
    pares = len(subs_por_sent) - 1
    com_comum = sum(bool(subs_por_sent[i] & subs_por_sent[i + 1]) for i in range(max(pares, 0)))

    conteudo = [t.lemma_.lower() for t in doc
                if t.pos_ in ("NOUN", "PROPN", "VERB", "ADJ", "ADV") and t.is_alpha]
    zipfs = [zipf_frequency(p, "en") for p in conteudo]

    simbolos = texto.count("#") + texto.count("...") + texto.count("…")

    return {
        "qlt_frac_linhas_pontuacao_final": razao(
            sum(ln.rstrip().endswith(PONTUACAO_FINAL) for ln in linhas), len(linhas)),
        "coe_frac_vizinhas_com_substantivo_comum": razao(com_comum, pares),
        "qlt_frac_chars_nao_alfanum": razao(
            sum(not c.isalnum() and not c.isspace() for c in texto), len(texto)),
        "rar_zipf_desvio": float(np.std(zipfs)) if len(zipfs) > 1 else 0.0,
        "qlt_razao_simbolo_palavra": razao(simbolos, len(palavras)),
    }


def calcular(nlp, textos):
    return pd.DataFrame([cinco_variaveis(doc, t)
                         for t, doc in zip(textos, nlp.pipe(textos, batch_size=16))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--originais", required=True)
    ap.add_argument("--reescritos", required=True)
    ap.add_argument("--saida", default="verificacao.md")
    ap.add_argument("--modelo", default="en_core_web_sm")
    args = ap.parse_args()

    originais = {}
    for linha in open(args.originais, encoding="utf-8"):
        d = json.loads(linha)
        originais[d["indice"]] = d["text"]

    reescritos = [json.loads(l) for l in open(args.reescritos, encoding="utf-8")]
    print(f"{len(originais)} originais, {len(reescritos)} reescritas")

    faltando = {r["indice"] for r in reescritos} - set(originais)
    if faltando:
        raise SystemExit(f"ERRO: {len(faltando)} índices das reescritas não existem "
                         f"nos originais. Exemplos: {sorted(faltando)[:5]}")

    nlp = spacy.load(args.modelo)
    nlp.max_length = 2_000_000

    indices_usados = sorted({r["indice"] for r in reescritos})
    base_orig = calcular(nlp, [originais[i] for i in indices_usados])
    base_orig["indice"] = indices_usados
    desvios = base_orig[list(VARIAVEIS)].std()

    md = ["# Verificação do injection\n",
          "Variação média de cada variável, em desvios-padrão da amostra original.\n",
          "A diagonal (P1 na variável 1, P2 na 2, e assim por diante) deve ser forte "
          "e no sentido pretendido.\n"]
    linhas = []
    for nome_prompt in sorted({r["prompt"] for r in reescritos}):
        deste = [r for r in reescritos if r["prompt"] == nome_prompt]
        idx = [r["indice"] for r in deste]
        novo = calcular(nlp, [r["texto_reescrito"] for r in deste])
        antigo = base_orig.set_index("indice").loc[idx].reset_index()
        linha = {"prompt": nome_prompt, "n": len(deste)}
        for v in VARIAVEIS:
            linha[v] = float(((novo[v] - antigo[v]) / desvios[v]).mean())
        linhas.append(linha)

    tabela = pd.DataFrame(linhas).set_index("prompt")
    md.append("\n| prompt | n | " + " | ".join(
        f"{VARIAVEIS[v][0]}: {v.split('_', 1)[1][:22]}" for v in VARIAVEIS) + " |")
    md.append("|---|---:|" + "---:|" * len(VARIAVEIS))
    for p, r in tabela.iterrows():
        md.append(f"| **{p}** | {int(r['n'])} | " +
                  " | ".join(f"{r[v]:+.2f}" for v in VARIAVEIS) + " |")

    md.append("\n## Leitura\n")
    for v, (p, sentido) in VARIAVEIS.items():
        if p in tabela.index:
            valor = tabela.loc[p, v]
            ok = (valor > 0.2) if sentido == "aumentar" else (valor < -0.2)
            md.append(f"- **{p}** deveria {sentido} `{v}`: moveu {valor:+.2f} dp — "
                      f"{'funcionou' if ok else '**não funcionou, revisar o prompt**'}")

    open(args.saida, "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
