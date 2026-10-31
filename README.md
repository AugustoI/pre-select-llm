# PreSelect — documentos, BPC e força preditiva

Este projeto prepara uma base de documentos para investigar **se os textos que um modelo prevê melhor também permitem distinguir modelos com maior capacidade**. É uma reprodução adaptada do método do artigo [Predictive Data Selection: The Data That Predicts Is the Data That Teaches](https://arxiv.org/abs/2503.00808), usando modelos menores.

A primeira etapa já está pronta: selecionamos os textos, calculamos o BPC de cada documento em seis modelos, avaliamos os modelos em benchmarks e reunimos tudo em uma base com força preditiva por documento. **Quem continuar o trabalho pode começar pelos dados prontos, sem rodar modelos ou alugar GPU.**

A próxima etapa prevista é a análise semântica desses textos. Ela ainda não foi feita, assim como não foi medido o efeito de selecionar esses documentos no treinamento de um novo modelo.

## Comece pelo que você quer fazer

| Quero… | Onde começar |
|---|---|
| Entender os resultados | [Resumo dos resultados](entrega/docs/RESULTADOS.md) |
| Ler textos, filtrar documentos e explorar gráficos | [Notebook de análise](entrega/notebooks/01_Explorar_Documentos_e_Resultados.ipynb) |
| Consultar a análise sem instalar Python | Baixe e abra a [versão HTML](entrega/docs/Exploracao_Resultados.html) no navegador; no GitHub ela aparece como arquivo |
| Usar textos e métricas em outro código | [JSONL completo](entrega/dados/consolidado/documentos_forca_preditiva.jsonl) |
| Abrir uma tabela no Excel ou similar | [CSV resumido, sem textos](entrega/dados/consolidado/documentos_resumo.csv) |
| Entender como cada campo foi calculado | [Metodologia e dicionário dos dados](entrega/docs/METODOLOGIA_E_DADOS.md) |
| Repetir os cálculos na GPU | Veja a seção **Executores** abaixo |
| Enviar o trabalho para outra pessoa | [ZIP da entrega completa](distribuicao/PreSelect_Entrega_6_Modelos.zip), com dados, código, notebooks e instruções |

## O que já foi construído

| Etapa concluída | O que foi produzido |
|---|---|
| Preparação da amostra | **1.000 documentos de 50 domínios**, com 20 textos por domínio, IDs, origem e hashes |
| Avaliação dos modelos | HellaSwag, ARC-Easy e BoolQ completos, em zero-shot, para os seis modelos |
| Cálculo por documento | **6.000 valores de BPC**: os mesmos 1.000 textos avaliados por cada modelo |
| Unificação | Força preditiva calculada com **15 pares de modelos por documento** |
| Exploração dos dados | Notebook executado, textos completos, filtros, tabelas, gráficos e versão HTML |
| Preparação para continuidade | Código, testes, manifestos, evidências das execuções e pacote compartilhável |

Os modelos são **Pythia 160M, 410M, 1B e 1.4B deduped**, além de **GPT-Neo 1.3B e 2.7B**. Foram executados em dois lotes, de quatro e dois modelos. A unificação usa os seis resultados e mantém os mesmos documentos.

Esta é uma **adaptação do experimento**: usamos uma amostra própria da fonte DCLM-refinedweb e uma suíte de modelos menores. Os dados não são a amostra exata nem os rótulos fornecidos pelos autores.

### Como interpretar BPC e força preditiva

**BPC, ou bits por caractere**, mede a dificuldade que um modelo teve para prever um texto. Quanto menor o BPC, melhor aquele modelo previu o documento. Cada texto tem seis BPCs, um por modelo.

**Capacidade do modelo** é a média dos seus escores nos três benchmarks. Essa capacidade determina a ordem dos modelos usada nas comparações; a ordem não é definida apenas pelo tamanho do modelo.

**Força preditiva do documento** é a fração de pares em que o modelo com maior capacidade também tem BPC menor naquele texto. Com seis modelos, temos 15 pares. Se 14 concordam, a força é `14 / 15 ≈ 0,9333`. Empates de capacidade são excluídos; empates de BPC não contam como concordância. Nesta execução, todos os 15 pares são comparáveis.

A força média observada foi **0,9092**, e **196 documentos** concordaram em todos os 15 pares. Isso mede concordância com a ordenação dos benchmarks; não atribui automaticamente rótulos semânticos de texto “bom” ou “ruim”.

## Mapa do repositório

```text
entrega/                         Material ativo para continuar a pesquisa
├── dados/
│   ├── consolidado/             Textos, seis BPCs e força preditiva calculados
│   ├── resultados_por_modelo/   Seis ZIPs originais dos cálculos na GPU
│   ├── amostras/                Textos e manifestos usados nos dois lotes
│   └── preselect_estado/        Registros de conclusão para retomada no Pod
├── notebooks/                  Análise local e os dois executores de GPU
├── src/                        Preparação, cálculo, unificação e validação
├── docs/                       Metodologia, resultados, HTML, tabelas e gráficos
├── tests/                      Testes de integridade da entrega
├── requirements.txt            Dependências da análise local
└── README.md                   Instruções da entrega independente

distribuicao/                    ZIP pronto para compartilhar
referencia_artigo/               Código original dos autores, para consulta
arquivo_local/                   Índice do histórico arquivado
```

Na máquina de desenvolvimento também existem `arquivo_local/2026-10-31/`, `.venv_analise/` e `entrega/.venv/`. **Esses conteúdos locais não são enviados ao GitHub.** A seção sobre “trash” explica o que é descartável.

## Dados: quais arquivos usar e quais preservar

Comece por [documentos_forca_preditiva.jsonl](entrega/dados/consolidado/documentos_forca_preditiva.jsonl). Cada linha contém um documento com:

- `document_id`: chave estável para cruzar os dados com análises futuras.
- `text`, `url` e `domain`: texto integral e sua origem.
- `n_chars` e `text_sha256`: tamanho do texto e hash para conferir sua integridade.
- `bpc__<modelo>`: seis colunas com os BPCs.
- `predictive_strength`, `concordant_pairs` e `comparable_pairs`: força, numerador e denominador.

O [CSV resumido](entrega/dados/consolidado/documentos_resumo.csv) mantém métricas e identificadores, mas omite o texto. [ranking_e_benchmarks.json](entrega/dados/consolidado/ranking_e_benchmarks.json) guarda os escores e metadados dos modelos.

Preserve os [ZIPs individuais](entrega/dados/resultados_por_modelo/), as [amostras e manifestos](entrega/dados/amostras/) e os [registros de conclusão](entrega/dados/preselect_estado/). Eles permitem verificar a origem dos cálculos, reconstruir o consolidado e retomar execuções.

Para acrescentar análises, use `document_id` como chave e salve as novas colunas em arquivos próprios. Mantenha os textos e resultados originais para permitir comparações futuras.

## Análise: como abrir e executar

O [notebook de análise](entrega/notebooks/01_Explorar_Documentos_e_Resultados.ipynb) já contém saídas salvas. Permite ler textos completos, filtrar por domínio ou trecho literal e comparar BPCs, capacidades e força preditiva. **Roda localmente, sem GPU e sem baixar modelos.**

Use Python 3.12, recomendado. Os comandos abaixo partem da raiz deste repositório.

### Windows — PowerShell

Na primeira instalação:

```powershell
py -3.12 -m venv entrega\.venv
.\entrega\.venv\Scripts\python.exe -m pip install -r entrega\requirements.txt
```

Para abrir, inclusive nas próximas vezes:

```powershell
.\entrega\.venv\Scripts\python.exe -m jupyter lab entrega/notebooks/01_Explorar_Documentos_e_Resultados.ipynb
```

Na máquina de desenvolvimento, esse ambiente já está criado e o kernel **Python (PreSelect - entrega)** está registrado. Em outra máquina, selecione o interpretador do ambiente que acabou de criar. O ambiente virtual não acompanha o clone ou o ZIP.

### Linux ou macOS

```bash
python3 -m venv entrega/.venv
entrega/.venv/bin/python -m pip install -r entrega/requirements.txt
entrega/.venv/bin/python -m jupyter lab entrega/notebooks/01_Explorar_Documentos_e_Resultados.ipynb
```

No Jupyter, use **Run All / Executar tudo**. Mantenha o notebook dentro da estrutura da entrega, pois ele lê `entrega/dados/`. Para apenas consultar, baixe e abra o [HTML](entrega/docs/Exploracao_Resultados.html) no navegador; os filtros editáveis ficam no notebook.

## Executores: o que rodar e em qual ambiente

### Cálculo dos modelos — GPU no Pod

| Executor | O que executa |
|---|---|
| [PreSelect_GPU_Um_Modelo_Por_Vez.ipynb](entrega/notebooks/PreSelect_GPU_Um_Modelo_Por_Vez.ipynb) | Pythia 160M, 410M e 1B; GPT-Neo 1.3B |
| [PreSelect_GPU_Mais_Dois_Modelos.ipynb](entrega/notebooks/PreSelect_GPU_Mais_Dois_Modelos.ipynb) | Pythia 1.4B; GPT-Neo 2.7B |

Cada notebook GPU é independente: contém a amostra e o código necessários. Envie somente o notebook ao Pod, abra um kernel novo e execute tudo. Ele processa os modelos em sequência, salva um ZIP por modelo e libera os pesos após validar cada resultado.

Os ZIPs ficam ao lado do notebook; o código não os transfere automaticamente para seu computador. A pasta `preselect_estado` faz a reexecução pular modelos concluídos, mesmo que seus ZIPs já tenham sido copiados e removidos. Preserve-a para retomar. Para recalcular tudo de propósito, use um workspace novo sem os registros anteriores.

As configurações de GPU, disco, retomada e versões estão no [README da entrega](entrega/README.md). **Não é necessário repetir essas execuções para trabalhar com os dados atuais.**

### Unificação e manutenção — CPU local

Estes comandos partem da raiz do repositório. Os cinco primeiros usam somente a biblioteca padrão do Python.

| Comando | Quando usar |
|---|---|
| `python entrega/src/verificar.py` | Conferir os seis resultados, textos, benchmarks e recálculo da força |
| `python entrega/src/consolidar.py` | Reconstruir `dados/consolidado/` a partir dos seis ZIPs |
| `python entrega/src/conferir_arquivos.py` | Conferir se os arquivos correspondem ao manifesto da entrega recebida |
| `python -m unittest discover -s entrega/tests -v` | Rodar os testes de integridade e compatibilidade |
| `python entrega/src/empacotar.py` | Atualizar o manifesto e gerar o ZIP compartilhável em `distribuicao/` |
| `python entrega/src/gerar_notebook_analise.py` | Recriar o notebook durante manutenção; substitui-o por uma versão sem saídas, que precisa ser executada novamente |

O gerador do notebook requer as dependências de análise. `src/preparar_amostra.py` prepara **outra amostra**, requer internet e `zstandard`; não é necessário para esta entrega. `src/core.py` contém o cálculo de BPC e benchmarks, e `src/gpu_step.py` controla a execução e retomada por modelo.

Os executores GPU têm cópias embutidas desse código: editar apenas `src/` não altera os notebooks já gerados. Mudanças no cálculo exigem atualizar os executores e identificar um novo protocolo, sem misturar resultados com os atuais.

## O que é ativo, referência e “trash”

“Trash” aqui significa material que não é necessário para executar a entrega atual. Não existe uma pasta ativa chamada `trash/`, e a reorganização preservou o histórico em vez de apagá-lo.

| Material | Classificação | Como tratar |
|---|---|---|
| `entrega/dados/`, `src/`, `notebooks/`, `docs/` e `tests/` | **Ativo** | Preservar: dados, ferramentas e evidências do trabalho atual |
| `entrega/dados/preselect_estado/` | **Estado de execução** | Preservar para retomar sem refazer modelos; não é cache descartável |
| `referencia_artigo/` | **Referência** | Código original dos autores, incluindo Megatron; não é o executor do piloto e não é lixo |
| `distribuicao/PreSelect_Entrega_6_Modelos.zip` | **Pacote gerado** | Pode ser recriado por `empacotar.py`; é a opção pronta para compartilhar |
| `arquivo_local/2026-10-31/` | **Histórico desativado, apenas local** | Protótipos, entradas antigas, caches e entrega de teste de 25 documentos; não usar como resultado atual nem incluir no envio |
| `.venv_analise/` | **Ambiente local anterior** | Pode remover se ninguém estiver usando; a análise atual usa `entrega/.venv/` |
| `entrega/.venv/` | **Ambiente local recriável** | Manter enquanto estiver usando; pode ser recriado com `requirements.txt` e não deve ser compartilhado |
| `__pycache__/`, `*.pyc` | **Cache descartável** | Pode remover; o Python recria quando necessário |
| `.ipynb_checkpoints/` | **Cópias automáticas locais** | Pode remover após salvar o notebook e confirmar que não precisa recuperar alguma versão |

O histórico contém também geradores antigos e arquivos brutos recebidos: ele não participa do fluxo atual, mas pode ser útil para auditoria. Se quiser descartá-lo definitivamente, guarde uma cópia do que pretende preservar. O [índice do arquivo local](arquivo_local/README.md) detalha seu conteúdo; no GitHub, só esse índice é versionado.

O antigo classificador fastText e a entrega de **25 documentos** pertencem a um protótipo arquivado. **A entrega válida para continuar este trabalho é a de 1.000 documentos e seis modelos em `entrega/`.**

## Para passar o trabalho adiante

Envie o [ZIP da entrega](distribuicao/PreSelect_Entrega_6_Modelos.zip) ou compartilhe este repositório. Oriente a pessoa a começar pelo notebook de análise e pela metodologia. Não é necessário enviar ambientes virtuais, caches, pesos de modelos ou o histórico local.

Para aprofundar: [instruções da entrega](entrega/README.md), [metodologia e campos](entrega/docs/METODOLOGIA_E_DADOS.md), [resultados e limitações](entrega/docs/RESULTADOS.md) e [código original do artigo](referencia_artigo/README.md).
