# Radar Macro | Inteligência Econômica no Brasil (2020–2023)

**Visualização de Dados e Business Intelligence — Linha 3 (BACEN/SGS)**

O Radar Macro reúne indicadores econômicos do Brasil entre 2020 e 2023:
Selic, IPCA, dólar PTAX e IBC-Br. A coleta e o tratamento dos dados foram
organizados em Python, com análise exploratória no Jupyter e visualizações
interativas no Streamlit.

## 1. Resumo executivo

O Brasil passou por pandemia, elevação de preços e mudanças de política
monetária. Um painel com dados oficiais harmonizados torna o contexto histórico
mais acessível, ajuda a observar movimentos coincidentes e evita confundir
associação com causalidade.

## 2. Problema de negócio e perguntas

**Como juros, inflação, câmbio e atividade se relacionaram no período?**

1. Como Selic e juro real ex-post evoluíram, e quando este foi maior?
2. Quando o dólar PTAX ficou acima da média histórica do quadriênio?
3. Como o IBC-Br se comportou durante movimentos de alta e baixa da Selic?
4. Quais pares tiveram as maiores correlações de Pearson?

O dashboard apresenta resposta textual baseada nos dados para cada pergunta,
junto dos gráficos interativos.

## 3. Fonte dos dados e licença

