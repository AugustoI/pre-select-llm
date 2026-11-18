# Características textuais e regressão sobre o BPC

Etapa 2 do artigo *Identifying causal effect on PRESELECT*. Recebe os 1.000 documentos
com BPC calculado pelo Augusto, calcula características linguísticas interpretáveis e
identifica quais delas explicam o BPC.

**Resultado principal: R² = 0,443, medido fora da amostra, com 5 variáveis.**

> **Correção importante (13/11).** A versão anterior relatava R² = 0,627, mas incluía
> razão de compressão gzip e entropia como variáveis explicativas. Isso é circular: o
> BPC *é* a perda de compressão do modelo sobre o texto, então essas variáveis o
> explicam por tautologia, não por achado. Foram removidas. Ver
> `auditoria_circularidade.md`.

---

## Como rodar

A partir do clone do repositório do Augusto, com esta pasta na raiz:

```bash
pip install spacy pandas statsmodels scikit-learn wordfreq lexicalrichness pyspellchecker
python -m spacy download en_core_web_sm

# 1. as 40 características das famílias da literatura   (~50s)
python extrair_caracteristicas_literatura.py \
  --entrada entrega/dados/consolidado/documentos_forca_preditiva.jsonl \
  --saida   caracteristicas_literatura.csv --processos 4

# 2. as 6 de ortografia e vocabulário                   (~10s)
python extrair_ortografia.py \
  --entrada entrega/dados/consolidado/documentos_forca_preditiva.jsonl \
  --saida   caracteristicas_ortografia.csv

# 3. mesclagem, seleção, validação e relatório          (~1min)
python regressao_literatura.py
```

Tudo em CPU, sem GPU. Semente fixa em 42: rodar de novo dá os mesmos números.

## Arquivos

| Arquivo | O que é |
|---|---|
| `base_mesclada_completa.csv` | 1.000 linhas, 105 características, sem o texto. É a base que o grupo deve usar |
| `auditoria_circularidade.md` | **A auditoria e o modelo final.** Comece por aqui |
| `resultados_regressao_literatura.md` | Relatório da versão anterior, com a compressão ainda dentro |
| `extrair_caracteristicas_literatura.py` | As 40 características novas. O cabeçalho traz a referência de cada família |
| `extrair_ortografia.py` | As 6 de ortografia e vocabulário |
| `regressao_literatura.py` | Mesclagem, seleção e validação |
| `caracteristicas_literatura.csv` | Saída do passo 1 |
| `caracteristicas_ortografia.csv` | Saída do passo 2 |

A coluna `indice` vai de 1 a 1000, ordenada por `document_id`. **Os textos reescritos
precisam preservar esse índice**, senão a comparação da etapa 4 não fecha.

## O método, em cinco passos

1. **Mesclagem** — junta BPCs, domínio e características pelo `document_id`, com
   `validate="one_to_one"`, que falha se houver índice duplicado ou faltando.
   Bateu 1000 de 1000, sem sobras.
2. **Alvo** — `Y = −(média dos 6 BPCs)`, invertido para que maior signifique melhor.
3. **Divisão** — 500 documentos para treino e 500 para validação, semente 42.
4. **Seleção** — somente no treino. Cada característica entra sozinha em
   `Y ~ característica + log(tamanho) + domínio`; guarda-se o |t|, ordena-se, e ficam as
   8 maiores que sejam significativas e com correlação abaixo de 0,6 entre si.
5. **Validação** — o modelo com essas 8 é ajustado no treino e o R² é medido na metade
   de validação, que não participou da seleção. Por isso o número não está inflado.

## As famílias de características e de onde vêm

| Família | Origem |
|---|---|
| Legibilidade | Flesch (1948), Flesch-Kincaid, Gunning Fog, SMOG, Coleman-Liau, ARI, LIX, RIX |
| Raridade lexical | Sofisticação lexical de Lu (2010, 2012): palavras fora das mais frequentes da língua, via frequência Zipf |
| Diversidade lexical | MTLD (McCarthy, 2005) e HD-D, robustas ao tamanho do texto |
| Qualidade de corpus | Sinais do Gopher (Rae et al., 2021), C4 (Raffel et al., 2020) e RefinedWeb (Penedo et al., 2023), como variáveis contínuas em vez de regras de corte |
| Sintaxe | Na linha do L2SCA de Lu |
| Ortografia | Dicionário offline de 160 mil palavras |

## Resultados

