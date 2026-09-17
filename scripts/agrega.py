"""Agrega os Dados Estatisticos do Transporte Aereo (ANAC) em um JSON leve
para alimentar o dashboard. Fonte: sistemas.anac.gov.br/dadosabertos."""
import json
import sys
import os
import pandas as pd
import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else "dados_estatisticos.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/painel.json"

COLS = [
    "EMPRESA_SIGLA", "EMPRESA_NOME", "EMPRESA_NACIONALIDADE", "ANO", "MES",
    "AEROPORTO_DE_ORIGEM_SIGLA", "AEROPORTO_DE_ORIGEM_NOME", "AEROPORTO_DE_ORIGEM_UF",
    "AEROPORTO_DE_ORIGEM_PAIS",
    "AEROPORTO_DE_DESTINO_SIGLA", "AEROPORTO_DE_DESTINO_NOME", "AEROPORTO_DE_DESTINO_UF",
    "AEROPORTO_DE_DESTINO_PAIS",
    "NATUREZA", "GRUPO_DE_VOO",
    "PASSAGEIROS_PAGOS", "CARGA_PAGA_KG", "ASK", "RPK", "DECOLAGENS",
    "COMBUSTIVEL_LITROS", "ASSENTOS", "HORAS_VOADAS",
]
NUM = ["PASSAGEIROS_PAGOS", "CARGA_PAGA_KG", "ASK", "RPK", "DECOLAGENS",
       "COMBUSTIVEL_LITROS", "ASSENTOS", "HORAS_VOADAS"]

mensal, emp, apt, uf, rotas = [], [], [], [], []
nomes_emp, nomes_apt = {}, {}

reader = pd.read_csv(SRC, sep=";", skiprows=1, encoding="utf-8-sig", decimal=",",
                     usecols=COLS, dtype=str, chunksize=400_000,
                     na_values=[""], quotechar='"', engine="c")

for i, ch in enumerate(reader):
    for c in NUM:
        ch[c] = pd.to_numeric(ch[c].str.replace(",", ".", regex=False), errors="coerce")
    ch["ANO"] = pd.to_numeric(ch["ANO"], errors="coerce")
    ch["MES"] = pd.to_numeric(ch["MES"], errors="coerce")
    ch = ch[ch["GRUPO_DE_VOO"] == "REGULAR"]
    ch["NAT"] = np.where(ch["NATUREZA"].str.startswith("DOM", na=False), "DOM", "INT")
    ch[NUM] = ch[NUM].fillna(0)

    mensal.append(ch.groupby(["ANO", "MES", "NAT"], dropna=True)[NUM].sum())
    emp.append(ch.groupby(["ANO", "NAT", "EMPRESA_SIGLA"], dropna=True)[
        ["RPK", "ASK", "PASSAGEIROS_PAGOS", "DECOLAGENS"]].sum())

    # nomes de empresa (o mais recente prevalece)
    nomes_emp.update(dict(zip(ch["EMPRESA_SIGLA"], ch["EMPRESA_NOME"])))

    # movimento por aeroporto: pax na origem + pax no destino (so aeroportos BR)
    for lado in ("ORIGEM", "DESTINO"):
        sig, nom, ufc, pais = (f"AEROPORTO_DE_{lado}_SIGLA", f"AEROPORTO_DE_{lado}_NOME",
                               f"AEROPORTO_DE_{lado}_UF", f"AEROPORTO_DE_{lado}_PAIS")
        br = ch[ch[pais] == "BRASIL"]
        if br.empty:
            continue
        apt.append(br.groupby(["ANO", sig], dropna=True)["PASSAGEIROS_PAGOS"].sum()
                   .rename_axis(["ANO", "SIGLA"]))
        uf.append(br.groupby(["ANO", ufc], dropna=True)["PASSAGEIROS_PAGOS"].sum()
                  .rename_axis(["ANO", "UF"]))
        nomes_apt.update(dict(zip(br[sig], zip(br[nom], br[ufc]))))

    # rotas domesticas (par nao direcionado)
    d = ch[ch["NAT"] == "DOM"].copy()
    if not d.empty:
        a = d["AEROPORTO_DE_ORIGEM_SIGLA"].fillna("")
        b = d["AEROPORTO_DE_DESTINO_SIGLA"].fillna("")
        d["PAR"] = np.where(a < b, a + "-" + b, b + "-" + a)
        rotas.append(d.groupby(["ANO", "PAR"])[["PASSAGEIROS_PAGOS", "DECOLAGENS"]].sum())
    print(f"chunk {i}", flush=True)

