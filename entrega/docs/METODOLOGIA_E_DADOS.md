# Metodologia e dicionário dos dados

## Escopo

Foram processados os mesmos 1.000 documentos de 50 domínios (20 por domínio) por seis modelos.
Não são os documentos exatos amostrados pelos autores. A fonte é o DCLM-refinedweb público enumerado
no código original, não a amostra FineWeb usada em um protótipo anterior, arquivado fora desta entrega.

A preparação percorreu até 50.000 linhas de cada um de quatro shards selecionados com semente 42,
contou domínios e amostrou textos em uma segunda passagem. Os URLs, ETags, parâmetros e hashes estão
nos manifestos. A seleção de domínios frequentes e o mesmo número de documentos por domínio
limitam a representatividade; este conjunto não é uma amostra aleatória uniforme de toda a web.

## BPC

`BPC = soma das perdas de log-verossimilhança negativa / (n_chars × ln(2))`.
`n_chars` conta caracteres Unicode do texto Python, não bytes UTF-8. Cada documento é independente;
o token inicial é BOS ou EOS do tokenizer. São usadas janelas de contexto 1024 e passo 512,
sem truncar o documento, e cada token do texto é alvo exatamente uma vez.
Os modelos rodam em BF16, com entropia cruzada em float32 e acumulação em float64.
O código exato está em `src/core.py`, com SHA256 registrado no protocolo.

## Capacidade e força preditiva

Capacidade = média aritmética de HellaSwag `acc_norm` (10.042 exemplos), ARC-Easy `acc_norm`
(2.376 exemplos) e BoolQ `acc` (3.270 exemplos). Avaliação completa, zero-shot, `lm_eval==0.4.9.2`.
As sementes e configurações estão nos relatórios individuais. A GPU informada nas seis execuções
é uma RTX 4090. As revisões exatas de modelos e versões de pacotes estão nos metadados dos ZIPs.

Para cada documento, ordenam-se os modelos por capacidade. Um par é concordante se o modelo
de maior capacidade tem BPC estritamente menor. A força é `concordant_pairs / comparable_pairs`.
Os seis escores de capacidade são distintos: há 15 pares comparáveis. Empate de BPC não conta como
concordância; eventual empate de capacidade seria excluído do denominador e informado.

Os primeiros quatro resultados tinham seis pares; acrescentar dois modelos introduz nove pares.
A nova força não é a média de forças de execuções separadas: é recalculada a partir dos seis BPCs.
Não existem rótulos de qualidade fornecidos pelos autores nesta entrega.

## Campos do JSONL consolidado

| Campo | Significado |
|---|---|
| `document_id` | Chave estável, derivada do shard e da linha de origem; usar em cruzamentos |
| `original_id` | ID fornecido pela fonte, quando disponível; pode ser nulo |
| `text` | Texto integral usado no cálculo, sem mudanças posteriores |
| `url`, `domain` | URL e domínio do documento |
| `source_url`, `source_line` | Shard e número de linha da origem |
| `text_sha256` | SHA256 dos bytes UTF-8 de `text` |
| `n_chars` | Número de caracteres Unicode |
| `bpc__<modelo>` | BPC calculado pelo modelo identificado no nome da coluna |
| `predictive_strength` | Fração dos pares concordantes, de 0 a 1 |
| `concordant_pairs` | Numerador da força |
| `comparable_pairs` | Denominador da força; 15 em todos os documentos desta entrega |
| `benchmark_tied_pairs` | Pares excluídos por empate de capacidade; zero nesta entrega |

JSONL é UTF-8, com um objeto por linha. Para ler com Python, itere o arquivo ou use
`read_bytes().splitlines()`; evite `str.splitlines()` sobre o arquivo inteiro porque alguns textos
contêm separadores Unicode que são conteúdo, não delimitadores de registros.
O CSV omite `text`, mantém os demais campos e usa UTF-8 com BOM para facilitar a leitura no Excel.

## Proveniência e validação

Os dois lotes têm IDs de amostra diferentes porque o manifesto inclui a lista de modelos.
Os hashes dos documentos e do protocolo são idênticos. O unificador valida cada ZIP contra seu
manifesto de origem, exige versões compatíveis e mantém os metadados originais.
`manifestos_execucoes.json` guarda ambos os manifestos; `sample.json` descreve a união.

`docs/origem_arquivos.json` registra os nomes dos ZIPs de entrada antes da organização, seus membros
e os hashes dos arquivos importados. `docs/verificacao.json` registra os testes sobre os seis resultados.
No repositório completo, os ZIPs recebidos foram preservados em `arquivo_local/2026-10-31/`.
`MANIFESTO_SHA256.json`, na raiz da entrega, permite conferir todos os arquivos distribuídos.

## Limitações

- A amostra é pequena e contém 20 documentos por domínio, com seleção prévia de domínios frequentes.
- Modelos menores e fontes de pré-treinamento próprias podem alterar a ordenação e a sobreposição com os textos.
- As capacidades de Pythia 1B, Pythia 1.4B e GPT-Neo 1.3B são próximas; não foi estimada a incerteza de sua ordem.
- BF16 e diferenças de plataforma podem afetar a reprodução numérica; os resultados originais foram preservados.
- A força mede concordância com benchmarks, não qualidade semântica ou benefício causal no treinamento.
- Não houve treino de novo classificador, comparação semântica ou reprodução do experimento de pré-treinamento dos autores nesta etapa.