**Fonte primária:** [Sistema Gerenciador de Séries Temporais do Banco Central do Brasil (SGS)](https://www.bcb.gov.br/estatisticas/sgs).
Consulta programática via [API pública SGS](https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial=01/01/2020&dataFinal=31/12/2023).
Séries: **432** Selic Meta, **433** IPCA mensal, **13522** IPCA em 12 meses,
**1** PTAX dólar americano venda e **24364** IBC-Br dessazonalizado.

**Janela fixa:** 01/01/2020 a 31/12/2023 (estudo histórico, não indicadores atuais).
Dados públicos oficiais do BCB; uso sujeito às condições de reutilização
indicadas pelo fornecedor, com atribuição da fonte.

## 4. Pipeline ETL e modelagem

`src/etl.py` executa: consumo HTTPS limitado ao recorte, retentativas,
validação do JSON, coerção de número e data, remoção de registros inválidos
e datas duplicadas, agregação para frequência mensal, cálculo de indicadores
e exportação de CSVs brutos e tratados.

- **Selic:** último dado publicado por mês, com continuidade da meta quando não alterada.
- **PTAX:** média das cotações diárias disponíveis no mês; série diária
  conservada para o gráfico de câmbio.
- **IPCA, IPCA 12m, IBC-Br:** valores mensais reportados pelo SGS, sem interpolação.
- **Juro real ex-post:** `((1 + selic/100)/(1 + ipca_12m/100) - 1) × 100`.

**Modelo:** tabela fato `macroeconomia_mensal`, uma linha por mês,
com variáveis econômicas como medidas. `ptax_diaria` preserva granularidade
diária para análise da trajetória do câmbio.

### Caminhos relativos e reprodutibilidade

Todos os caminhos são definidos com `pathlib.Path` relativamente à raiz
do repositório. O pipeline produz os arquivos em `data/raw/` e
`data/processed/`.

## 5. Dicionário de dados

| Campo | Tipo | Significado / unidade |
| --- | --- | --- |
| data | datetime | Mês de referência (ou data da PTAX diária) |
| selic | float | Meta Selic de fim do mês, % ao ano (SGS 432) |
| ipca_mensal | float | IPCA no mês, % (SGS 433) |
| ipca_12m | float | IPCA acumulado em 12 meses, % (SGS 13522) |
| ptax | float | Média mensal da PTAX venda, R$/US$ (SGS 1) |
| ibc_br | float | Índice de atividade IBC-Br dessazonalizado (SGS 24364) |
| juro_real | float | Juro real ex-post anualizado aproximado via Fisher, % |

## 6. Tecnologias e justificativa

| Tecnologia | Utilização |
| --- | --- |
| Python e Requests | Consulta à API SGS |
| Pandas e NumPy | Tratamento dos dados e cálculos estatísticos |
| Plotly | Gráficos interativos |
| Streamlit | Interface, indicadores e filtros |
| Jupyter Notebook | Análise exploratória |
| Git e GitHub | Controle de versões |
| PostgreSQL | Conexão opcional com banco de dados |

## 7. Resultados e evidências numéricas

Os resultados abaixo foram calculados com os dados do Banco Central
após a execução do ETL. O script `src/report.py` atualiza esta seção.

<!-- RESULTADOS_START -->
_Aguardando geração e validação do conjunto de dados oficial. Não há
resultados numéricos inventados._
<!-- RESULTADOS_END -->

O painel apresenta a evolução de Selic, IPCA e juros reais, o histórico
da PTAX com sua média, o índice IBC-Br e uma matriz de correlação.

## 8. Discussão e limitações

- O recorte é histórico (2020–2023) e não informa a taxa Selic atual.
- Dados mensais não preservam cada variação intramês.
- Correlação em séries temporais pode ser espúria por tendência e
  autocorrelação, e não prova relação causal.
- Juro real é uma aproximação retrospectiva com inflação observada em 12 meses.
- Nulos são documentados no notebook; choques reais não são descartados só
  por serem outliers estatísticos.

## 9. Aplicação profissional

O painel pode apoiar análise de cenários, relatórios de controladoria,
revisão de exposição cambial e discussão contextual de custo de capital.
Decisões devem considerar fontes adicionais, defasagens e modelos
econométricos antes de alegar impactos.

## 10. Aplicação e demonstração

- **Aplicação Streamlit:** [Radar Macro](https://bi-financeiro-recuperacao-emihmxehu9appqpbps8pn4s.streamlit.app)
- **Apresentação em vídeo:** a incluir
- **Capturas do painel:** a incluir

## 11. Executar localmente

```bash
git clone https://github.com/gabrielpaulorodrigues/bi-financeiro-recuperacao.git
cd bi-financeiro-recuperacao
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m src.etl
python -m src.report
python -m unittest discover -s tests -v
streamlit run app.py
```

Para abrir a análise exploratória:
`jupyter notebook notebooks/eda_exploratoria.ipynb`
(instale o Jupyter Notebook, se necessário).

**Opcional:** criar `.streamlit/secrets.toml` com uma conexão `postgresql`
válida, conforme `.streamlit/secrets.toml.example`. Em ambiente sem
PostgreSQL, a aplicação consulta a API; em indisponibilidade, recorre a
CSVs tratados já existentes. Para publicar no Streamlit Cloud, configure
entrypoint `app.py`, branch `main` e dependências `requirements.txt`.

## 12. Estrutura do projeto

```text
data/raw/                  Séries originais em CSV após o ETL
data/processed/            Base mensal, PTAX diária e metadados
notebooks/eda_exploratoria.ipynb
src/etl.py                 Extração, limpeza, validação e harmonização
src/analytics.py           Métricas, correlação e conclusões
src/storage.py             PostgreSQL opcional / API / CSV de contingência
src/report.py              Evidências numéricas para o README
tests/test_etl.py          Testes determinísticos (mockados)
.streamlit/config.toml     Tema executivo
.streamlit/secrets.toml.example
app.py                     Interface Streamlit
requirements.txt
README.md
docs/trello_kanban.md
docs/roteiro_pitch.md
```

## 13. Gestão ágil e links do projeto

- **Quadro Trello:** a incluir
- **Captura do quadro:** a incluir
- [Planejamento das tarefas](docs/trello_kanban.md)
- [Roteiro da apresentação](docs/roteiro_pitch.md)

## 14. Autoria e créditos

**Responsável pelo projeto:** Gabriel Paulo Rodrigues.
Repositório: [GitHub](https://github.com/gabrielpaulorodrigues/bi-financeiro-recuperacao).

**Referências:** Banco Central do Brasil (SGS e API pública);
documentação oficial de [Streamlit](https://docs.streamlit.io/),
[Pandas](https://pandas.pydata.org/docs/),
[Plotly](https://plotly.com/python/) e
[Requests](https://requests.readthedocs.io/).

