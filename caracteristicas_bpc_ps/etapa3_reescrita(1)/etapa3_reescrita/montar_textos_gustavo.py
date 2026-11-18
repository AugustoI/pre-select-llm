"""Monta o arquivo de textos para a etapa de reescrita, com o indice ja casado."""
import json, numpy as np, pandas as pd

JSONL = "/home/claude/augustoi/pre-select-llm/entrega/dados/consolidado/documentos_forca_preditiva.jsonl"
docs = [json.loads(l) for l in open(JSONL, encoding="utf-8")]
d = pd.DataFrame(docs)
bpc = [c for c in d.columns if c.startswith("bpc__")]
d["bpc_medio"] = d[bpc].mean(axis=1)

# mesmo indice da base de caracteristicas: 1..1000 ordenado por document_id
d = d.sort_values("document_id").reset_index(drop=True)
d.insert(0, "indice", range(1, len(d) + 1))

# confere que bate com a base ja entregue
base = pd.read_csv("base_mesclada_completa.csv", encoding="utf-8-sig")
casado = d.merge(base[["indice", "document_id"]], on="indice", suffixes=("", "_base"))
assert (casado["document_id"] == casado["document_id_base"]).all(), "indice nao bate!"
print("indice confere com base_mesclada_completa.csv")

# grupos por BPC: maior BPC = pior
ordem = d.sort_values("bpc_medio", ascending=False).reset_index(drop=True)
piores_200 = set(ordem.loc[:199, "indice"])
melhores_200 = set(ordem.loc[len(ordem) - 200:, "indice"])
d["grupo"] = np.where(d["indice"].isin(piores_200), "piores_200",
             np.where(d["indice"].isin(melhores_200), "melhores_200", "meio"))

cols = ["indice", "document_id", "domain", "grupo", "n_chars",
        "bpc_medio", "predictive_strength", "text"]

with open("textos_para_reescrita.jsonl", "w", encoding="utf-8") as f:
    for _, r in d[cols].iterrows():
        f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

# amostra do plano original: 100 dos 200 piores + 100 do meio
rng = np.random.default_rng(42)
a = d[d["grupo"] == "piores_200"].sample(100, random_state=42)
b = d[d["grupo"] == "meio"].sample(100, random_state=42)
amostra = pd.concat([a, b]).sort_values("indice")
with open("amostra_200_para_reescrita.jsonl", "w", encoding="utf-8") as f:
    for _, r in amostra[cols].iterrows():
        f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

print(f"textos_para_reescrita.jsonl      {len(d)} textos")
print(f"amostra_200_para_reescrita.jsonl {len(amostra)} textos "
      f"({(amostra.grupo=='piores_200').sum()} piores + {(amostra.grupo=='meio').sum()} meio)")
print(f"\nBPC medio: piores_200 = {d[d.grupo=='piores_200'].bpc_medio.mean():.3f} | "
      f"meio = {d[d.grupo=='meio'].bpc_medio.mean():.3f} | "
      f"melhores_200 = {d[d.grupo=='melhores_200'].bpc_medio.mean():.3f}")
print(f"tamanho mediano dos textos: {int(d.n_chars.median())} caracteres")
