# Prompts de injection — etapa 3

Material para o Gustavo. São 7 reescritas por documento, como o Ícaro definiu:
5 isolando cada variável, 1 com as cinco juntas e 1 de controle.

## Qual arquivo usar

**`textos_para_reescrita.jsonl`** — 1.000 textos, um por linha, com os campos:

| campo | o que é |
|---|---|
| `indice` | 1 a 1000. **É o que amarra tudo.** Tem que vir junto em cada texto reescrito |
| `document_id` | o hash original do Augusto |
| `domain` | o site de origem |
| `grupo` | `piores_200`, `meio` ou `melhores_200`, por BPC médio |
| `bpc_medio` | média dos 6 modelos, para referência |
| `text` | o texto a reescrever |

O `indice` é o mesmo de `base_mesclada_completa.csv`, já conferido.
Não use `base_mesclada_completa.csv` para a reescrita: ela não tem os textos, só as
características.

### Se 7.000 reescritas for pesado

**`amostra_200_para_reescrita.jsonl`** segue o plano da primeira reunião: 100 sorteados
entre os 200 piores BPC e 100 sorteados do meio. Dá 1.400 reescritas em vez de 7.000.
Sorteio com semente 42, reproduzível.

Referência de tamanho: o texto mediano tem 2.197 caracteres.
BPC médio por grupo: piores 1,493 · meio 1,103 · melhores 0,852.

## O formato da saída

Um registro por reescrita, preservando o índice:

```json
{"indice": 7, "prompt": "P1", "texto_reescrito": "..."}
```

Com `prompt` em `P1`…`P5`, `P6` (todas juntas) e `P0` (controle). Assim dá para
calcular o BPC de cada versão e comparar com o original pelo mesmo índice.

---

## Os 7 prompts

Todos em inglês, porque os textos são em inglês (RefinedWeb). A frase sobre preservar o
conteúdo é importante: sem ela o modelo reescreve o sentido junto e o experimento mede
outra coisa.

### P1 — `qlt_frac_linhas_pontuacao_final` (aumentar)

> Rewrite the text below so that every line ends with terminal punctuation (a period,
> question mark, or exclamation mark). Turn fragments, labels, headings, and list items
> into complete sentences. Preserve all of the original information and meaning. Do not
> change anything else about the style.
>
> Text:
> {texto}

### P2 — `coe_frac_vizinhas_com_substantivo_comum` (aumentar)

> Rewrite the text below so that consecutive sentences are linked by repeated nouns:
> each sentence should reuse at least one key noun from the sentence before it, instead
> of introducing entirely new subjects. Preserve all of the original information and
> meaning. Do not change anything else about the style.
>
> Text:
> {texto}

### P3 — `qlt_frac_chars_nao_alfanum` (reduzir)

> Rewrite the text below using as few non-alphanumeric characters as possible. Remove
> brackets, slashes, pipes, asterisks, bullets, and decorative punctuation, and express
> the same information in plain words instead. Preserve all of the original information
> and meaning. Do not change anything else about the style.
>
> Text:
> {texto}

### P4 — `rar_zipf_desvio` (reduzir)

> Rewrite the text below using vocabulary at a consistent level of commonness. Replace
> unusually rare, technical, or specialized words with ordinary everyday equivalents, and
> avoid mixing very common and very rare words in the same passage. Preserve all of the
> original information and meaning. Do not change anything else about the style.
>
> Text:
> {texto}

### P5 — `qlt_razao_simbolo_palavra` (reduzir)

> Rewrite the text below removing all hash symbols (#) and all ellipses (... or …).
> Rewrite any truncated or trailing-off passage as a complete statement. Preserve all of
> the original information and meaning. Do not change anything else about the style.
>
> Text:
> {texto}

### P6 — as cinco juntas

> Rewrite the text below following all of these rules:
> 1. End every line with terminal punctuation; turn fragments and labels into complete
>    sentences.
> 2. Link consecutive sentences by reusing a key noun from the previous sentence.
> 3. Use as few non-alphanumeric characters as possible; express information in plain
>    words instead of brackets, slashes, pipes, asterisks, or bullets.
> 4. Keep vocabulary at a consistent level of commonness; replace unusually rare or
>    specialized words with ordinary equivalents.
> 5. Remove all hash symbols and ellipses.
>
> Preserve all of the original information and meaning.
>
> Text:
> {texto}

### P0 — controle, sem injection

> Rewrite the text below. Preserve all of the original information and meaning.
>
> Text:
> {texto}

---

## Três avisos que afetam a leitura do resultado

**P3 e P5 se sobrepõem.** O símbolo `#` e as reticências que o P5 remove também são
caracteres não alfanuméricos, que o P3 já reduz. Os efeitos dos dois não vão sair
totalmente separados. Vale registrar no artigo em vez de descobrir na análise.

**P1 e P3 puxam em direções opostas.** O P1 acrescenta pontuação final e o P3 reduz
caracteres não alfanuméricos, que incluem pontuação. No P6 o modelo vai ter que
equilibrar os dois. Se o P6 render menos que a soma dos efeitos isolados, é provavelmente
por isso.

**O controle P0 precisa dar trabalho parecido ao modelo.** Se o P0 fizer o modelo mudar
quase nada e os outros fizerem reescrever por inteiro, a diferença de BPC pode vir do
tamanho da reescrita, e não da característica. Vale conferir se os textos de P0 mudaram
em extensão parecida com os demais.

## Depois de reescrever: conferir se o injection funcionou

Antes de calcular o BPC, vale checar se cada prompt de fato mexeu na variável que ele
deveria mexer. Sem isso não dá para distinguir "a característica não afeta o BPC" de
"o prompt não mudou a característica".

`verificar_reescrita.py` faz isso: recebe os textos reescritos, recalcula as 5 variáveis
e mostra quanto cada uma andou em relação ao original, por prompt.

```bash
python verificar_reescrita.py \
  --originais   textos_para_reescrita.jsonl \
  --reescritos  reescritas_do_gustavo.jsonl \
  --saida       verificacao.md
```

A tabela esperada tem a diagonal forte: o P1 mexendo bastante na variável 1, o P2 na 2, e
assim por diante. Onde a diagonal estiver fraca, o prompt precisa ser ajustado antes de
gastar GPU com o BPC.
