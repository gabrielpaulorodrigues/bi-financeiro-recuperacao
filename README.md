# Radar Macro | Inteligência Econômica no Brasil (2020–2023)

**Data App executivo • Visualização de Dados e Business Intelligence • Linha 3 — BACEN/SGS**

Este projeto individual investiga como a Selic, a inflação, o câmbio e o
Índice de Atividade Econômica (IBC-Br) evoluíram entre 2020 e 2023, combinando
ETL em Python, EDA em Jupyter, gráficos Plotly e aplicação Streamlit.

> **Status:** código desenvolvido; publicação, apresentação e evidências
> externas dependem de execução e validação. Não declare o trabalho entregue
> antes de verificar o dashboard público, Trello e vídeo.

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
diária para análise da trajetória do câmbio. Não se utilizam dados pessoais.

### Caminhos relativos e reprodutibilidade

Todos os caminhos são definidos com `pathlib.Path` relativamente à raiz
do repositório. O pipeline produz os arquivos em `data/raw/` e
`data/processed/`. Não há caminho absoluto da máquina do estudante.

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

Python e requests (API confiável); Pandas/NumPy (limpeza e estatística);
Plotly Express (visualização e exploração); Streamlit (dashboard publicado,
controles e KPIs); Jupyter (análise exploratória reprodutível);
Git/GitHub (revisão, branches e histórico); PostgreSQL/Supabase (opcional,
para arquitetura de banco remoto).

## 7. Resultados e evidências numéricas

**Seção preenchida automaticamente** pelo script `python -m src.report`
após a execução do ETL, usando valores **reais** das séries oficiais.

<!-- RESULTADOS_START -->
Base validada: **48 meses**, **1002 observações diárias PTAX**. Recorte histórico de 2020 a 2023.

- **Pergunta 1:** Selic: 4.50% no início do recorte e 11.75% no fim. Maior juro real ex-post observado: 10.27% em 06/2023 (Selic versus IPCA de 12 meses, Fisher).
- **Pergunta 2:** PTAX média das 1002 observações do período: R$ 5.179/US$. Em 54.1% dos dias observados a cotação ficou acima dessa média.
- **Pergunta 3:** O IBC-Br passou de 97.58 para 104.93 no recorte (+7.53%). A comparação visual com Selic é descritiva; não prova que os juros causaram a variação da atividade.
- **Pergunta 4:** Maior correlação absoluta de Pearson (níveis mensais): Selic meta (% a.a.) × Juro real ex-post (% a.a.) = +0.807. A tendência comum e a autocorrelação podem produzir associações espúrias; não há inferência causal.
<!-- RESULTADOS_END -->

Visualizações implementadas: (1) linhas de Selic, IPCA e juros reais;
(2) série PTAX e sua média; (3) linha IBC-Br; (4) heatmap Pearson.

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

- **Streamlit Community Cloud:** [INSERIR LINK PÚBLICO DA APLICAÇÃO]
- **Vídeo pitch (3–5 minutos):** [INSERIR LINK PÚBLICO DO VÍDEO]
- **Capturas da aplicação:** [ADICIONAR PRINTS REAIS APÓS DEPLOY]

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

Para executar o notebook: `jupyter notebook notebooks/eda_exploratoria.ipynb`
(instale `notebook` se necessário). O notebook deve ser salvo com células
executadas e gráficos visíveis para atender ao critério eliminatório.

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

- **Quadro público Trello:** [INSERIR LINK REAL]
- **Print do Trello com cards concluídos:** [INSERIR IMAGEM REAL]
- **Guia de cards:** [docs/trello_kanban.md](docs/trello_kanban.md)
- **Roteiro do pitch:** [docs/roteiro_pitch.md](docs/roteiro_pitch.md)
- **Deploy:** [INSERIR LINK REAL DO STREAMLIT]
- **Vídeo:** [INSERIR LINK REAL DO PITCH]

O quadro deve mostrar Backlog, A Fazer, Em Andamento e Concluído,
com tarefas efetivamente movimentadas (somente uma em andamento).

## 14. Autoria e créditos

**Autor:** Gabriel Paulo Rodrigues — projeto acadêmico individual.
Repositório: [GitHub](https://github.com/gabrielpaulorodrigues/bi-financeiro-recuperacao).

**Referências:** Banco Central do Brasil (SGS e API pública);
documentação oficial de [Streamlit](https://docs.streamlit.io/),
[Pandas](https://pandas.pydata.org/docs/),
[Plotly](https://plotly.com/python/) e
[Requests](https://requests.readthedocs.io/).

A autoria, revisão das análises, apresentação e entrega final devem
ser verificadas pelo estudante.
