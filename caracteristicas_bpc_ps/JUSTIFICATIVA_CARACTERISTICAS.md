# Justificativa das características textuais

Texto pronto para o artigo, em três tamanhos. Escolham o que couber nas 2 páginas.

---

## Versão curta — um parágrafo

> As características textuais testadas não foram escolhidas livremente, mas extraídas de
> famílias já consolidadas na literatura de complexidade textual e de seleção de dados
> para pré-treino. Foram calculadas 105 variáveis interpretáveis em sete famílias:
> legibilidade, pelas fórmulas clássicas de Flesch, Flesch-Kincaid, Gunning Fog, SMOG,
> Coleman-Liau, ARI, LIX e RIX; sofisticação lexical, no sentido de Lu (2010, 2012), como
> a proporção de palavras fora das mais frequentes da língua, medida pela frequência
> Zipf; diversidade lexical, por MTLD e HD-D, preferidas ao type-token ratio por serem
> robustas ao tamanho do texto; complexidade sintática, na linha do L2SCA; coesão
> referencial, na linha do Coh-Metrix; ortografia, por dicionário; e sinais de qualidade
> de corpus, operacionalizados a partir dos filtros heurísticos do Gopher (Rae et al.,
> 2021), do C4 (Raffel et al., 2020) e do RefinedWeb (Penedo et al., 2023), calculados
> como variáveis contínuas em vez de regras de corte. Esta última família é a definição
> operacional de qualidade efetivamente usada na construção de corpora de pré-treino, o
> que a torna o ponto de comparação natural para um método de seleção de dados como o
> PRESELECT. Variáveis que medem compressibilidade ou previsibilidade do próprio texto —
> razão de compressão e entropia — foram calculadas mas descartadas da análise final, por
> serem circulares em relação ao alvo: o BPC é, por definição, a perda de compressão do
> modelo sobre o texto, de modo que tais variáveis o explicariam por tautologia.

---

## Versão média — para a seção de metodologia

> **Seleção das características textuais.** Para evitar escolha arbitrária, partimos de
> famílias de características já estabelecidas na literatura de complexidade textual e de
> seleção de dados para pré-treino, totalizando 105 variáveis interpretáveis. (i)
> *Legibilidade*: as fórmulas clássicas de Flesch, Flesch-Kincaid, Gunning Fog, SMOG,
> Coleman-Liau, ARI, LIX e RIX, implementadas diretamente para dispensar dicionário
> fonético. (ii) *Sofisticação lexical*: a proporção de palavras fora das mais frequentes
> da língua, no sentido de Lu (2010, 2012), medida de forma contínua pela frequência Zipf
> de um corpus de referência externo. (iii) *Diversidade lexical*: MTLD e HD-D, preferidas
> ao type-token ratio por não dependerem do tamanho do texto. (iv) *Complexidade
> sintática*: orações por sentença, modificadores por substantivo e distância média de
> dependência, na linha do L2SCA. (v) *Coesão referencial*: sobreposição de substantivos
> entre sentenças vizinhas e densidade de conectivos por função, na linha do Coh-Metrix.
> (vi) *Ortografia*: taxa de palavras fora de um dicionário de 160 mil entradas. (vii)
> *Qualidade de corpus*: os sinais dos filtros heurísticos do Gopher (Rae et al., 2021),
> do C4 (Raffel et al., 2020) e do RefinedWeb (Penedo et al., 2023) — razão símbolo por
> palavra, linhas iniciadas por marcador, linhas terminadas em reticências, linhas
> terminadas em pontuação, contagem de stopwords, fração de caracteres não alfanuméricos
> e fração de caracteres em n-gramas repetidos — calculados como variáveis contínuas em
> vez de critérios de corte. Esta última família foi incluída por ser a definição
> operacional de qualidade usada na prática para construir corpora de pré-treino, o que a
> torna o ponto de comparação natural para um método de seleção de dados.
>
> **Exclusão por circularidade.** Razão de compressão e entropia de caracteres e palavras
> foram calculadas, mas removidas da análise final. O BPC é, por definição, a perda de
> compressão do modelo sobre o texto; uma variável que mede compressibilidade o explica
> por tautologia, e não por achado linguístico. A inclusão dessas variáveis elevava o R²
> de validação de 0,443 para 0,627, o que ilustra a magnitude do artefato.
>
> **Procedimento.** A amostra de 1.000 documentos foi dividida ao meio. A seleção foi
> feita exclusivamente na metade de treino: cada característica foi ajustada
> individualmente em um modelo controlado por tamanho do documento e domínio de origem, e
> ranqueada pelo valor absoluto da estatística t; mantiveram-se as de maior magnitude que
> fossem significativas e apresentassem correlação inferior a 0,6 entre si, seguidas de
> eliminação regressiva. O R² relatado foi medido na metade de validação, que não
> participou da seleção.

