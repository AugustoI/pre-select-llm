"""Generate the small CPU-only analysis notebook. Execute separately to save outputs."""
from pathlib import Path
import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(text):
    cells.append(nb.v4.new_markdown_cell(text.strip()))


def code(text):
    compile(text.strip(), '<notebook cell>', 'exec')
    cells.append(nb.v4.new_code_cell(text.strip()))


md('''# PreSelect: documentos e resultados dos seis modelos

Abra este notebook e use **Run All / Executar tudo**. A análise é local, usa os resultados já calculados
e não precisa de GPU, conexão com a internet ou pesos de modelos. As saídas já estão salvas para leitura.

Vamos conferir a integridade, ver os textos, comparar as capacidades e os BPCs e descrever a força preditiva.
São os mesmos 1.000 documentos em duas execuções: quatro modelos iniciais e dois adicionais.
Não há análise semântica nem classificação dos textos como “bons” ou “ruins”.''')
code('''from pathlib import Path
import sys, json, hashlib, html, itertools
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, HTML, Markdown

ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents]
             if (p / 'dados/consolidado/documentos_forca_preditiva.jsonl').is_file()), None)
if ROOT is None:
    raise FileNotFoundError('Abra o notebook dentro da pasta entrega extraída, mantendo dados/ ao lado de notebooks/.')
DATA = ROOT / 'dados/consolidado'
FIGURES = ROOT / 'docs/figuras'
FIGURES.mkdir(parents=True, exist_ok=True)
df = pd.DataFrame(json.loads(line) for line in (DATA / 'documentos_forca_preditiva.jsonl').read_bytes().splitlines())
reports = json.loads((DATA / 'ranking_e_benchmarks.json').read_text(encoding='utf-8'))
models = sorted(reports, key=lambda model: reports[model]['benchmark']['score'])
bpc_columns = ['bpc__' + model for model in models]
short = {model: model.split('/')[-1] for model in models}
pd.set_option('display.max_colwidth', 100)
plt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False})
print(f'{len(df):,} documentos | {df.domain.nunique()} domínios | {len(models)} modelos | {df[bpc_columns].count().sum():,} BPCs')''')
md('''## 1. Conferência dos resultados

Esta célula valida os seis ZIPs originais, recibos, textos, checkpoints, contagens dos benchmarks e
cobertura dos tokens. Também recalcula a força a partir dos ZIPs e compara com o consolidado entregue.''')
code('''sys.path.insert(0, str(ROOT / 'src'))
from verificar import verify
verification = verify(ROOT)
print('Integridade:', verification['status'])
print('Pares comparáveis por documento:', verification['comparable_pairs_per_document'])
display(pd.DataFrame([{'documentos': len(df), 'domínios': df.domain.nunique(),
                      'IDs duplicados': int(df.document_id.duplicated().sum()),
                      'textos repetidos por hash': int(df.text_sha256.duplicated().sum()),
                      'BPCs ausentes': int(df[bpc_columns].isna().sum().sum()),
                      'caracteres totais': int(df.n_chars.sum())}]))''')
md('''## 2. Ver os documentos

A tabela mostra uma prévia. Ajuste os filtros abaixo e execute novamente esta célula.
`BUSCA` procura uma sequência literal no texto; não é uma comparação semântica.''')
code('''DOMINIO = ''           # Exemplo: copie um domínio da tabela; vazio inclui todos.
BUSCA = ''             # Texto literal; vazio inclui todos.
FORCA_MINIMA = 0.0
FORCA_MAXIMA = 1.0

selection = df.loc[df.predictive_strength.between(FORCA_MINIMA, FORCA_MAXIMA)].copy()
if DOMINIO:
    selection = selection[selection.domain.eq(DOMINIO)]
if BUSCA:
    selection = selection[selection.text.str.contains(BUSCA, case=False, regex=False, na=False)]
selection = selection.sort_values(['predictive_strength', 'document_id'], ascending=[False, True]).reset_index(drop=True)
preview = selection[['document_id', 'domain', 'n_chars', 'predictive_strength', 'concordant_pairs']].copy()
preview['trecho'] = selection.text.str.replace(r'\\s+', ' ', regex=True).str.slice(0, 180)
print(f'{len(selection)} documentos encontrados. Mostrando os primeiros 15:')
display(preview.head(15))''')
code('''POSICAO = 0            # Posição na seleção acima, começando em zero.
DOCUMENT_ID = ''        # Opcional: ID completo; substitui a escolha por posição.

def mostrar_documento(row):
    display(pd.DataFrame([{key: row[key] for key in
                         ['document_id', 'domain', 'url', 'n_chars', 'concordant_pairs', 'comparable_pairs', 'predictive_strength']}]))
    display(pd.DataFrame({'modelo': [short[m] for m in models],
                          'BPC': [row['bpc__' + m] for m in models]}))
    # Escape HTML para mostrar o texto como dado, sem executar conteúdo do corpus.
    display(HTML('<div style="white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #ccc;'
                 'padding:16px;max-height:650px;overflow:auto">' + html.escape(row['text']) + '</div>'))

if DOCUMENT_ID:
    chosen = df[df.document_id.eq(DOCUMENT_ID)]
    if chosen.empty:
        print('ID não encontrado.')
    else:
        mostrar_documento(chosen.iloc[0])
elif 0 <= POSICAO < len(selection):
    mostrar_documento(selection.iloc[POSICAO])
else:
    print('Nenhum documento nessa posição. Ajuste os filtros ou POSICAO.')''')
