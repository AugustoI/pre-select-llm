"""
Características leves que faltavam, a partir das sugestões do Ícaro.

Não precisam de spaCy nem de modelo: só regex, um dicionário ortográfico offline
(pyspellchecker, 160 mil palavras) e a frequência Zipf do wordfreq. Roda em segundos.

  (G) ORTOGRAFIA E BOA FORMAÇÃO
      ort_frac_erros              fração das palavras fora do dicionário
      ort_frac_erros_corrigiveis  dessas, as que têm correção a 1 edição de distância
                                  (separa erro de digitação de nome próprio e jargão)
      ort_frac_sentencas_maiuscula  sentenças que começam com maiúscula
      ort_frac_caps_no_meio       palavras em CAIXA ALTA no meio do texto

  (H) VOCABULÁRIO RELEVANTE
      voc_frac_banda_informativa  palavras na faixa Zipf de 2 a 5, isto é, nem
                                  ultrafrequentes (artigos, preposições) nem lixo
                                  ou ruído. É a leitura operacional de "densidade
                                  de vocabulário relevante".
      voc_frac_ultracomuns        palavras com Zipf acima de 6

Ressalva: o dicionário é de inglês americano, então grafias britânicas ("colour")
contam como erro. Para comparar documentos entre si isso é um viés constante e
não atrapalha, mas não use ort_frac_erros como medida absoluta de qualidade.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from spellchecker import SpellChecker
from wordfreq import zipf_frequency

RE_PALAVRA = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
RE_SENTENCA = re.compile(r"[^.!?]+[.!?]")

CORRETOR = SpellChecker(distance=1)


def razao(a, b):
    return a / b if b else 0.0


def extrair(texto):
    palavras = RE_PALAVRA.findall(texto)
    minusculas = [p.lower() for p in palavras]
    n = len(palavras)
    if n == 0:
        return {k: 0.0 for k in (
            "ort_frac_erros", "ort_frac_erros_corrigiveis",
            "ort_frac_sentencas_maiuscula", "ort_frac_caps_no_meio",
            "voc_frac_banda_informativa", "voc_frac_ultracomuns")}

    # --- ortografia ---
    unicas = set(minusculas)
    desconhecidas = CORRETOR.unknown(unicas)
    n_erros = sum(p in desconhecidas for p in minusculas)
    # uma "correção" a 1 edição de distância sugere erro de digitação, e não
    # nome próprio ou termo técnico, que o dicionário simplesmente não tem
    corrigiveis = {p for p in desconhecidas if CORRETOR.correction(p) not in (None, p)}
    n_corrigiveis = sum(p in corrigiveis for p in minusculas)

    sentencas = [s.strip() for s in RE_SENTENCA.findall(texto) if s.strip()]
    com_maiuscula = sum(s[0].isupper() for s in sentencas if s and s[0].isalpha())

    # --- vocabulário ---
    zipfs = [zipf_frequency(p, "en") for p in unicas]
    por_tipo = dict(zip(unicas, zipfs))
    faixa = sum(2.0 <= por_tipo[p] <= 5.0 for p in minusculas)
    ultracomuns = sum(por_tipo[p] > 6.0 for p in minusculas)

    return {
        "ort_frac_erros": razao(n_erros, n),
        "ort_frac_erros_corrigiveis": razao(n_corrigiveis, n),
        "ort_frac_sentencas_maiuscula": razao(com_maiuscula, len(sentencas)),
        "ort_frac_caps_no_meio": razao(
            sum(p.isupper() and len(p) > 1 for p in palavras), n),
        "voc_frac_banda_informativa": razao(faixa, n),
        "voc_frac_ultracomuns": razao(ultracomuns, n),
    }


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--max-chars", type=int, default=100_000)
    args = ap.parse_args()

    linhas = []
    with open(args.entrada, encoding="utf-8") as f:
        for i, linha in enumerate(f):
            d = json.loads(linha)
            carac = extrair(d["text"][: args.max_chars])
            carac["document_id"] = d["document_id"]
            linhas.append(carac)
            if (i + 1) % 200 == 0:
                print(f"  {i + 1}")

    tabela = pd.DataFrame(linhas)
    cols = ["document_id"] + [c for c in tabela.columns if c != "document_id"]
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    tabela[cols].to_csv(args.saida, index=False)
    print(f"{len(tabela)} linhas, {len(cols) - 1} características -> {args.saida}")


if __name__ == "__main__":
    principal()