mensal = pd.concat(mensal).groupby(level=[0, 1, 2]).sum().reset_index()
emp = pd.concat(emp).groupby(level=[0, 1, 2]).sum().reset_index()
apt = pd.concat(apt).groupby(level=[0, 1]).sum().reset_index()
uf = pd.concat(uf).groupby(level=[0, 1]).sum().reset_index()
rotas = pd.concat(rotas).groupby(level=[0, 1]).sum().reset_index()

mensal = mensal[(mensal["ANO"] >= 2000) & (mensal["MES"].between(1, 12))]
ano_max, mes_max = int(mensal["ANO"].max()), None
mes_max = int(mensal[mensal["ANO"] == ano_max]["MES"].max())
ano_cheio = ano_max - 1 if mes_max < 12 else ano_max

# --- serie mensal ---
serie = [{"a": int(r.ANO), "m": int(r.MES), "n": r.NAT,
          "rpk": float(r.RPK), "ask": float(r.ASK), "pax": float(r.PASSAGEIROS_PAGOS),
          "dec": float(r.DECOLAGENS), "carga": float(r.CARGA_PAGA_KG),
          "comb": float(r.COMBUSTIVEL_LITROS), "hrs": float(r.HORAS_VOADAS)}
         for r in mensal.itertuples()]

# --- estrutura de mercado por ano/natureza ---
def estrutura(g):
    tot = g["RPK"].sum()
    if tot <= 0:
        return None
    s = (g["RPK"] / tot).sort_values(ascending=False)
    return {"hhi": float((s ** 2).sum() * 10000), "cr4": float(s.head(4).sum()),
            "nemp": int((s > 0).sum())}

mercado, share = [], []
for (a, n), g in emp.groupby(["ANO", "NAT"]):
    e = estrutura(g)
    if not e:
        continue
    mercado.append({"a": int(a), "n": n, **e})
    tot = g["RPK"].sum()
    g = g.assign(sh=g["RPK"] / tot).sort_values("sh", ascending=False)
    maj = g[g["sh"] >= 0.02]
    for r in maj.itertuples():
        share.append({"a": int(a), "n": n, "e": r.EMPRESA_SIGLA, "sh": round(float(r.sh), 5),
                      "pax": float(r.PASSAGEIROS_PAGOS)})
    out = g[g["sh"] < 0.02]
    if len(out):
        share.append({"a": int(a), "n": n, "e": "OUTRAS", "sh": round(float(out["sh"].sum()), 5),
                      "pax": float(out["PASSAGEIROS_PAGOS"].sum())})

# --- aeroportos: top 20 do ultimo ano cheio, com serie historica ---
top_apt = (apt[apt["ANO"] == ano_cheio].sort_values("PASSAGEIROS_PAGOS", ascending=False)
           .head(20)["SIGLA"].tolist())
aero = [{"s": r.SIGLA, "a": int(r.ANO), "pax": float(r.PASSAGEIROS_PAGOS)}
        for r in apt[apt["SIGLA"].isin(top_apt)].itertuples()]
aero_meta = {s: {"nome": nomes_apt.get(s, ("", ""))[0], "uf": nomes_apt.get(s, ("", ""))[1]}
             for s in top_apt}

# --- UF no ultimo ano cheio ---
ufs = [{"uf": r.UF, "pax": float(r.PASSAGEIROS_PAGOS)}
       for r in uf[(uf["ANO"] == ano_cheio) & (uf["UF"].str.len() == 2)]
       .sort_values("PASSAGEIROS_PAGOS", ascending=False).itertuples()]

# --- top rotas domesticas ultimo ano cheio ---
rot = [{"par": r.PAR, "pax": float(r.PASSAGEIROS_PAGOS), "dec": float(r.DECOLAGENS)}
       for r in rotas[rotas["ANO"] == ano_cheio]
       .sort_values("PASSAGEIROS_PAGOS", ascending=False).head(15).itertuples()]

emp_nomes = {k: v for k, v in nomes_emp.items()
             if k in set(x["e"] for x in share)}

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
json.dump({
    "meta": {"fonte": "ANAC - Dados Estatisticos do Transporte Aereo",
             "url": "https://sistemas.anac.gov.br/dadosabertos/",
             "filtro": "voos REGULARES", "ano_max": ano_max, "mes_max": mes_max,
             "ano_cheio": int(ano_cheio)},
    "serie": serie, "mercado": mercado, "share": share,
    "aero": aero, "aero_meta": aero_meta, "uf": ufs, "rotas": rot,
    "empresas": emp_nomes,
}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

print("OK", OUT, os.path.getsize(OUT) // 1024, "KB",
      "| ano_max", ano_max, "mes_max", mes_max, "| ano_cheio", ano_cheio)