md('''## 3. Capacidade dos modelos e BPC

Capacidade é a média simples de HellaSwag (`acc_norm`), ARC-Easy (`acc_norm`) e BoolQ (`acc`),
com avaliação completa e zero-shot. Os números abaixo são proporções de acerto, entre 0 e 1.
**BPC menor significa que o modelo previu melhor aquele texto.**
A ordem dos modelos é definida pela capacidade medida, não pelo número de parâmetros.''')
code('''model_rows = []
for model in models:
    benchmark = reports[model]['benchmark']
    values = df['bpc__' + model]
    model_rows.append({'modelo': short[model], 'capacidade': benchmark['score'],
                      **benchmark['per_task'], 'BPC médio': values.mean(),
                      'BPC mediano': values.median(), 'BPC p10': values.quantile(.1),
                      'BPC p90': values.quantile(.9)})
model_table = pd.DataFrame(model_rows)
display(model_table.round(4))

fig, ax = plt.subplots(figsize=(10, 4))
ax.boxplot([df['bpc__' + m] for m in models], showfliers=False)
ax.set_xticks(range(1, len(models) + 1), [short[m] for m in models], rotation=25, ha='right')
ax.set_ylabel('BPC (menor = melhor previsão)')
ax.set_title('BPC dos mesmos 1.000 documentos por modelo; pontos extremos omitidos no gráfico')
fig.tight_layout()
fig.savefig(FIGURES / 'bpc_por_modelo.png', dpi=160, bbox_inches='tight')
plt.show()''')
md('''## 4. Distribuição da força preditiva

Para cada par de modelos, verificamos se o modelo com maior capacidade também tem BPC menor.
A força é a fração desses pares que concordam. Aqui há 15 pares: `15/15 = 1`, `14/15 ≈ 0,933` etc.
Empates de capacidade seriam excluídos; empate de BPC não conta como concordância.
Força alta indica concordância entre essas ordenações, não uma medida direta de qualidade semântica.''')
code('''distribution = (df.groupby(['concordant_pairs', 'comparable_pairs'])
                  .size().rename('documentos').reset_index())
distribution['força'] = distribution.concordant_pairs / distribution.comparable_pairs
distribution['percentual'] = 100 * distribution.documentos / len(df)
display(distribution.round(3))
display(df[['predictive_strength', 'n_chars']].describe().round(3))

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
labels = [f'{a}/{b}' for a, b in zip(distribution.concordant_pairs, distribution.comparable_pairs)]
axes[0].bar(labels, distribution.documentos, color='#246b96')
axes[0].set(title='Concordância entre os 15 pares', xlabel='Pares concordantes / comparáveis', ylabel='Documentos')
axes[1].hist(df.n_chars, bins=30, color='#3a8d73')
axes[1].set(title='Comprimento dos textos', xlabel='Caracteres Unicode', ylabel='Documentos')
fig.tight_layout()
fig.savefig(FIGURES / 'forca_e_comprimento.png', dpi=160, bbox_inches='tight')
plt.show()''')
md('''## 5. Quais pares discordam e como os domínios se distribuem?

“Não concordantes” inclui inversões de BPC e empates exatos. Cada linha compara os mesmos 1.000 textos.
Os resumos por domínio são descritivos; a amostra tem apenas 20 documentos por domínio e não permite
generalizar estas médias para toda a web.''')
code('''pair_rows = []
for weak, strong in itertools.combinations(models, 2):
    if reports[weak]['benchmark']['score'] == reports[strong]['benchmark']['score']:
        continue
    concordant = df['bpc__' + weak] > df['bpc__' + strong]
    ties = df['bpc__' + weak] == df['bpc__' + strong]
    pair_rows.append({'menor capacidade': short[weak], 'maior capacidade': short[strong],
                      'concordantes': int(concordant.sum()), 'não concordantes': int((~concordant).sum()),
                      'empates de BPC': int(ties.sum()), 'concordância (%)': 100 * concordant.mean()})
pair_table = pd.DataFrame(pair_rows).sort_values('não concordantes', ascending=False)
display(pair_table.round(2))

domain_table = df.groupby('domain').agg(documentos=('document_id', 'size'),
    força_média=('predictive_strength', 'mean'), caracteres_medianos=('n_chars', 'median'))
domain_table = domain_table.sort_values(['força_média', 'domain'], ascending=[False, True])
print('Cinco maiores e cinco menores médias observadas, entre os 50 domínios:')
display(pd.concat([domain_table.head(5), domain_table.tail(5)]).round(3))
length_correlation = df.n_chars.rank().corr(df.predictive_strength.rank())
print(f'Correlação descritiva por postos entre comprimento e força: {length_correlation:.3f}')''')
md('''## 6. Um exemplo de menor força e o que podemos concluir

O exemplo abaixo tem a menor força observada; isso não é um rótulo de texto “ruim”.
A exibição do texto serve à inspeção humana, sem análise semântica automatizada.''')
code('''mostrar_documento(df.sort_values(['predictive_strength', 'document_id']).iloc[0])
maximum_count = int(df.predictive_strength.eq(1).sum())
display(Markdown(f"""**Leitura dos resultados:** {maximum_count} de {len(df)} documentos
({maximum_count / len(df):.1%}) concordam nos 15 pares. A força média é
{df.predictive_strength.mean():.4f}; o intervalo observado é
{df.predictive_strength.min():.2f} a {df.predictive_strength.max():.2f}.

As diferenças de capacidade entre Pythia 1B, Pythia 1.4B e GPT-Neo 1.3B são pequenas.
A ordem é a dos escores medidos; não foi estimada a incerteza dessa ordem.
Os resultados descrevem esta amostra e esta suíte. Não demonstram, por si sós, que selecionar esses
documentos melhora o treinamento de um novo modelo. A comparação semântica e experimentos de
treinamento ficam como etapas posteriores."""))''')
md('''## 7. Salvar tabelas para continuar o trabalho

As tabelas auxiliares e os gráficos ficam em `docs/`. Os dados completos permanecem em
`dados/consolidado/`, incluindo textos, IDs, hashes e proveniência.
Para cruzar análises futuras, use `document_id` como chave; não use a posição da linha.''')
code('''model_table.to_csv(ROOT / 'docs/resumo_modelos.csv', index=False, encoding='utf-8-sig')
distribution.to_csv(ROOT / 'docs/distribuicao_forca.csv', index=False, encoding='utf-8-sig')
pair_table.to_csv(ROOT / 'docs/comparacoes_pares.csv', index=False, encoding='utf-8-sig')
domain_table.to_csv(ROOT / 'docs/resumo_dominios.csv', encoding='utf-8-sig')
summary = {'documentos': len(df), 'dominios': int(df.domain.nunique()), 'modelos': len(models),
           'bpcs': int(df[bpc_columns].count().sum()), 'forca_media': float(df.predictive_strength.mean()),
           'forca_mediana': float(df.predictive_strength.median()), 'forca_minima': float(df.predictive_strength.min()),
           'forca_maxima': float(df.predictive_strength.max()), 'concordancia_total_documentos': maximum_count,
           'caracteres_totais': int(df.n_chars.sum()), 'correlacao_postos_comprimento_forca': float(length_correlation),
           'distribuicao': distribution.to_dict(orient='records')}
(ROOT / 'docs/resumo_resultados.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('Tabelas, resumo e gráficos salvos em docs/. Dados originais preservados.')''')

notebook = nb.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3 (ipykernel)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.12'}})
nb.validate(notebook)
target = ROOT / 'notebooks/01_Explorar_Documentos_e_Resultados.ipynb'
nb.write(notebook, target)
print(target)
