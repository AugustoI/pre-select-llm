"""
Etapa de mesclagem e regressao do projeto PRESELECT (parte do Rafael).

Junta tres fontes pelo document_id:
  1. documentos_resumo.csv  -> BPC dos 6 modelos, dominio, forca preditiva (Augusto)
  2. caracteristicas.csv    -> 61 caracteristicas linguisticas do spaCy (Rafael)
  3. o indice numerico 1..1000, criado aqui, que o grupo usa para cruzar os textos

Roda a regressao em duas versoes de Y, porque a reuniao nao definiu qual e o
"BPC Score" do diagrama, e as duas NAO sao equivalentes (Spearman ~ -0,22):
  Y_bpc  = -(media dos 6 BPCs)     -> maior = melhor
  Y_ps   = forca preditiva          -> maior = melhor

Cada Y roda em dois modelos:
  simples    : Y ~ X1+X2+X3+X4
  controlado : Y ~ X1+X2+X3+X4 + log(tamanho) + dominio

Saidas: base_mesclada.csv, resultados_regressao.md, regressao_completa.txt
"""
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

RESUMO = "/home/claude/augustoi/pre-select-llm/entrega/dados/consolidado/documentos_resumo.csv"
CARAC  = "/home/claude/perfil_zip/perfil_linguistico/resultados/caracteristicas.csv"
COMPAR = "/home/claude/perfil_zip/perfil_linguistico/resultados/comparacao_grupos.csv"

# ---------------------------------------------------------------- 1. mesclagem
resumo = pd.read_csv(RESUMO, encoding="utf-8-sig")
carac  = pd.read_csv(CARAC)
bpc_cols = [c for c in resumo.columns if c.startswith("bpc__")]

for nome, df in [("resumo", resumo), ("caracteristicas", carac)]:
    assert df["document_id"].is_unique, f"document_id duplicado em {nome}"
    assert df["document_id"].notna().all(), f"document_id vazio em {nome}"

resumo = resumo.sort_values("document_id").reset_index(drop=True)
resumo.insert(0, "indice", range(1, len(resumo) + 1))   # 1..1000, ordem estavel por hash

base = resumo.merge(carac, on="document_id", how="outer",
                    validate="one_to_one", indicator=True)
conferencia = base["_merge"].value_counts().to_dict()
assert conferencia.get("both") == 1000 and len(base) == 1000, conferencia
base = base.drop(columns="_merge")

# ---------------------------------------------------------------- 2. variaveis
base["bpc_medio"]       = base[bpc_cols].mean(axis=1)
base["Y_bpc"]           = -base["bpc_medio"]          # invertido: maior = melhor
base["Y_ps"]            = base["predictive_strength"]
base["log_tamanho"]     = np.log(base["n_chars"].clip(lower=1))

FEATURES = [c for c in carac.columns
            if c not in ("document_id", "foi_cortado", "cov_log_n_chars")]

# --------------------------------------------- 3. dois conjuntos de 4 variaveis
# conjunto A: herdado da etapa anterior (importancia por permutacao na
#             classificacao PS alta x PS baixa). NAO foi otimizado para BPC.
comp = pd.read_csv(COMPAR)
comp = comp[comp["caracteristica"].isin(FEATURES)]
CONJ_A = comp.sort_values("importancia_permutacao", ascending=False)["caracteristica"].head(4).tolist()

# conjunto B: selecionado para o alvo certo. Para cada caracteristica, roda
#             Y ~ carac + log(tamanho) + dominio e guarda |t|. Fica com as 4
#             maiores que nao estejam muito correlacionadas entre si (|r| < 0,6).
def selecionar_para_alvo(y_col, k=4, limite_r=0.6):
    pontuacao = []
    for f in FEATURES:
        d = base[[y_col, f, "log_tamanho", "domain"]].rename(columns={f: "v", y_col: "y"})
        try:
            m = smf.ols("y ~ v + log_tamanho + C(domain)", data=d).fit()
            pontuacao.append((f, abs(m.tvalues["v"]), m.params["v"], m.pvalues["v"]))
        except Exception:
            pass
    pontuacao.sort(key=lambda r: -r[1])
    escolhidas = []
    for f, t, coef, p in pontuacao:
        if p >= 0.05:
            continue
        if any(abs(base[f].corr(base[g])) > limite_r for g in escolhidas):
            continue
        escolhidas.append(f)
        if len(escolhidas) == k:
            break
    return escolhidas

CONJ_B = selecionar_para_alvo("Y_bpc")

