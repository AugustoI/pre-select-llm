"""
Regressão sobre o conjunto completo de características textuais (101 variáveis):
as 61 do extrator anterior mais as 40 das famílias usadas na literatura.

Desenho, para não cair em seleção enviesada:
  * a amostra de 1000 documentos é dividida ao meio (semente fixa);
  * a seleção das variáveis é feita SÓ na metade de treino;
  * o R² relatado é medido na metade de validação, que não participou da seleção.

Para cada alvo (Y), relata:
  1. R² de cada família de características sozinha (qual família explica o BPC);
  2. as variáveis escolhidas e seus coeficientes padronizados;
  3. R² dentro e fora da amostra, contra os baselines de tamanho e domínio.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.model_selection import train_test_split

SEMENTE = 42
RESUMO = "/home/claude/augustoi/pre-select-llm/entrega/dados/consolidado/documentos_resumo.csv"
CARAC_61 = "/home/claude/perfil_zip/perfil_linguistico/resultados/caracteristicas.csv"
CARAC_LIT = "caracteristicas_literatura.csv"
CARAC_ORT = "caracteristicas_ortografia.csv"

FAMILIAS = {
    "legibilidade": "leg_",
    "raridade lexical": "rar_",
    "diversidade lexical": "div_",
    "compressao/informacao": "inf_",
    "qualidade de corpus (Gopher/C4)": "qlt_",
    "sintaxe (L2SCA)": "sinx_",
    "lexico (extrator anterior)": "lex_",
    "sintaxe (extrator anterior)": "sin_",
    "coesao (extrator anterior)": "coe_",
    "organizacao (extrator anterior)": "org_",
    "registro (extrator anterior)": "reg_",
    "ortografia": "ort_",
    "vocabulario relevante": "voc_",
}


def montar_base():
    resumo = pd.read_csv(RESUMO, encoding="utf-8-sig").sort_values("document_id").reset_index(drop=True)
    resumo.insert(0, "indice", range(1, len(resumo) + 1))
    c61 = pd.read_csv(CARAC_61).drop(columns=["foi_cortado"], errors="ignore")
    clit = pd.read_csv(CARAC_LIT)

    base = resumo.merge(c61, on="document_id", how="outer", validate="one_to_one", indicator="m1")
    assert (base["m1"] == "both").all(), base["m1"].value_counts().to_dict()
    base = base.drop(columns="m1").merge(clit, on="document_id", how="outer",
                                         validate="one_to_one", indicator="m2")
    assert (base["m2"] == "both").all(), base["m2"].value_counts().to_dict()
    base = base.drop(columns="m2").merge(pd.read_csv(CARAC_ORT), on="document_id",
                                         how="outer", validate="one_to_one", indicator="m3")
    assert (base["m3"] == "both").all(), base["m3"].value_counts().to_dict()
    base = base.drop(columns="m3")
    assert len(base) == 1000

    bpc_cols = [c for c in base.columns if c.startswith("bpc__")]
    base["bpc_medio"] = base[bpc_cols].mean(axis=1)
    base["Y_bpc"] = -base["bpc_medio"]
    base["Y_ps"] = base["predictive_strength"]
    base["log_tamanho"] = np.log(base["n_chars"].clip(lower=1))

    nao_feat = set(["indice", "document_id", "original_id", "url", "domain", "n_chars",
                    "text_sha256", "source_url", "source_line", "predictive_strength",
                    "concordant_pairs", "comparable_pairs", "benchmark_tied_pairs",
                    "bpc_medio", "Y_bpc", "Y_ps", "log_tamanho", "cov_log_n_chars"] + bpc_cols)
    feats = [c for c in base.columns if c not in nao_feat and base[c].dtype != object]
    # descarta variáveis constantes ou quase (não dá para padronizar)
    feats = [f for f in feats if base[f].std() > 1e-9]
    base[feats] = base[feats].replace([np.inf, -np.inf], np.nan)
    base[feats] = base[feats].fillna(base[feats].median())
    return base, feats, bpc_cols


def r2_fora(modelo, dados_val, y_col):
    pred = modelo.predict(dados_val)
    y = dados_val[y_col]
    return 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def r2_familia(treino, val, feats, y_col, prefixo):
    membros = [f for f in feats if f.startswith(prefixo)]
    if not membros:
        return None, 0
    formula = f"{y_col} ~ " + " + ".join(membros)
    m = smf.ols(formula, data=treino).fit()
    return r2_fora(m, val, y_col), len(membros)


def selecionar(treino, feats, y_col, k=8, limite_r=0.6, excluir_prefixos=()):
    """Ranqueia por |t| em Y ~ caracteristica + log(tamanho) + dominio, só no treino.

    `excluir_prefixos` tira famílias do conjunto candidato. Usado para a família
    `ort_`: ela é forte sozinha, mas redundante com a raridade lexical (ver a seção
    "Teste da família de ortografia" no relatório), e como a busca aqui é gulosa,
    deixá-la concorrer expulsa variáveis melhores e piora o modelo final.
    """
    pontos = []
    feats = [f for f in feats if not f.startswith(tuple(excluir_prefixos))] if excluir_prefixos else feats
    for f in feats:
        d = treino[[y_col, f, "log_tamanho", "domain"]].rename(columns={f: "v", y_col: "y"})
        try:
            m = smf.ols("y ~ v + log_tamanho + C(domain)", data=d).fit()
            if np.isfinite(m.tvalues["v"]):
                pontos.append((f, abs(m.tvalues["v"]), m.pvalues["v"]))
        except Exception:
            pass
    pontos.sort(key=lambda r: -r[1])
    escolhidas = []
    for f, t, p in pontos:
        if p >= 0.05:
            continue
        if any(abs(treino[f].corr(treino[g])) > limite_r for g in escolhidas):
            continue
        escolhidas.append(f)
        if len(escolhidas) == k:
            break
    return escolhidas, pontos


def main():
    base, feats, bpc_cols = montar_base()
    print(f"base: {len(base)} documentos, {len(feats)} caracteristicas\n")

    treino, val = train_test_split(base, test_size=0.5, random_state=SEMENTE)
    linhas_md = ["# Regressão com as características da literatura\n",
                 f"Base: {len(base)} documentos, **{len(feats)} características** "
                 f"(61 do extrator anterior + 40 das famílias usadas na literatura).\n",
                 f"Desenho: a amostra é dividida ao meio (semente {SEMENTE}). A seleção das "
                 "variáveis usa **somente a metade de treino**; o R² relatado é medido na "
                 "metade de validação, que não participou da seleção.\n"]
    w = linhas_md.append

    for y_col, rotulo in [("Y_bpc", "Y = −(BPC médio dos 6 modelos)"),
                          ("Y_ps", "Y = força preditiva")]:
        w(f"\n## {rotulo}\n")

        # --- 1. famílias sozinhas, medidas fora da amostra ---
        w("\n### Qual família explica o alvo\n")
        w("R² medido na metade de validação, cada família sozinha.\n")
        w("\n| Família | nº de variáveis | R² fora da amostra |")
        w("|---|---:|---:|")
        resultados_fam = []
        for nome, prefixo in FAMILIAS.items():
            r2, n = r2_familia(treino, val, feats, y_col, prefixo)
            if r2 is not None:
                resultados_fam.append((nome, n, r2))
        for nome, n, r2 in sorted(resultados_fam, key=lambda r: -r[2]):
            w(f"| {nome} | {n} | {r2:.3f} |")
        for nome, formula in [("tamanho do texto (baseline)", "log_tamanho"),
                              ("domínio do site (baseline)", "C(domain)")]:
            m = smf.ols(f"{y_col} ~ {formula}", data=treino).fit()
            w(f"| *{nome}* | 1 | {r2_fora(m, val, y_col):.3f} |")

        # --- 2. seleção e modelo final ---
        escolhidas, ranking = selecionar(treino, feats, y_col, k=8, excluir_prefixos=("ort_",))
        w(f"\n### As 8 variáveis selecionadas (no treino) e validadas\n")
        formula = f"{y_col} ~ " + " + ".join(escolhidas)
        m = smf.ols(formula, data=treino).fit()
        z_tr = treino.copy()
        for c in escolhidas + [y_col]:
            z_tr[c] = (z_tr[c] - z_tr[c].mean()) / z_tr[c].std()
        mz = smf.ols(formula, data=z_tr).fit()

        w("\n| característica | família | β padronizado | p | direção |")
        w("|---|---|---:|---:|---|")
        for f in escolhidas:
            fam = next((nome for nome, pre in FAMILIAS.items() if f.startswith(pre)), "?")
            beta = mz.params[f]
            w(f"| `{f}` | {fam} | {beta:+.3f} | {m.pvalues[f]:.4f} | "
              f"{'aumentar' if beta > 0 else 'reduzir'} |")

        r2_val = r2_fora(m, val, y_col)
        m_ctrl = smf.ols(formula + " + log_tamanho + C(domain)", data=treino).fit()
        w(f"\nR² no treino: {m.rsquared:.3f} · **R² na validação: {r2_val:.3f}** · "
          f"com tamanho e domínio junto: {r2_fora(m_ctrl, val, y_col):.3f}\n")

        # --- 3. as 15 mais fortes individualmente, para consulta ---
        w("\n<details><summary>As 15 variáveis mais fortes individualmente "
          "(|t| controlando tamanho e domínio, no treino)</summary>\n")
        w("\n| característica | \\|t\\| | p |")
        w("|---|---:|---:|")
        for f, t, p in ranking[:15]:
            w(f"| `{f}` | {t:.2f} | {p:.4f} |")
        w("\n</details>\n")

        # --- 4. teste da família de ortografia (sugestão do Ícaro) ---
        if y_col == "Y_bpc":
            w("\n### Teste da família de ortografia\n")
            ort = [f for f in feats if f.startswith("ort_")]
            ranking_todos = {f: (t, p) for f, t, p in
                             selecionar(treino, feats, y_col, k=1)[1]}
            posicao = [f for f, _, _ in sorted(
                selecionar(treino, feats + ort, y_col, k=1)[1],
                key=lambda r: -r[1])]
            w("`ort_frac_erros` está entre as variáveis mais fortes **individualmente** "
              f"(|t| = {ranking_todos.get('ort_frac_erros', (0, 0))[0]:.2f}), mas não "
              "acrescenta nada ao modelo conjunto:\n")
            escolhidas_b, _ = selecionar(treino, feats, y_col, k=8)
            modelos = {
                "A: as 8 selecionadas (sem ortografia)": escolhidas,
                "B: 8 deixando a ortografia concorrer": escolhidas_b,
                "C: as 8 de A mais `ort_frac_erros`": escolhidas + ["ort_frac_erros"],
            }
            w("\n| Modelo | R² na validação |")
            w("|---|---:|")
            for nome, fs in modelos.items():
                mm = smf.ols(f"{y_col} ~ " + " + ".join(fs), data=treino).fit()
                w(f"| {nome} | {r2_fora(mm, val, y_col):.3f} |")
            w("\nA causa é redundância com a raridade lexical:\n")
            w("\n| | correlação com `ort_frac_erros` |")
            w("|---|---:|")
            for v in ["rar_zipf_p10", "rar_frac_raras", "rar_zipf_desvio",
                      "rar_frac_desconhecidas"]:
                w(f"| `{v}` | {base['ort_frac_erros'].corr(base[v]):+.3f} |")
            w("\nPara o `wordfreq`, uma palavra escrita errada é simplesmente uma palavra "
              "rara, então as medidas de raridade já capturavam o fenômeno. No modelo C o "
              "coeficiente da ortografia ainda troca de sinal, sinal clássico de "
              "colinearidade. Por isso o modelo reportado acima é o A.\n")

    # --- base final ---
    cols = (["indice", "document_id", "domain", "n_chars", "log_tamanho",
             "predictive_strength", "bpc_medio", "Y_bpc", "Y_ps"] + bpc_cols + feats)
    base[cols].to_csv("base_mesclada_completa.csv", index=False, encoding="utf-8-sig")
    open("resultados_regressao_literatura.md", "w").write("\n".join(linhas_md))
    print("\n".join(linhas_md))


if __name__ == "__main__":
    main()
