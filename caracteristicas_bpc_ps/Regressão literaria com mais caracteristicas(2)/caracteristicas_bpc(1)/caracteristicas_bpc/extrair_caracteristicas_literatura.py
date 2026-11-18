"""
Extrai as características textuais que a literatura da área usa, para complementar
as 61 já calculadas em `caracteristicas.csv`.

Cada família abaixo vem de um conjunto de trabalhos, não de escolha arbitrária:

  (A) LEGIBILIDADE — fórmulas clássicas de readability. Flesch Reading Ease e
      Flesch-Kincaid usam sílabas por palavra como proxy de sofisticação lexical e
      palavras por sentença como proxy de complexidade sintática; Gunning Fog, SMOG,
      Coleman-Liau, ARI, LIX e RIX são variantes com outras proxies. São as medidas
      citadas em praticamente todo trabalho de complexidade textual.
      Implementadas aqui à mão (sem textstat/cmudict) para ficarem auditáveis.

  (B) SOFISTICAÇÃO / RARIDADE LEXICAL — "lexical sophistication" no sentido de
      O'Dell et al. e Lu: proporção de palavras fora das K mais frequentes da língua.
      Usamos a frequência Zipf da biblioteca `wordfreq` (escala logarítmica: ~7 para
      "the", ~3 para palavra incomum, ~1,7 para palavra rara). Substitui a lista
      Dale-Chall, que não está disponível offline aqui, por uma medida contínua.

  (C) DIVERSIDADE LEXICAL — MTLD (McCarthy) e HD-D (Malvern/McCarthy & Jarvis), que
      são as medidas padrão por serem robustas ao tamanho do texto, ao contrário do
      TTR simples. O MATTR já existia no extrator anterior.

  (D) COMPRESSÃO E INFORMAÇÃO — razão de compressão gzip e entropia de caracteres e
      de palavras. Entram porque a força preditiva do PRESELECT é definida sobre a
      perda de compressão dos modelos: é a família mais diretamente ligada ao alvo.

  (E) HEURÍSTICAS DE QUALIDADE DE CORPUS — os sinais do Gopher (Rae et al., 2021),
      C4 (Raffel et al., 2020) e RefinedWeb/RedPajama-v2, calculados como variáveis
      contínuas em vez de regras de corte: tamanho médio de palavra, razão
      símbolo/palavra, linhas em bullet, linhas terminadas em reticências, contagem
      de stopwords, fração de palavras alfabéticas, linhas com pontuação final,
      linhas duplicadas e fração de caracteres em n-gramas repetidos.
      São os filtros efetivamente usados para montar os corpora de pré-treino, ou
      seja, a definição operacional de "texto bom" na área de seleção de dados.

  (F) COMPLEXIDADE SINTÁTICA ADICIONAL — densidade de orações e complexidade de
      sintagma nominal, na linha do L2SCA de Lu.

Uso:
  python extrair_caracteristicas_literatura.py \
      --entrada documentos_forca_preditiva.jsonl \
      --saida   caracteristicas_literatura.csv
"""

import argparse
import gzip
import json
import math
import re
import statistics
from collections import Counter
from pathlib import Path

import pandas as pd
import spacy
from lexicalrichness import LexicalRichness
from wordfreq import zipf_frequency

# ---------------------------------------------------------------------------
# Listas e expressões fixas
# ---------------------------------------------------------------------------

# Stopwords do Gopher: a regra original exige pelo menos 2 destas no documento.
STOPWORDS_GOPHER = {"the", "be", "to", "of", "and", "that", "have", "with"}

# Bullets reconhecidos pelo RefinedWeb/RedPajama-v2.
BULLETS = ("•", "‣", "▶", "◀", "◦", "■",
           "□", "▪", "▫", "–", "-", "*", "+")

RETICENCIAS = ("...", "…")
PONTUACAO_FINAL = (".", "!", "?", '"', "'", "”")

VOGAIS = "aeiouy"
RE_PALAVRA = re.compile(r"[a-zA-Z']+")


def razao(a, b):
    return a / b if b else 0.0


# ---------------------------------------------------------------------------
# (A) Legibilidade
# ---------------------------------------------------------------------------