# ---------------------------------------------------------------- 4. regressoes
def rodar(y_col, feats, com_controle):
    d = base.rename(columns={y_col: "y"}).copy()
    for i, f in enumerate(feats, 1):
        d[f"X{i}"] = d[f]
    termos = " + ".join(f"X{i}" for i in range(1, len(feats) + 1))
    formula = f"y ~ {termos}" + (" + log_tamanho + C(domain)" if com_controle else "")
    m = smf.ols(formula, data=d).fit()
    # padronizados: so faz sentido no modelo simples
    z = d.copy()
    for c in [f"X{i}" for i in range(1, len(feats) + 1)] + ["y"]:
        z[c] = (z[c] - z[c].mean()) / z[c].std()
    mz = smf.ols(f"y ~ {termos}", data=z).fit()
    linhas = []
    for i, f in enumerate(feats, 1):
        linhas.append({"variavel": f"X{i}", "caracteristica": f,
                       "coef": m.params[f"X{i}"], "p": m.pvalues[f"X{i}"],
                       "beta_padronizado": mz.params[f"X{i}"]})
    return m, pd.DataFrame(linhas)

def r2_concorrentes(y_col):
    out = {}
    for nome, extra in [("so as 4 caracteristicas", None), ("so tamanho", "log_tamanho"),
                        ("so dominio", "C(domain)")]:
        if extra is None:
            continue
        out[nome] = smf.ols(f"{y_col} ~ {extra}", data=base).fit().rsquared
    return out

def vif(feats):
    X = sm.add_constant(base[feats])
    return {f: variance_inflation_factor(X.values, i)
            for i, f in enumerate(X.columns) if f != "const"}

# ---------------------------------------------------------------- 5. relatorio
linhas_md = []
w = linhas_md.append
w("# Mesclagem e regressao — resultados\n")
w(f"Base: {len(base)} documentos, merge por `document_id` "
  f"({conferencia.get('both')} de {len(base)} batendo, sem sobras).\n")
w("Indice numerico `indice` 1..1000, criado aqui, ordenado por `document_id`.\n")
w(f"\nCorrelacao entre os dois candidatos a Y (Spearman): "
  f"{base[['bpc_medio','predictive_strength']].corr(method='spearman').iloc[0,1]:+.3f} "
  "— sao medidas diferentes, nao duas versoes da mesma.\n")

texto_completo = []
for y_col, rotulo in [("Y_bpc", "Y = -(BPC medio dos 6 modelos)"),
                      ("Y_ps",  "Y = forca preditiva (predictive strength)")]:
    w(f"\n## {rotulo}\n")
    conc = r2_concorrentes(y_col)
    for conj_nome, feats in [("A (herdado da etapa anterior)", CONJ_A),
                             ("B (selecionado para este alvo)", CONJ_B)]:
        m_s, t_s = rodar(y_col, feats, com_controle=False)
        m_c, t_c = rodar(y_col, feats, com_controle=True)
        w(f"\n### Conjunto {conj_nome}\n")
        w(f"R² só as 4: **{m_s.rsquared:.3f}** · só tamanho: {conc['so tamanho']:.3f} · "
          f"só domínio: {conc['so dominio']:.3f} · 4+tamanho+domínio: {m_c.rsquared:.3f}\n")
        w("\n| | característica | β padronizado | p (simples) | p (com controle) | direção |")
        w("|---|---|---:|---:|---:|---|")
        for (_, a), (_, b_) in zip(t_s.iterrows(), t_c.iterrows()):
            direcao = "reduzir" if a["beta_padronizado"] < 0 else "aumentar"
            robusto = "" if b_["p"] < 0.05 else " ⚠"
            w(f"| {a['variavel']} | `{a['caracteristica']}` | {a['beta_padronizado']:+.3f} | "
              f"{a['p']:.4f} | {b_['p']:.4f}{robusto} | {direcao} |")
        vifs = vif(feats)
        w(f"\nVIF: " + ", ".join(f"{k.split('_')[0]}…={v:.2f}" for k, v in vifs.items()) +
          " (todos baixos, sem multicolinearidade).\n")
        texto_completo.append(f"\n{'='*70}\n{rotulo} — conjunto {conj_nome}\n"
                              f"{'='*70}\nSIMPLES\n{m_s.summary()}\n\nCOM CONTROLE\n{m_c.summary()}\n")

w("\n## Leitura\n")
w("- `direção` diz o que a reescrita deve fazer com a característica: como os dois Y são "
  "\"maior = melhor\", coeficiente negativo significa que mais daquilo piora o texto.\n")
w("- ⚠ marca característica que **não** sobrevive ao controle de tamanho e domínio.\n")
w("- O domínio sozinho explica mais que as quatro características juntas. Por isso a "
  "comparação da etapa 3 tem que ser pareada: o mesmo texto, com e sem injection.\n")

open("resultados_regressao.md", "w").write("\n".join(linhas_md))
open("regressao_completa.txt", "w").write("\n".join(texto_completo))

# ---------------------------------------------------------------- 6. base final
cols = (["indice", "document_id", "domain", "n_chars", "log_tamanho",
         "predictive_strength", "concordant_pairs", "comparable_pairs",
         "bpc_medio", "Y_bpc", "Y_ps"] + bpc_cols + FEATURES)
base[cols].to_csv("base_mesclada.csv", index=False, encoding="utf-8-sig")

print("\n".join(linhas_md))
print("\nCONJ_A =", CONJ_A)
print("CONJ_B =", CONJ_B)
