# Como contribuir

Guia para quem do grupo vai mexer no painel. Leia o [README](README.md) antes para entender o
que o painel mostra e de onde vêm os dados.

## 1. Acesso

O repositório é público: qualquer pessoa pode ver e baixar. Para **editar** você precisa ser
colaborador — mande seu usuário do GitHub para o Italo, aceite o convite que chega por e‑mail
(ou em <https://github.com/notifications>) e pronto.

## 2. Preparar o ambiente (uma vez só)

Precisa de [Git](https://git-scm.com/) e [Python 3.12](https://www.python.org/downloads/).

```bash
git clone https://github.com/oitalorabelo/painel-aviacao-br.git
cd painel-aviacao-br
pip install -r requirements.txt
python scripts/build.py      # gera dist/index.html — abra no navegador
```

Para mexer só na página **não é preciso baixar a base da ANAC** (359 MB): o `build.py` usa o
`data/painel.json` que já está no repositório.

## 3. O fluxo de trabalho

A `main` é o que está no ar: **todo push na `main` republica o site**. Por isso, ninguém edita a
`main` direto — cada mudança vai num branch e entra por pull request (PR).

```bash
git checkout main
git pull                                  # sempre comece atualizado
git checkout -b minha-mudanca             # nome curto, ex.: grafico-regional
# ... edite, rode python scripts/build.py e confira dist/index.html no navegador ...
git add .
git commit -m "Adiciona gráfico por região"
git push -u origin minha-mudanca
```

Depois abra o PR no GitHub (aparece um botão *Compare & pull request*). Uma checagem automática
monta a página para garantir que nada quebrou; com ela verde e uma revisão de outra pessoa do
grupo, o PR pode ser mesclado.

> **Atenção ao `git pull`:** todo dia 12 um robô (`github-actions[bot]`) commita os dados novos
> da ANAC na `main`. Se o seu branch for antigo, atualize‑o com `git pull origin main` antes de
> abrir o PR.

## 4. Onde mexer

| Quero… | Arquivo |
|---|---|
| mudar visual, textos, gráficos ou filtros | `src/painel.template.html` (HTML/CSS/SVG puro, sem bibliotecas) |
| mudar o que é calculado a partir da ANAC | `scripts/agrega.py` (pandas) |
| mudar como a página final é montada | `scripts/build.py` |
| mudar agenda ou publicação | `.github/workflows/atualiza-painel.yml` |

Algumas regras:

- **Não edite `data/painel.json` à mão.** Ele é gerado pelo `agrega.py`. Se mudar o `agrega.py`,
  baixe a base (comando no README), rode o script e commite o JSON resultante junto.
- **Não commite** `dados_estatisticos.csv` nem `dist/` — já estão no `.gitignore`.
- O template precisa manter o marcador `__DADOS__`; é ali que o `build.py` injeta os dados.
- Escreva commits e PRs em português, dizendo *o que* mudou e *por quê*.

## 5. Dúvidas

Abra uma [issue](https://github.com/oitalorabelo/painel-aviacao-br/issues) descrevendo o problema
ou a ideia — vale também para bugs nos dados.
