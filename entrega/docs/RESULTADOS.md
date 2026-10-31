# Resultado observado nos seis modelos

As duas execuções estão completas e compatíveis: **1.000 documentos de 50 domínios, 6.000 BPCs,
15 pares por documento e 3.610.511 caracteres de texto**. Todos os benchmarks têm suas contagens
completas. O consolidado foi recalculado a partir dos seis ZIPs originais e validado.

## Capacidade medida

| Modelo | Média dos três benchmarks |
|---|---:|
| Pythia 160M deduped | 0,349005 |
| Pythia 410M deduped | 0,450071 |
| Pythia 1B deduped | 0,534068 |
| Pythia 1.4B deduped | 0,535888 |
| GPT-Neo 1.3B | 0,537942 |
| GPT-Neo 2.7B | 0,570316 |

GPT-Neo 2.7B tem a maior capacidade medida e o menor BPC médio da suíte (aproximadamente 0,9924).
Os números completos por benchmark e as distribuições de BPC estão em `resumo_modelos.csv`.

## Força preditiva

A média é **0,9092**, a mediana é **14/15 ≈ 0,9333** e o intervalo observado é **0,60 a 1,00**.

| Pares concordantes | Documentos | Percentual |
|---|---:|---:|
| 9/15 | 3 | 0,3% |
| 10/15 | 6 | 0,6% |
| 11/15 | 11 | 1,1% |
| 12/15 | 113 | 11,3% |
| 13/15 | 260 | 26,0% |
| 14/15 | 411 | 41,1% |
| 15/15 | 196 | 19,6% |

Portanto, 607 documentos (60,7%) concordam em pelo menos 14 dos 15 pares.
Na execução inicial, 639 concordavam em todos os seis pares disponíveis. A mudança para 196 em
todos os 15 pares resulta da ampliação das comparações; não significa que os textos mudaram.

## Onde aparecem as discordâncias

O par Pythia 1B versus Pythia 1.4B concentra 561 discordâncias em 1.000 documentos.
Apesar da capacidade medida ligeiramente maior de Pythia 1.4B, seu BPC é menor em apenas 439 textos.
Pythia 1B versus GPT-Neo 1.3B tem 360 discordâncias; Pythia 1.4B versus GPT-Neo 1.3B tem 337.
Não houve empate exato de BPC nesses pares.

Esses três modelos têm capacidades próximas. A força usa a ordem observada, sem intervalo de confiança
para essa ordem; os resultados não sustentam uma afirmação de superioridade estatística entre eles.
A correlação descritiva por postos entre comprimento do texto e força é aproximadamente 0,067,
uma associação fraca nesta amostra. Isso não testa nem demonstra causalidade.

O notebook permite ler exemplos de força máxima e mínima e comparar seus seis BPCs. A leitura não é
convertida em rótulos “bom”/“ruim”; a análise semântica e o efeito dos documentos no aprendizado
continuam abertos para a próxima etapa.