### Qual família explica o BPC

R² medido na metade de validação, cada família sozinha:

| Família | variáveis | R² |
|---|---:|---:|
| Qualidade de corpus (Gopher/C4) | 14 | **0,543** |
| Léxico | 11 | 0,452 |
| *Domínio do site (baseline)* | 1 | *0,409* |
| Sintaxe | 19 | 0,335 |
| Legibilidade | 8 | 0,254 |
| Registro | 10 | 0,238 |
| *Tamanho do texto (baseline)* | 1 | *0,218* |
| Raridade lexical | 6 | 0,217 |
| Organização | 10 | 0,173 |
| Diversidade lexical | 2 | 0,160 |
| Coesão | 10 | 0,143 |
| Ortografia | 4 | 0,130 |
| Sintaxe (L2SCA) | 5 | 0,102 |
| Vocabulário relevante | 2 | 0,052 |

O que importa para o artigo:

**A família de qualidade de corpus (0,543) supera o domínio do site (0,409).** Esse era
o confundidor que enfraquecia a análise anterior. A vantagem é menor do que a versão
circular sugeria, mas é real.

**Os dois são complementares, não concorrentes:** juntos chegam a 0,692. Por isso a
comparação da etapa 3 tem que ser pareada, o mesmo texto com e sem injection.

### As 5 variáveis do modelo final

Todas com p < 0,001, depois de eliminação regressiva.

| característica | família | β padronizado | direção |
|---|---|---:|---|
| `qlt_frac_linhas_pontuacao_final` | qualidade | +0,334 | aumentar |
| `coe_frac_vizinhas_com_substantivo_comum` | coesão | +0,240 | aumentar |
| `qlt_frac_chars_nao_alfanum` | qualidade | −0,220 | reduzir |
| `rar_zipf_desvio` | raridade | −0,214 | reduzir |
| `qlt_razao_simbolo_palavra` | qualidade | −0,120 | reduzir |

R² no treino 0,477 · **na validação 0,443** · com tamanho e domínio junto 0,692.

As cinco são acionáveis num prompt de reescrita.

### Teste dos erros ortográficos

`ort_frac_erros` é a 4ª variável mais forte **individualmente** (|t| = 9,17), mas não
acrescenta nada ao modelo conjunto. A causa é redundância com a raridade lexical — a
correlação com `rar_zipf_p10` é −0,734. Para o `wordfreq`, uma palavra escrita errada é
simplesmente uma palavra rara. Mantido o modelo sem ela, por parcimônia.

### Com Y = força preditiva, nada funciona

O mesmo procedimento aplicado à força preditiva dá **R² de 0,048 na validação**. A melhor
família sozinha chega a 0,076 e o próprio domínio do site só alcança 0,079.

As características textuais explicam bem o BPC e praticamente não explicam a força
preditiva. Isso aponta o BPC médio como alvo da reescrita.

## Tradução para o prompt de injection

Se o grupo aprovar as 5 variáveis, elas viram mais ou menos isto:

> Reescreva o texto como prosa contínua. Termine cada frase com pontuação e encadeie as
> frases retomando substantivos entre frases vizinhas. Mantenha o vocabulário uniforme em
> registro, sem alternar entre palavras muito comuns e muito raras. Evite símbolos,
> pontuação solta e caracteres não alfanuméricos.

## Ressalvas, para constar no artigo

- Compressão e entropia foram removidas por circularidade (ver
  `auditoria_circularidade.md`). Nenhuma das 5 restantes tem esse problema: a raridade
  lexical, por exemplo, mede o vocabulário contra um corpus externo, e não contra as
  estatísticas do próprio texto.
- O domínio do site explica quase tanto quanto as características (0,409 contra 0,443),
  então a comparação pareada da etapa 3 é obrigatória, não opcional.
- O dicionário ortográfico é de inglês americano, então grafias britânicas contam como
  erro. Para comparar documentos entre si é um viés constante, mas `ort_frac_erros` não
  serve como medida absoluta de qualidade.
- O modelo final deixa mais da metade da variação do BPC sem explicação.
- A comparação da etapa 3 continua tendo que ser pareada, o mesmo texto com e sem
  injection.

## Decisões pendentes do grupo

1. Confirmar que o alvo é o **BPC médio**, não a força preditiva.
2. Aprovar as 5 variáveis do modelo final.
3. Confirmar o índice de 1 a 1000, que precisa ser preservado nos textos reescritos.
