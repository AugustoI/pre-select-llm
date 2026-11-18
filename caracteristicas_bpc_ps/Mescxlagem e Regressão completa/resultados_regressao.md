# Mesclagem e regressao — resultados

Base: 1000 documentos, merge por `document_id` (1000 de 1000 batendo, sem sobras).

Indice numerico `indice` 1..1000, criado aqui, ordenado por `document_id`.


Correlacao entre os dois candidatos a Y (Spearman): -0.220 — sao medidas diferentes, nao duas versoes da mesma.


## Y = -(BPC medio dos 6 modelos)


### Conjunto A (herdado da etapa anterior)

R² só as 4: **0.156** · só tamanho: 0.227 · só domínio: 0.499 · 4+tamanho+domínio: 0.652


| | característica | β padronizado | p (simples) | p (com controle) | direção |
|---|---|---:|---:|---:|---|
| X1 | `lex_frac_numeros` | -0.211 | 0.0000 | 0.0000 | reduzir |
| X2 | `lex_frac_boilerplate` | -0.303 | 0.0000 | 0.0000 | reduzir |
| X3 | `org_formulas_1000c` | -0.100 | 0.0012 | 0.0048 | reduzir |
| X4 | `coe_conectivos_contraste_100p` | -0.089 | 0.0029 | 0.0640 ⚠ | reduzir |

VIF: lex…=1.16, lex…=1.01, org…=1.11, coe…=1.05 (todos baixos, sem multicolinearidade).


### Conjunto B (selecionado para este alvo)

R² só as 4: **0.283** · só tamanho: 0.227 · só domínio: 0.499 · 4+tamanho+domínio: 0.699


| | característica | β padronizado | p (simples) | p (com controle) | direção |
|---|---|---:|---:|---:|---|
| X1 | `coe_frac_vizinhas_com_substantivo_comum` | +0.277 | 0.0000 | 0.0000 | aumentar |
| X2 | `lex_frac_pontuacao` | -0.173 | 0.0000 | 0.0000 | reduzir |
| X3 | `org_frac_linhas_curtas` | -0.270 | 0.0000 | 0.0000 | reduzir |
| X4 | `sin_frac_sentencas_com_verbo` | +0.119 | 0.0001 | 0.0001 | aumentar |

VIF: coe…=1.11, lex…=1.15, org…=1.07, sin…=1.25 (todos baixos, sem multicolinearidade).


## Y = forca preditiva (predictive strength)


### Conjunto A (herdado da etapa anterior)

R² só as 4: **0.101** · só tamanho: 0.008 · só domínio: 0.195 · 4+tamanho+domínio: 0.226


| | característica | β padronizado | p (simples) | p (com controle) | direção |
|---|---|---:|---:|---:|---|
| X1 | `lex_frac_numeros` | -0.130 | 0.0001 | 0.0189 | reduzir |
| X2 | `lex_frac_boilerplate` | -0.213 | 0.0000 | 0.0076 | reduzir |
| X3 | `org_formulas_1000c` | -0.118 | 0.0002 | 0.3548 ⚠ | reduzir |
| X4 | `coe_conectivos_contraste_100p` | +0.098 | 0.0015 | 0.0009 | aumentar |

VIF: lex…=1.16, lex…=1.01, org…=1.11, coe…=1.05 (todos baixos, sem multicolinearidade).


### Conjunto B (selecionado para este alvo)

R² só as 4: **0.063** · só tamanho: 0.008 · só domínio: 0.195 · 4+tamanho+domínio: 0.217


| | característica | β padronizado | p (simples) | p (com controle) | direção |
|---|---|---:|---:|---:|---|
| X1 | `coe_frac_vizinhas_com_substantivo_comum` | +0.032 | 0.3258 | 0.6511 ⚠ | aumentar |
| X2 | `lex_frac_pontuacao` | -0.157 | 0.0000 | 0.0001 | reduzir |
| X3 | `org_frac_linhas_curtas` | -0.182 | 0.0000 | 0.1645 ⚠ | reduzir |
| X4 | `sin_frac_sentencas_com_verbo` | -0.038 | 0.2694 | 0.3262 ⚠ | reduzir |

VIF: coe…=1.11, lex…=1.15, org…=1.07, sin…=1.25 (todos baixos, sem multicolinearidade).


## Leitura

- `direção` diz o que a reescrita deve fazer com a característica: como os dois Y são "maior = melhor", coeficiente negativo significa que mais daquilo piora o texto.

- ⚠ marca característica que **não** sobrevive ao controle de tamanho e domínio.

- O domínio sozinho explica mais que as quatro características juntas. Por isso a comparação da etapa 3 tem que ser pareada: o mesmo texto, com e sem injection.