def contar_silabas(palavra):
    """Heurística padrão de contagem de sílabas em inglês (grupos de vogais).

    Conta cada grupo contíguo de vogais como uma sílaba, desconta o 'e' mudo final
    e garante o mínimo de uma sílaba. É a aproximação usada nas implementações
    clássicas das fórmulas de legibilidade quando não há dicionário fonético.
    """
    palavra = palavra.lower().strip("'")
    if not palavra:
        return 0
    grupos = 0
    vogal_anterior = False
    for letra in palavra:
        eh_vogal = letra in VOGAIS
        if eh_vogal and not vogal_anterior:
            grupos += 1
        vogal_anterior = eh_vogal
    if palavra.endswith("e") and not palavra.endswith(("le", "ee")) and grupos > 1:
        grupos -= 1
    return max(grupos, 1)


def legibilidade(palavras, n_sentencas, n_chars_alfa):
    """As oito fórmulas, a partir de contagens já feitas."""
    n_p = len(palavras)
    if n_p == 0 or n_sentencas == 0:
        return {k: 0.0 for k in (
            "leg_flesch_reading_ease", "leg_flesch_kincaid", "leg_gunning_fog",
            "leg_smog", "leg_coleman_liau", "leg_ari", "leg_lix", "leg_rix")}

    silabas = [contar_silabas(p) for p in palavras]
    total_silabas = sum(silabas)
    # "palavra complexa" (Gunning Fog / SMOG): 3 sílabas ou mais
    n_complexas = sum(s >= 3 for s in silabas)
    # "palavra longa" (LIX / RIX): mais de 6 caracteres
    n_longas = sum(len(p) > 6 for p in palavras)

    pps = n_p / n_sentencas            # palavras por sentença
    spp = total_silabas / n_p          # sílabas por palavra
    cpp = n_chars_alfa / n_p           # caracteres por palavra

    return {
        # Flesch (1948): quanto MAIOR, mais fácil de ler
        "leg_flesch_reading_ease": 206.835 - 1.015 * pps - 84.6 * spp,
        # Flesch-Kincaid (1975): série escolar; quanto maior, mais difícil
        "leg_flesch_kincaid": 0.39 * pps + 11.8 * spp - 15.59,
        # Gunning Fog (1952)
        "leg_gunning_fog": 0.4 * (pps + 100 * razao(n_complexas, n_p)),
        # SMOG (McLaughlin, 1969)
        "leg_smog": 1.0430 * math.sqrt(n_complexas * (30 / n_sentencas)) + 3.1291,
        # Coleman-Liau (1975): usa letras em vez de sílabas
        "leg_coleman_liau": 0.0588 * (cpp * 100) - 0.296 * (n_sentencas / n_p * 100) - 15.8,
        # Automated Readability Index (Smith & Senter, 1967)
        "leg_ari": 4.71 * cpp + 0.5 * pps - 21.43,
        # LIX (Björnsson, 1968)
        "leg_lix": pps + 100 * razao(n_longas, n_p),
        # RIX (Anderson, 1983)
        "leg_rix": razao(n_longas, n_sentencas),
    }


# ---------------------------------------------------------------------------
# (B) Sofisticação / raridade lexical
# ---------------------------------------------------------------------------

def raridade_lexical(palavras_conteudo):
    """Frequência Zipf: ~7 = muito comum ("the"), ~3 = incomum, <2 = rara."""
    if not palavras_conteudo:
        return {k: 0.0 for k in (
            "rar_zipf_medio", "rar_zipf_desvio", "rar_frac_raras",
            "rar_frac_muito_raras", "rar_frac_desconhecidas", "rar_zipf_p10")}

    zipfs = [zipf_frequency(p, "en") for p in palavras_conteudo]
    n = len(zipfs)
    ordenados = sorted(zipfs)
    return {
        "rar_zipf_medio": statistics.mean(zipfs),
        "rar_zipf_desvio": statistics.pstdev(zipfs) if n > 1 else 0.0,
        # sofisticação lexical no sentido de Lu: fora das mais frequentes
        "rar_frac_raras": razao(sum(z < 3.0 for z in zipfs), n),
        "rar_frac_muito_raras": razao(sum(z < 2.0 for z in zipfs), n),
        "rar_frac_desconhecidas": razao(sum(z == 0.0 for z in zipfs), n),
        # décimo percentil: o quão rara é a cauda do vocabulário do texto
        "rar_zipf_p10": ordenados[max(0, int(0.10 * n) - 1)],
    }


