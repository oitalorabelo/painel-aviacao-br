"""Injeta os dados agregados no template e escreve a pagina final em dist/index.html."""
import io
import json
import os
import sys

TPL = sys.argv[1] if len(sys.argv) > 1 else "src/painel.template.html"
DADOS = sys.argv[2] if len(sys.argv) > 2 else "data/painel.json"
OUT = sys.argv[3] if len(sys.argv) > 3 else "dist/index.html"

tpl = io.open(TPL, encoding="utf-8").read()
if "__DADOS__" not in tpl:
    sys.exit(f"ERRO: {TPL} nao contem o marcador __DADOS__")

bruto = io.open(DADOS, encoding="utf-8").read()
meta = json.loads(bruto)["meta"]

# O JSON entra dentro de um <script type="application/json">; uma sequencia "</script"
# no conteudo fecharia a tag antes da hora. Os dados da ANAC nao tem isso, mas a pagina
# e gerada sem supervisao, entao a checagem fica.
if "</script" in bruto.lower():
    sys.exit("ERRO: os dados contem '</script' e quebrariam a pagina")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="\n").write(tpl.replace("__DADOS__", bruto))

print(f"OK {OUT} {os.path.getsize(OUT) // 1024} KB "
      f"| serie ate {meta['mes_max']:02d}/{meta['ano_max']} "
      f"| ultimo ano fechado {meta['ano_cheio']}")
