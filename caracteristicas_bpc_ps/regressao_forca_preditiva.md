# Regressão com a força preditiva como alvo

## O alvo tem pouca variação


A força preditiva assume **apenas 7 valores distintos** nos 1.000 documentos, e 87% deles caem em três valores (13, 14 e 15 de 15 pares).


| pares concordantes (de 15) | documentos |
|---:|---:|
| 15 | 196 |
| 14 | 411 |
| 13 | 260 |
| 12 | 113 |
| 11 | 11 |
| 10 | 6 |
| 9 | 3 |

Coeficiente de variação: **0.075** para a força preditiva, contra **0.211** para o BPC médio. A força preditiva varia cerca de um terço do que o BPC varia, em termos relativos.

## O teto do R²


A força preditiva de um documento é a fração de 15 pares de modelos em que o modelo mais forte teve BPC menor. Com apenas 15 pares, vindos de 6 modelos, o valor observado carrega bastante ruído. Para medir quanto, os pares foram divididos ao meio 200 vezes e o PS de cada metade foi correlacionado com o da outra, com correção de Spearman-Brown. É a confiabilidade da medida, e ela limita o R² de qualquer conjunto de variáveis.


| medida | confiabilidade = teto do R² |
|---|---:|
| **Força preditiva** (15 pares) | **0.324** |
| BPC médio (6 modelos) | 0.996 |

Duas metades aleatórias dos pares concordam fracamente entre si: a força preditiva, medida com 6 modelos, é uma medida ruidosa. Nenhum conjunto de variáveis textuais passaria de R² ≈ 0.32 nesta amostra. O BPC médio, pelo mesmo critério, é quase perfeitamente confiável (0.996).

## O modelo


Seleção na metade de treino, depois eliminação regressiva: sobraram 5 variáveis.


| característica | β padronizado | p | direção |
|---|---:|---:|---|
| `qlt_frac_chars_numericos` | -0.155 | 0.0005 | reduzir |
| `org_urls_1000c` | -0.092 | 0.0333 | reduzir |
| `coe_conectivos_contraste_100p` | +0.134 | 0.0025 | aumentar |
| `reg_1a_pessoa_100p` | -0.201 | 0.0000 | reduzir |
| `qlt_frac_chars_top_2gram` | -0.111 | 0.0108 | reduzir |

R² no treino 0.132 · **na validação 0.052** · teto estimado 0.324


Isto é, o modelo captura cerca de **16% do sinal disponível** (0.052 de um teto de 0.324). Para comparar, com o BPC médio o modelo chega a 0,443 de um teto de 0,996, ou seja, 44% do sinal.

## Checagem com GLM binomial


A força preditiva é uma proporção sobre 15 pares, então a regressão linear é uma aproximação. O GLM binomial é a forma correta e serve de checagem:


| característica | coef. (log-odds) | p |
|---|---:|---:|
| `qlt_frac_chars_numericos` | -5.928 | 0.0037 |
| `org_urls_1000c` | -0.126 | 0.1586 |
| `coe_conectivos_contraste_100p` | +0.202 | 0.0079 |
| `reg_1a_pessoa_100p` | -0.077 | 0.0001 |
| `qlt_frac_chars_top_2gram` | -3.403 | 0.0426 |

4 de 5 variáveis mantêm a mesma conclusão de significância nos dois modelos.

## Famílias, com a força preditiva como alvo


| Família | variáveis | R² na validação |
|---|---:|---:|
| qualidade de corpus (Gopher/C4) | 14 | 0.076 |
| lexico (extrator anterior) | 11 | 0.071 |
| sintaxe (extrator anterior) | 19 | 0.052 |
| organizacao (extrator anterior) | 10 | 0.044 |
| registro (extrator anterior) | 10 | 0.034 |
| vocabulario relevante | 2 | 0.030 |
| raridade lexical | 6 | 0.018 |
| legibilidade | 8 | 0.007 |
| ortografia | 4 | 0.004 |
| coesao (extrator anterior) | 10 | -0.013 |
| sintaxe (L2SCA) | 5 | -0.014 |
| diversidade lexical | 2 | -0.042 |
| *tamanho do texto (baseline)* | 1 | 0.010 |
| *domínio do site (baseline)* | 1 | 0.079 |

## Lado a lado com o BPC


| | força preditiva | BPC médio |
|---|---|---|
| R² na validação | 0.052 | 0,443 |
| Teto (confiabilidade da medida) | 0.324 | 0.996 |
| Fração do sinal capturada | 16% | 44% |
| Variáveis selecionadas | 5 | 5 |

Variáveis em comum entre os dois alvos: `qlt_frac_chars_numericos`.


Selecionadas só pela força preditiva: `org_urls_1000c`, `coe_conectivos_contraste_100p`, `reg_1a_pessoa_100p`, `qlt_frac_chars_top_2gram`.
