# PreSelect — reprodução adaptada e resultados

A entrega atual está em **[entrega/](entrega/README.md)**: 1.000 documentos, seis modelos e 6.000 BPCs,
com força preditiva recalculada sobre 15 pares por documento. As duas execuções recebidas foram
validadas e reunidas. A etapa atual não inclui análise semântica ou treinamento de classificador.

- **Para compartilhar:** `distribuicao/PreSelect_Entrega_6_Modelos.zip`.
- **Para explorar:** [notebook de documentos e resultados](entrega/notebooks/01_Explorar_Documentos_e_Resultados.ipynb).
- **Para ler sem Jupyter:** [análise em HTML](entrega/docs/Exploracao_Resultados.html).
- **Para continuar o trabalho:** [instruções da entrega](entrega/README.md) e [metodologia/dicionário](entrega/docs/METODOLOGIA_E_DADOS.md).

## Organização do repositório

| Pasta | Finalidade |
|---|---|
| `entrega/` | Pacote independente de dados, notebooks, código e documentação atuais |
| `distribuicao/` | ZIP pronto para enviar; gerado por `entrega/src/empacotar.py` |
| `referencia_artigo/` | Código original do artigo, preservado com sua estrutura interna e README |
| `arquivo_local/` | Protótipos, execuções antigas, entradas brutas e entrega de 25 documentos; fora do pacote para envio |
| `.venv_analise/` | Ambiente Python local usado para validar a análise; não distribuir |

O material antigo foi arquivado, sem apagar dados ou pesos existentes. Não é necessário enviar
`arquivo_local/`, ambientes virtuais, caches ou pesos de modelos para continuar a análise.
O registro de reorganização está em `entrega/docs/reorganizacao.json`.

Comandos a partir desta raiz:

```bash
python entrega/src/verificar.py
python -m unittest discover -s entrega/tests -v
python entrega/src/empacotar.py
```

Para executar o fluxo original do artigo, consulte `referencia_artigo/README.md` e use essa pasta
como diretório de trabalho. Para o piloto de seis modelos, use somente as instruções de `entrega/README.md`.
