# Painel do transporte aéreo brasileiro

Painel interativo com 26 anos de voos regulares no Brasil — demanda, oferta, taxa de ocupação e
concentração de mercado — construído a partir dos microdados da ANAC. A página se reconstrói
sozinha todo mês, via GitHub Actions.

**Painel:** https://oitalorabelo.github.io/painel-aviacao-br/
**Guia (PDF):** [`docs/guia-painel-aviacao.pdf`](docs/guia-painel-aviacao.pdf) — como ler o painel,
de onde vêm os dados e como ele é construído.

## O que ele mostra

- **Oferta × demanda** — ASK e RPK no mesmo eixo, mês a mês desde janeiro de 2000. O vão entre as
  duas áreas é o assento que voou vazio; a taxa de ocupação, no painel de baixo, é a razão entre elas.
- **Estrutura de mercado** — participação de cada companhia no RPK, por ano, e o índice
  Herfindahl‑Hirschman com as faixas usuais do antitruste.
- **Aeroportos e rotas** — movimento por aeroporto no último ano fechado, comparado ao nível de 2019,
  e os pares de aeroportos mais movimentados.
- Filtros de mercado (doméstico, internacional, total) e de período, além da série anual em tabela.

## Fonte

| | |
|---|---|
| Base | **Dados Estatísticos do Transporte Aéreo** — ANAC |
| Arquivo | `Dados_Estatisticos.csv` (~359 MB, ~1,1 milhão de linhas, 38 colunas) |
| Origem | [portal de dados abertos da ANAC](https://sistemas.anac.gov.br/dadosabertos/) › *Voos e operações aéreas* › *Dados Estatísticos do Transporte Aéreo* |
| Cobertura | janeiro de 2000 em diante, granularidade empresa × par de aeroportos × mês |
| Catálogo | localizada via [AVSTATS‑Brasil](https://avstats-brasil.avmoliveira.chatgpt.site/), do NECTAR‑ITA |

**Método.** Somente voos regulares. RPK e ASK são agregados por mês e natureza; a taxa de ocupação é
RPK/ASK. O movimento de um aeroporto soma passageiros pagos na origem e no destino, considerando
apenas aeroportos brasileiros. O HHI é calculado sobre a participação em RPK de todas as empresas do
mercado no ano, inclusive as que o gráfico agrupa em "outras". O último mês da série pode ser
preliminar.

## Como funciona

```
ANAC (CSV, 359 MB)
   └─ scripts/agrega.py ──> data/painel.json      (~155 KB, versionado)
                               └─ scripts/build.py ──> dist/index.html   (GitHub Pages)
                                     ▲
                                     └─ src/painel.template.html
```

O JSON agregado é commitado a cada execução, então o histórico do repositório guarda também o
histórico das revisões da ANAC.

### O workflow

`.github/workflows/atualiza-painel.yml` roda em três situações:

| Gatilho | O que faz |
|---|---|
| **Agendado** — dia 12, 06:00 BRT | baixa a base da ANAC, reagrega, commita o JSON se mudou e publica |
| **Push na `main`** | só remonta a página a partir do JSON versionado — não rebaixa os 359 MB |
| **Manual** (*Run workflow*) | igual ao agendado; a caixa `rebaixar` permite pular o download |

O download é validado antes de seguir: o job falha se o arquivo vier com menos de 300 MB ou se a
primeira linha não trouxer o `Atualizado em:` esperado — assim uma mudança de layout na ANAC aparece
como erro, e não como painel silenciosamente errado.

## Rodando localmente

```bash
pip install -r requirements.txt

# baixa a base (~359 MB; aceita retomada com -C -)
curl -L -C - -o dados_estatisticos.csv \
  "https://sistemas.anac.gov.br/dadosabertos/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Dados%20Estat%C3%ADsticos%20do%20Transporte%20A%C3%A9reo/Dados_Estatisticos.csv"

python scripts/agrega.py dados_estatisticos.csv data/painel.json
python scripts/build.py          # -> dist/index.html
```

Para só reconstruir a página depois de mexer no template, o `build.py` sozinho basta.

## Estrutura

```
.github/workflows/atualiza-painel.yml   agendamento, build e deploy
scripts/agrega.py                       CSV da ANAC -> JSON agregado
scripts/build.py                        template + JSON -> página final
src/painel.template.html                página (HTML/CSS/SVG, sem dependências)
data/painel.json                        dados agregados, versionados
```

A página não usa biblioteca de gráficos: os SVGs são desenhados à mão, e a única dependência externa
são as fontes do Google Fonts.

## Licença

Código sob licença MIT. Os dados são públicos, de autoria da ANAC, e devem ser citados como tal.