# ---------------------------------------------------------------------------
# (C) Diversidade lexical
# ---------------------------------------------------------------------------

def diversidade_lexical(palavras):
    """MTLD e HD-D, robustas ao tamanho do texto (TTR simples não é)."""
    vazio = {"div_mtld": 0.0, "div_hdd": 0.0}
    if len(palavras) < 50:
        return vazio
    try:
        lr = LexicalRichness(" ".join(palavras))
        return {"div_mtld": float(lr.mtld(threshold=0.72)),
                "div_hdd": float(lr.hdd(draws=42))}
    except Exception:
        return vazio


# ---------------------------------------------------------------------------
# (D) Compressão e informação
# ---------------------------------------------------------------------------

def entropia(contagens):
    total = sum(contagens.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in contagens.values())


def compressao_e_informacao(texto, palavras):
    bytes_originais = texto.encode("utf-8")
    if not bytes_originais:
        return {k: 0.0 for k in ("inf_razao_gzip", "inf_entropia_char",
                                 "inf_entropia_palavra", "inf_entropia_palavra_norm")}
    comprimido = gzip.compress(bytes_originais, compresslevel=6)
    ent_palavra = entropia(Counter(palavras))
    n_tipos = len(set(palavras))
    return {
        # razão de compressão: quanto MENOR, mais repetitivo é o texto
        "inf_razao_gzip": len(comprimido) / len(bytes_originais),
        "inf_entropia_char": entropia(Counter(texto)),
        "inf_entropia_palavra": ent_palavra,
        # normalizada pelo máximo possível (log2 do número de tipos)
        "inf_entropia_palavra_norm": razao(ent_palavra, math.log2(n_tipos)) if n_tipos > 1 else 0.0,
    }


# ---------------------------------------------------------------------------
# (E) Heurísticas de qualidade de corpus (Gopher, C4, RefinedWeb)
# ---------------------------------------------------------------------------

def frac_chars_em_ngramas(palavras, n, modo):
    """modo 'top': fração de caracteres no n-grama mais frequente.
       modo 'dupe': fração de caracteres em n-gramas que aparecem mais de uma vez."""
    if len(palavras) < n:
        return 0.0
    ngramas = [" ".join(palavras[i:i + n]) for i in range(len(palavras) - n + 1)]
    contagem = Counter(ngramas)
    total_chars = sum(len(p) for p in palavras)
    if total_chars == 0:
        return 0.0
    if modo == "top":
        grama, vezes = contagem.most_common(1)[0]
        return razao(len(grama.replace(" ", "")) * vezes, total_chars)
    repetidos = sum(len(g.replace(" ", "")) * (v - 1) for g, v in contagem.items() if v > 1)
    return razao(repetidos, total_chars)


def heuristicas_qualidade(texto, palavras):
    linhas = [ln for ln in texto.split("\n") if ln.strip()]
    n_linhas = len(linhas)
    n_p = len(palavras)
    minusculas = [p.lower() for p in palavras]

    simbolos = texto.count("#") + texto.count("...") + texto.count("…")
    paragrafos = [p for p in texto.split("\n\n") if p.strip()]

    return {
        # --- Gopher (Rae et al., 2021) ---
        "qlt_tam_medio_palavra": razao(sum(len(p) for p in palavras), n_p),
        "qlt_razao_simbolo_palavra": razao(simbolos, n_p),
        "qlt_frac_linhas_bullet": razao(
            sum(ln.lstrip().startswith(BULLETS) for ln in linhas), n_linhas),
        "qlt_frac_linhas_reticencias": razao(
            sum(ln.rstrip().endswith(RETICENCIAS) for ln in linhas), n_linhas),
        "qlt_n_stopwords_gopher": sum(p in STOPWORDS_GOPHER for p in minusculas),
        "qlt_frac_palavras_alfabeticas": razao(
            sum(any(c.isalpha() for c in p) for p in palavras), n_p),
        # --- C4 (Raffel et al., 2020) ---
        "qlt_frac_linhas_pontuacao_final": razao(
            sum(ln.rstrip().endswith(PONTUACAO_FINAL) for ln in linhas), n_linhas),
        # --- repetição (Gopher / RefinedWeb) ---
        "qlt_frac_linhas_duplicadas": 1 - razao(len(set(linhas)), n_linhas),
        "qlt_frac_paragrafos_duplicados": 1 - razao(len(set(paragrafos)), len(paragrafos)),
        "qlt_frac_chars_top_2gram": frac_chars_em_ngramas(minusculas, 2, "top"),
        "qlt_frac_chars_top_3gram": frac_chars_em_ngramas(minusculas, 3, "top"),
        "qlt_frac_chars_dupe_5gram": frac_chars_em_ngramas(minusculas, 5, "dupe"),
        # --- caracteres (Nemo / RefinedWeb) ---
        "qlt_frac_chars_nao_alfanum": razao(
            sum(not c.isalnum() and not c.isspace() for c in texto), len(texto)),
        "qlt_frac_chars_numericos": razao(sum(c.isdigit() for c in texto), len(texto)),
        "qlt_frac_chars_espaco": razao(sum(c.isspace() for c in texto), len(texto)),
    }