---

## Parágrafo sobre a escolha do alvo

Este é o que responde diretamente à pergunta do Ícaro e vale entrar no artigo, porque é
um achado, não uma decisão administrativa.

> **Escolha da variável resposta.** A força preditiva do PRESELECT é definida como a
> fração de pares de modelos em que o modelo de melhor desempenho em benchmark obtém menor
> perda de compressão. Com os seis modelos disponíveis, essa fração é calculada sobre
> apenas 15 pares e assume somente sete valores distintos na amostra, com 87% dos
> documentos concentrados em três deles. Para quantificar o efeito dessa granularidade,
> estimamos a confiabilidade da medida por divisão ao meio dos pares, com correção de
> Spearman-Brown: a força preditiva apresenta confiabilidade de 0,32, contra 0,996 do BPC
> médio dos seis modelos. Como a confiabilidade de uma medida limita superiormente a
> variância que qualquer conjunto de preditores pode explicar, o teto de R² para a força
> preditiva nesta amostra é de aproximadamente 0,32. Reportamos ambas as análises: com a
> força preditiva como alvo, o modelo atinge R² de validação de 0,052, equivalente a 16%
> do sinal disponível; com o BPC médio, atinge 0,443 de um teto de 0,996, equivalente a
> 44%. Adotamos o BPC médio como alvo principal por essa razão métrica, e não por
> conveniência de resultado. A baixa confiabilidade da força preditiva com seis modelos é
> em si uma limitação relevante para trabalhos que repliquem o PRESELECT em escala
> reduzida.

---

## Referências para a bibliografia

- Flesch, R. (1948). A new readability yardstick. *Journal of Applied Psychology*.
- Graesser, A. C., McNamara, D. S., Louwerse, M. M., & Cai, Z. (2004). Coh-Metrix:
  Analysis of text on cohesion and language. *Behavior Research Methods*.
- Lu, X. (2010). Automatic analysis of syntactic complexity in second language writing.
  *International Journal of Corpus Linguistics*.
- Lu, X. (2012). The relationship of lexical richness to the quality of ESL learners' oral
  narratives. *The Modern Language Journal*.
- McCarthy, P. M., & Jarvis, S. (2010). MTLD, vocd-D, and HD-D: A validation study of
  sophisticated approaches to lexical diversity assessment. *Behavior Research Methods*.
- Penedo, G., et al. (2023). The RefinedWeb dataset for Falcon LLM. *NeurIPS*.
- Rae, J. W., et al. (2021). Scaling language models: Methods, analysis & insights from
  training Gopher. *arXiv:2112.11446*.
- Raffel, C., et al. (2020). Exploring the limits of transfer learning with a unified
  text-to-text transformer (C4/T5). *JMLR*.
- Shum, K., et al. (2025). Predictive data selection: The data that predicts is the data
  that teaches (PRESELECT). *ICML*.

Confiram as referências antes de submeter: escrevi de memória as que não consultei
diretamente, e ano ou veículo podem estar imprecisos.
