# Auditoria de circularidade

O BPC é a perda de compressão do modelo sobre o texto. Variáveis que são elas mesmas medidas de compressibilidade explicam o BPC por tautologia.


## Efeito de remover as variáveis circulares


| Conjunto candidato | nº de variáveis | R² na validação |
|---|---:|---:|
| Com tudo (versao anterior, CIRCULAR) | 105 | 0.627 |
| Sem a camada 1 (compressao e entropia) | 101 | 0.445 |
| Sem as camadas 1 e 2 (tambem sem repeticao) | 96 | 0.445 |

## Modelo: Sem a camada 1 (compressao e entropia)


| característica | β padronizado | p | direção |
|---|---:|---:|---|
| `qlt_frac_chars_nao_alfanum` | -0.207 | 0.0000 | reduzir |
| `qlt_frac_chars_numericos` | -0.050 | 0.2696 | reduzir |
| `rar_zipf_desvio` | -0.213 | 0.0000 | reduzir |
| `qlt_frac_linhas_pontuacao_final` | +0.329 | 0.0000 | aumentar |
| `coe_frac_vizinhas_com_substantivo_comum` | +0.238 | 0.0000 | aumentar |
| `sin_pos_propn` | +0.011 | 0.7757 | aumentar |
| `sin_dist_dependencia_media` | +0.028 | 0.4709 | aumentar |
| `qlt_razao_simbolo_palavra` | -0.122 | 0.0004 | reduzir |

R² no treino 0.479 · **na validação 0.445** · com tamanho e domínio junto 0.702


As 12 mais fortes individualmente neste conjunto:


| característica | \|t\| |
|---|---:|
| `qlt_frac_chars_nao_alfanum` | 11.06 |
| `qlt_frac_chars_numericos` | 8.29 |
| `rar_zipf_desvio` | 7.21 |
| `rar_frac_raras` | 7.02 |
| `qlt_frac_linhas_pontuacao_final` | 6.91 |
| `rar_zipf_p10` | 6.90 |
| `coe_frac_vizinhas_com_substantivo_comum` | 6.42 |
| `rar_frac_muito_raras` | 6.27 |
| `lex_frac_pontuacao` | 6.18 |
| `lex_frac_numeros` | 6.03 |
| `rar_zipf_medio` | 5.94 |
| `coe_sobreposicao_vizinhas` | 5.85 |

## Modelo: Sem as camadas 1 e 2 (tambem sem repeticao)


| característica | β padronizado | p | direção |
|---|---:|---:|---|
| `qlt_frac_chars_nao_alfanum` | -0.207 | 0.0000 | reduzir |
| `qlt_frac_chars_numericos` | -0.050 | 0.2696 | reduzir |
| `rar_zipf_desvio` | -0.213 | 0.0000 | reduzir |
| `qlt_frac_linhas_pontuacao_final` | +0.329 | 0.0000 | aumentar |
| `coe_frac_vizinhas_com_substantivo_comum` | +0.238 | 0.0000 | aumentar |
| `sin_pos_propn` | +0.011 | 0.7757 | aumentar |
| `sin_dist_dependencia_media` | +0.028 | 0.4709 | aumentar |
| `qlt_razao_simbolo_palavra` | -0.122 | 0.0004 | reduzir |

R² no treino 0.479 · **na validação 0.445** · com tamanho e domínio junto 0.702


As 12 mais fortes individualmente neste conjunto:


| característica | \|t\| |
|---|---:|
| `qlt_frac_chars_nao_alfanum` | 11.06 |
| `qlt_frac_chars_numericos` | 8.29 |
| `rar_zipf_desvio` | 7.21 |
| `rar_frac_raras` | 7.02 |
| `qlt_frac_linhas_pontuacao_final` | 6.91 |
| `rar_zipf_p10` | 6.90 |
| `coe_frac_vizinhas_com_substantivo_comum` | 6.42 |
| `rar_frac_muito_raras` | 6.27 |
| `lex_frac_pontuacao` | 6.18 |
| `lex_frac_numeros` | 6.03 |
| `rar_zipf_medio` | 5.94 |
| `coe_sobreposicao_vizinhas` | 5.85 |

## Famílias, já sem as variáveis circulares


| Família | variáveis | R² na validação |
|---|---:|---:|
| qualidade de corpus (Gopher/C4) | 14 | 0.543 |
| lexico (extrator anterior) | 11 | 0.452 |
| sintaxe (extrator anterior) | 19 | 0.335 |
| legibilidade | 8 | 0.254 |
| registro (extrator anterior) | 10 | 0.238 |
| raridade lexical | 6 | 0.217 |
| organizacao (extrator anterior) | 10 | 0.173 |
| diversidade lexical | 2 | 0.160 |
| coesao (extrator anterior) | 10 | 0.143 |
| ortografia | 4 | 0.130 |
| sintaxe (L2SCA) | 5 | 0.102 |
| vocabulario relevante | 2 | 0.052 |
| *tamanho do texto (baseline)* | 1 | 0.218 |
| *domínio do site (baseline)* | 1 | 0.409 |
---

## Modelo final, depois da eliminação regressiva

O modelo de 8 variáveis acima ficou com três não significativas, porque a seleção
ranqueia cada variável sozinha e não reavalia o conjunto. Retirando-as uma a uma
(`sin_pos_propn` p=0,78, depois `sin_dist_dependencia_media` p=0,44, depois
`qlt_frac_chars_numericos` p=0,35), sobra um modelo de 5 variáveis, todas com
p < 0,001 e praticamente o mesmo poder explicativo:

| característica | família | β padronizado | p | direção |
|---|---|---:|---:|---|
| `qlt_frac_linhas_pontuacao_final` | qualidade | +0,334 | <0,001 | aumentar |
| `coe_frac_vizinhas_com_substantivo_comum` | coesão | +0,240 | <0,001 | aumentar |
| `qlt_frac_chars_nao_alfanum` | qualidade | −0,220 | <0,001 | reduzir |
| `rar_zipf_desvio` | raridade | −0,214 | <0,001 | reduzir |
| `qlt_razao_simbolo_palavra` | qualidade | −0,120 | <0,001 | reduzir |

R² no treino 0,477 · **na validação 0,443** · com tamanho e domínio junto 0,692.

As cinco são acionáveis num prompt de reescrita, ao contrário da compressão.

## Onde isso deixa o argumento do artigo

| | R² na validação |
|---|---:|
| Família de qualidade de corpus inteira (14 variáveis) | **0,543** |
| *Domínio do site (baseline)* | *0,409* |
| Modelo final interpretável (5 variáveis) | 0,443 |
| *Tamanho do texto (baseline)* | *0,218* |

Com a compressão fora, a afirmação "as características superam o domínio" fica
mais modesta mas continua de pé: a família de qualidade de corpus chega a 0,543
contra 0,409 do domínio, e o modelo pequeno de 5 variáveis fica em 0,443, pouco
acima do domínio.

Os dois são complementares, não concorrentes: juntos chegam a 0,692.

**A comparação pareada na etapa 3 continua obrigatória**, e agora por necessidade,
não só por rigor: o domínio explica quase tanto quanto as características.