# ---------------------------------------------------------------------------
# (F) Complexidade sintática adicional (linha do L2SCA de Lu)
# ---------------------------------------------------------------------------

DEPS_ORACAO = {"ccomp", "xcomp", "advcl", "acl", "relcl", "csubj", "csubjpass"}
DEPS_MODIFICADOR_NOMINAL = {"amod", "nmod", "compound", "poss", "nummod", "det"}


def sintaxe_adicional(doc, sentencas):
    n_sent = len(sentencas)
    substantivos = [t for t in doc if t.pos_ in ("NOUN", "PROPN")]
    oracoes = sum(t.dep_ in DEPS_ORACAO for t in doc) + n_sent
    return {
        "sinx_oracoes_por_sentenca": razao(oracoes, n_sent),
        "sinx_palavras_por_oracao": razao(sum(t.is_alpha for t in doc), oracoes),
        "sinx_modificadores_por_substantivo": razao(
            sum(t.dep_ in DEPS_MODIFICADOR_NOMINAL for t in doc), len(substantivos)),
        "sinx_frac_sentencas_longas": razao(
            sum(sum(t.is_alpha for t in s) > 25 for s in sentencas), n_sent),
        "sinx_frac_sentencas_curtas": razao(
            sum(sum(t.is_alpha for t in s) < 5 for s in sentencas), n_sent),
    }


# ---------------------------------------------------------------------------
# Extração de um documento
# ---------------------------------------------------------------------------

def extrair(doc, texto):
    palavras = [t.text for t in doc if t.is_alpha]
    minusculas = [p.lower() for p in palavras]
    conteudo = [t.lemma_.lower() for t in doc
                if t.pos_ in ("NOUN", "PROPN", "VERB", "ADJ", "ADV") and t.is_alpha]
    sentencas = [s for s in doc.sents if any(t.is_alpha for t in s)]
    n_chars_alfa = sum(len(p) for p in palavras)

    carac = {}
    carac.update(legibilidade(palavras, len(sentencas), n_chars_alfa))
    carac.update(raridade_lexical(conteudo))
    carac.update(diversidade_lexical(minusculas))
    carac.update(compressao_e_informacao(texto, minusculas))
    carac.update(heuristicas_qualidade(texto, palavras))
    carac.update(sintaxe_adicional(doc, sentencas))
    return carac


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", required=True)
    ap.add_argument("--saida", required=True)
    ap.add_argument("--modelo", default="en_core_web_sm")
    ap.add_argument("--max-chars", type=int, default=100_000)
    ap.add_argument("--processos", type=int, default=1)
    args = ap.parse_args()

    documentos = [json.loads(l) for l in open(args.entrada, encoding="utf-8")]
    print(f"{len(documentos)} documentos lidos")

    nlp = spacy.load(args.modelo)
    nlp.max_length = max(nlp.max_length, args.max_chars + 1000)
    textos = [d["text"][: args.max_chars] for d in documentos]

    linhas = []
    for i, (documento, doc) in enumerate(
            zip(documentos, nlp.pipe(textos, batch_size=16, n_process=args.processos))):
        carac = extrair(doc, textos[i])
        carac["document_id"] = documento["document_id"]
        linhas.append(carac)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(documentos)}")

    tabela = pd.DataFrame(linhas)
    colunas = ["document_id"] + [c for c in tabela.columns if c != "document_id"]
    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    tabela[colunas].to_csv(args.saida, index=False)
    print(f"{len(tabela)} linhas, {len(colunas) - 1} características -> {args.saida}")


if __name__ == "__main__":
    principal()
