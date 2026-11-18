# Regressão com as características da literatura

Base: 1000 documentos, **105 características** (61 do extrator anterior + 40 das famílias usadas na literatura).

Desenho: a amostra é dividida ao meio (semente 42). A seleção das variáveis usa **somente a metade de treino**; o R² relatado é medido na metade de validação, que não participou da seleção.


## Y = −(BPC médio dos 6 modelos)


### Qual família explica o alvo

R² medido na metade de validação, cada família sozinha.


| Família | nº de variáveis | R² fora da amostra |
|---|---:|---:|
| qualidade de corpus (Gopher/C4) | 14 | 0.543 |
| compressao/informacao | 4 | 0.494 |
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

### As 8 variáveis selecionadas (no treino) e validadas


| característica | família | β padronizado | p | direção |
|---|---|---:|---:|---|
| `inf_razao_gzip` | compressao/informacao | -0.519 | 0.0000 | reduzir |
| `inf_entropia_char` | compressao/informacao | -0.074 | 0.0450 | reduzir |
| `rar_zipf_desvio` | raridade lexical | -0.253 | 0.0000 | reduzir |
| `qlt_frac_linhas_pontuacao_final` | qualidade de corpus (Gopher/C4) | +0.137 | 0.0000 | aumentar |
| `coe_frac_vizinhas_com_substantivo_comum` | coesao (extrator anterior) | +0.175 | 0.0000 | aumentar |
| `lex_frac_pontuacao` | lexico (extrator anterior) | -0.090 | 0.0061 | reduzir |
| `sin_dist_dependencia_media` | sintaxe (extrator anterior) | -0.042 | 0.1609 | reduzir |
| `qlt_razao_simbolo_palavra` | qualidade de corpus (Gopher/C4) | -0.149 | 0.0000 | reduzir |

R² no treino: 0.682 · **R² na validação: 0.627** · com tamanho e domínio junto: 0.759


<details><summary>As 15 variáveis mais fortes individualmente (|t| controlando tamanho e domínio, no treino)</summary>


| característica | \|t\| | p |
|---|---:|---:|
| `inf_razao_gzip` | 13.14 | 0.0000 |
| `inf_entropia_char` | 11.37 | 0.0000 |
| `qlt_frac_chars_nao_alfanum` | 11.06 | 0.0000 |
| `qlt_frac_chars_numericos` | 8.29 | 0.0000 |
| `rar_zipf_desvio` | 7.21 | 0.0000 |
| `rar_frac_raras` | 7.02 | 0.0000 |
| `qlt_frac_linhas_pontuacao_final` | 6.91 | 0.0000 |
| `rar_zipf_p10` | 6.90 | 0.0000 |
| `coe_frac_vizinhas_com_substantivo_comum` | 6.42 | 0.0000 |
| `rar_frac_muito_raras` | 6.27 | 0.0000 |
| `lex_frac_pontuacao` | 6.18 | 0.0000 |
| `lex_frac_numeros` | 6.03 | 0.0000 |
| `rar_zipf_medio` | 5.94 | 0.0000 |
| `coe_sobreposicao_vizinhas` | 5.85 | 0.0000 |
| `sin_pos_propn` | 5.82 | 0.0000 |

</details>


### Teste da família de ortografia

`ort_frac_erros` está entre as variáveis mais fortes **individualmente** (|t| = 9.17), mas não acrescenta nada ao modelo conjunto:


| Modelo | R² na validação |
|---|---:|
| A: as 8 selecionadas (sem ortografia) | 0.627 |
| B: 8 deixando a ortografia concorrer | 0.584 |
| C: as 8 de A mais `ort_frac_erros` | 0.627 |

A causa é redundância com a raridade lexical:


| | correlação com `ort_frac_erros` |
|---|---:|
| `rar_zipf_p10` | -0.734 |
| `rar_frac_raras` | +0.719 |
| `rar_zipf_desvio` | +0.666 |
| `rar_frac_desconhecidas` | +0.590 |

Para o `wordfreq`, uma palavra escrita errada é simplesmente uma palavra rara, então as medidas de raridade já capturavam o fenômeno. No modelo C o coeficiente da ortografia ainda troca de sinal, sinal clássico de colinearidade. Por isso o modelo reportado acima é o A.


## Y = força preditiva


### Qual família explica o alvo

R² medido na metade de validação, cada família sozinha.


| Família | nº de variáveis | R² fora da amostra |
|---|---:|---:|
| qualidade de corpus (Gopher/C4) | 14 | 0.076 |
| lexico (extrator anterior) | 11 | 0.071 |
| sintaxe (extrator anterior) | 19 | 0.052 |
| organizacao (extrator anterior) | 10 | 0.044 |
| compressao/informacao | 4 | 0.037 |
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

### As 8 variáveis selecionadas (no treino) e validadas


| característica | família | β padronizado | p | direção |
|---|---|---:|---:|---|
| `qlt_frac_chars_numericos` | qualidade de corpus (Gopher/C4) | -0.129 | 0.0133 | reduzir |
| `qlt_frac_chars_nao_alfanum` | qualidade de corpus (Gopher/C4) | -0.076 | 0.1537 | reduzir |
| `org_urls_1000c` | organizacao (extrator anterior) | -0.073 | 0.1053 | reduzir |
| `coe_conectivos_contraste_100p` | coesao (extrator anterior) | +0.144 | 0.0013 | aumentar |
| `reg_1a_pessoa_100p` | registro (extrator anterior) | -0.183 | 0.0001 | reduzir |
| `qlt_frac_chars_top_2gram` | qualidade de corpus (Gopher/C4) | -0.113 | 0.0111 | reduzir |
| `org_chars_por_linha` | organizacao (extrator anterior) | -0.058 | 0.1817 | reduzir |
| `sin_desvio_tam_sentenca` | sintaxe (extrator anterior) | +0.033 | 0.4559 | aumentar |

R² no treino: 0.139 · **R² na validação: 0.048** · com tamanho e domínio junto: 0.052


<details><summary>As 15 variáveis mais fortes individualmente (|t| controlando tamanho e domínio, no treino)</summary>


| característica | \|t\| | p |
|---|---:|---:|
| `qlt_frac_chars_numericos` | 3.82 | 0.0002 |
| `qlt_frac_chars_nao_alfanum` | 3.81 | 0.0002 |
| `inf_entropia_char` | 3.43 | 0.0007 |
| `org_urls_1000c` | 3.26 | 0.0012 |
| `lex_frac_numeros` | 3.11 | 0.0020 |
| `coe_conectivos_contraste_100p` | 2.87 | 0.0043 |
| `coe_conectivos_total_100p` | 2.70 | 0.0073 |
| `reg_1a_pessoa_100p` | 2.69 | 0.0075 |
| `qlt_frac_chars_top_2gram` | 2.58 | 0.0101 |
| `org_chars_por_linha` | 2.52 | 0.0119 |
| `sin_desvio_tam_sentenca` | 2.43 | 0.0155 |
| `reg_entidades_100p` | 2.35 | 0.0192 |
| `coe_conectivos_causal_100p` | 2.33 | 0.0202 |
| `qlt_razao_simbolo_palavra` | 2.29 | 0.0227 |
| `reg_frac_entidades_data_numero` | 2.19 | 0.0287 |

</details>
