# PreSelect — entrega dos seis modelos

Esta é a entrega atual: **1.000 documentos, 50 domínios, seis modelos, 6.000 BPCs e 15 pares por documento**.
Os dois resultados da última execução foram reunidos aos quatro anteriores. Os textos são os mesmos;
a força preditiva foi recalculada com todos os seis modelos. Não há análise semântica ou treinamento de classificador nesta entrega.

## Comece aqui

- Para ler sem instalar nada, abra `docs/Exploracao_Resultados.html` no navegador.
- Para explorar, abra `notebooks/01_Explorar_Documentos_e_Resultados.ipynb` no Jupyter.
  Ele já vem executado, mostra textos completos e permite filtrar por domínio, trecho literal e força.
- Para usar os dados em outra pesquisa, comece por `dados/consolidado/documentos_forca_preditiva.jsonl`.
  Cada linha contém o texto, o ID, a origem, seis BPCs e a força. O CSV ao lado omite o texto.

**Mantenha a estrutura de pastas ao compartilhar.** O notebook de análise precisa da pasta `dados/`;
os dois notebooks de execução GPU são independentes e podem ser enviados sozinhos ao Pod.

## Rodar a análise localmente

Python 3.10 ou superior, recomendado 3.12. Na pasta desta entrega:

```bash
python -m venv .venv
```

No Windows:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m jupyter lab notebooks/01_Explorar_Documentos_e_Resultados.ipynb
```

No Linux/macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m jupyter lab notebooks/01_Explorar_Documentos_e_Resultados.ipynb
```

Use **Run All / Executar tudo**. Não baixa corpus ou modelos e não precisa de GPU.
As versões usadas para validar esta entrega estão em `docs/ambiente_analise.txt`.

## Organização

| Pasta | Conteúdo |
|---|---|
| `notebooks/` | Análise simples e os dois notebooks GPU usados nas execuções |
| `dados/consolidado/` | Textos completos, BPCs, força, CSV e manifestos |
| `dados/resultados_por_modelo/` | Os seis ZIPs individuais originais, sem alteração |
| `dados/amostras/` | Amostras com textos idênticos e manifestos dos lotes de quatro e dois modelos |
| `dados/preselect_estado/` | Registros de conclusão do Pod, preservados para retomada |
| `src/` | Código de BPC, preparação, execução, validação, unificação e geração da análise |
| `docs/` | Metodologia, dicionário, relatório, tabelas, gráficos, proveniência e verificação |
| `tests/` | Testes de integridade da entrega e compatibilidade dos notebooks |

## Verificar ou reconstruir o consolidado

Estes comandos usam somente a biblioteca padrão do Python e funcionam sem instalar as dependências de análise:

```bash
python src/verificar.py
python src/consolidar.py
python -m unittest discover -s tests -v
python src/conferir_arquivos.py
```

`verificar.py` compara os ZIPs com seus registros e recalcula os resultados para conferir o JSONL entregue.
`consolidar.py` regrava apenas os arquivos derivados em `dados/consolidado/` e o relatório de verificação.
Os seis ZIPs individuais são as evidências de origem.
`conferir_arquivos.py` confere os hashes da entrega recebida; alterações ou novas saídas depois de
reexecutar notebooks podem mudar esses hashes. Use `src/empacotar.py` para gerar uma nova versão do pacote.

## Repetir o cálculo com GPU

`PreSelect_GPU_Um_Modelo_Por_Vez.ipynb` calcula os quatro modelos iniciais;
`PreSelect_GPU_Mais_Dois_Modelos.ipynb` calcula os dois adicionais. Os nomes e conteúdos foram preservados.
Cada notebook contém a amostra e o código, executa tudo em sequência, salva ZIPs e remove os pesos após validar cada resultado.
Use kernel novo, Python 3.10–3.12, PyTorch >= 2.6, GPU CUDA com BF16; para os dois adicionais,
recomendam-se GPU de 24 GB, RAM de 32 GB e 20 GB livres em `/tmp`.

Para retomar uma execução, copie `dados/preselect_estado/` para uma pasta chamada `preselect_estado/`
ao lado do notebook no Pod. Os registros farão os modelos concluídos serem pulados mesmo sem seus ZIPs.
Para medir tudo novamente de propósito, use um workspace novo sem esses registros.
Os notebooks têm cópias embutidas de `core.py`, `bundles.py` e `gpu_step.py`, conferidas pelos testes;
editar apenas os arquivos de `src/` não altera o código já embutido nos notebooks.
Qualquer mudança no cálculo exige novo protocolo e nova identificação, sem misturar resultados antigos.

Para preparar uma nova amostra, `src/preparar_amostra.py` requer adicionalmente `zstandard==0.25.0`
e acesso à internet. **Não execute isso para continuar esta análise**: a amostra original já está incluída.

## Continuar a pesquisa

Leia `docs/METODOLOGIA_E_DADOS.md` e `docs/RESULTADOS.md`. Use `document_id` como chave para adicionar
análises futuras e preserve os textos e hashes originais. A amostra e os modelos são uma adaptação
do artigo, não seus rótulos ou sua suíte original. A análise semântica e a avaliação de efeito no
treinamento de novos modelos permanecem etapas posteriores.

Referência: [Predictive Data Selection: The Data That Predicts Is the Data That Teaches](https://arxiv.org/abs/2503.00808).
Código de origem: [hkust-nlp/PreSelect](https://github.com/hkust-nlp/PreSelect), commit local
`258c632b831e178459441518ec47adf831d70b0b`. O código original do artigo foi preservado separadamente
em `referencia_artigo/` no repositório completo. Esta entrega contém o fluxo adaptado usado no piloto.
