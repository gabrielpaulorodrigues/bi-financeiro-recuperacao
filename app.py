"""Dashboard executivo de inteligência macroeconômica — linha BACEN/SGS.

Recorte histórico FIXO do trabalho: jan/2020 a dez/2023.
Os KPIs são históricos, não taxas vigentes na data de acesso.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import CAMPOS, conclusoes, correlacao_pares, ultimo_valor, variacao_pontos
from src.storage import carregar_bases

st.set_page_config(
    page_title="Radar Macro | Brasil 2020–2023",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=3600, show_spinner="Buscando e tratando dados oficiais do BACEN...")
def obter_dados():
    """Cache de uma hora para economizar chamadas à API SGS."""
    return carregar_bases(st)


def moeda(valor, casas=3):
    return "N/D" if valor is None or pd.isna(valor) else f"R$ {valor:.{casas}f}"


def percentual(valor):
    return "N/D" if valor is None or pd.isna(valor) else f"{valor:.2f}%"


def delta_pp(valor):
    return None if valor is None or pd.isna(valor) else f"{valor:+.2f} p.p."


def formatar_mes(d):
    return d.strftime("%m/%Y")


def resetar_filtros():
    for chave in ("periodo", "indicadores"):
        if chave in st.session_state:
            del st.session_state[chave]


st.title("Radar Macro | Inteligência Econômica")
st.caption("Brasil • séries oficiais do Banco Central (SGS) • estudo histórico: janeiro de 2020 a dezembro de 2023")

try:
    mensal, dolar_diario, origem = obter_dados()
except Exception as exc:
    st.error("Não foi possível carregar as bases de dados oficiais.")
    st.code(str(exc))
    st.info("Execute `python -m src.etl` com acesso à internet e atualize o repositório com os CSVs gerados.")
    st.stop()

mensal["data"] = pd.to_datetime(mensal["data"])
dolar_diario["data"] = pd.to_datetime(dolar_diario["data"])
mensal = mensal.sort_values("data").reset_index(drop=True)
dolar_diario = dolar_diario.sort_values("data").reset_index(drop=True)
st.caption(f"Origem efetiva: {origem}. Taxas e conclusões referem-se ao recorte selecionado, não ao dia de hoje.")

st.sidebar.header("Explorar dados")
intervalo = st.sidebar.date_input(
    "Período histórico",
    value=(date(2020, 1, 1), date(2023, 12, 31)),
    min_value=date(2020, 1, 1),
    max_value=date(2023, 12, 31),
    key="periodo",
)
disponiveis = {
    "Selic": "selic",
    "IPCA 12 meses": "ipca_12m",
    "Juro real": "juro_real",
}
indicadores = st.sidebar.multiselect(
    "Comparar na política monetária",
    options=list(disponiveis),
    default=list(disponiveis),
    key="indicadores",
)
st.sidebar.button("↺ Resetar filtros", use_container_width=True, on_click=resetar_filtros)
if len(intervalo) != 2:
    st.warning("Selecione uma data inicial e outra final.")
    st.stop()
inicio, fim = intervalo
if inicio > fim:
    st.warning("A data inicial deve anteceder a final.")
    st.stop()
filtrada = mensal.loc[mensal["data"].dt.date.between(inicio, fim)].copy()
cotacoes = dolar_diario.loc[dolar_diario["data"].dt.date.between(inicio, fim)].copy()
if filtrada.empty:
    st.warning("O filtro não contém meses com dados disponíveis.")
    st.stop()

st.subheader("Panorama econômico do período")
cols = st.columns(4)
for coluna, rotulo in zip(
    ["selic", "ipca_12m", "juro_real"],
    ["Selic meta • fim do recorte", "IPCA 12 meses • fim do recorte", "Juro real ex-post • fim do recorte"],
):
    with cols[["selic", "ipca_12m", "juro_real"].index(coluna)]:
        st.metric(
            rotulo,
            percentual(ultimo_valor(filtrada, coluna)),
            delta=delta_pp(variacao_pontos(filtrada, coluna)),
            help="Delta = último menos primeiro valor observado no recorte (pontos percentuais).",
        )
with cols[3]:
    ultimo_cambio = float(cotacoes["valor"].iloc[-1]) if not cotacoes.empty else None
    delta_cambio = (
        float(cotacoes["valor"].iloc[-1] - cotacoes["valor"].iloc[0])
        if len(cotacoes) >= 2 else None
    )
    st.metric(
        "PTAX • último dia observado",
        moeda(ultimo_cambio),
        delta=None if delta_cambio is None else f"R$ {delta_cambio:+.3f}",
        help="Delta em R$/US$: última menos primeira cotação do filtro.",
    )

questoes = conclusoes(filtrada, cotacoes)
aba_resumo, aba_juros, aba_cambio, aba_atividade, aba_correlacao, aba_dados = st.tabs([
    "Visão executiva", "Juros e inflação", "Câmbio", "Atividade", "Correlações", "Base e método"
])

with aba_resumo:
    st.markdown("### Contexto → Evidência → Decisão")
    st.write(
        "Este painel organiza a trajetória macroeconômica brasileira durante a pandemia e "
        "o ciclo posterior de elevação e redução dos juros. Os indicadores permitem "
        "comparações descritivas, não inferências causais."
    )
    for indice, titulo in [
        ("1", "Juros reais e Selic"), ("2", "Dólar acima da média"),
        ("3", "Evolução do IBC-Br"), ("4", "Relações estatísticas"),
    ]:
        st.markdown(f"**{indice}. {titulo}**")
        st.write(questoes[indice])
    st.info(
        "Uso sugerido: acompanhar exposição cambial, custos financeiros e contexto "
        "de atividade. Compare períodos e valide hipóteses antes de decidir."
    )

with aba_juros:
    st.markdown("### Pergunta 1 — Como evoluíram Selic e juros reais em 2020–2023?")
    st.write(questoes["1"])
    colunas_grafico = [disponiveis[n] for n in indicadores]
    if colunas_grafico:
        longa = filtrada.melt(
            id_vars=["data"], value_vars=colunas_grafico,
            var_name="indicador", value_name="percentual"
        )
        longa["indicador"] = longa["indicador"].map(CAMPOS)
        fig = px.line(
            longa, x="data", y="percentual", color="indicador", markers=True,
            title="Política monetária e inflação (séries mensais)",
            labels={"data": "Mês", "percentual": "Percentual (%)", "indicador": "Série"},
        )
        fig.add_hline(y=0, line_dash="dot", line_color="gray")
        fig.update_layout(legend_title_text=None, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Selecione pelo menos um indicador na barra lateral.")
    st.caption(
        "Juro real ex-post estimado pela fórmula de Fisher: "
        "[(1 + Selic/100) / (1 + IPCA_12m/100) − 1] × 100. "
        "Comparação retrospectiva, não expectativa futura."
    )

with aba_cambio:
    st.markdown("### Pergunta 2 — Quando a PTAX ficou acima de sua média histórica?")
    st.write(questoes["2"])
    if not cotacoes.empty:
        media_ptax = float(cotacoes["valor"].mean())
        fig = px.line(
            cotacoes, x="data", y="valor",
            title="Dólar PTAX venda • observações diárias",
            labels={"data": "Data", "valor": "R$/US$"},
        )
        fig.add_hline(
            y=media_ptax, line_dash="dash", line_color="#ec8a24",
            annotation_text=f"Média do filtro: R$ {media_ptax:.3f}",
        )
        fig.update_layout(hovermode="x")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Não há dados de câmbio no período filtrado.")
    st.caption("PTAX venda (SGS 1); a média de referência muda conforme o filtro de datas.")

with aba_atividade:
    st.markdown("### Pergunta 3 — Como o IBC-Br se comportou nos ciclos de juros?")
    st.write(questoes["3"])
    fig = px.line(
        filtrada, x="data", y="ibc_br", markers=True,
        title="IBC-Br dessazonalizado • série mensal",
        labels={"data": "Mês", "ibc_br": "Índice dessazonalizado"},
    )
    fig.update_layout(hovermode="x")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Comparação contextual com Selic na aba anterior. Séries em níveis podem ter "
        "tendências comuns: não se interpreta correlação como efeito causal."
    )

with aba_correlacao:
    st.markdown("### Pergunta 4 — Quais variáveis apresentam maior correlação de Pearson?")
    st.write(questoes["4"])
    matriz, pares = correlacao_pares(filtrada)
    fig = px.imshow(
        matriz, zmin=-1, zmax=1,
        color_continuous_scale="RdBu_r", text_auto=".2f",
        aspect="auto", title="Correlação de Pearson • observações mensais pareadas",
    )
    fig.update_layout(coloraxis_colorbar_title="r")
    st.plotly_chart(fig, use_container_width=True)
    if not pares.empty:
        st.dataframe(
            pares.rename(columns={"variavel_1": "Série A", "variavel_2": "Série B",
                                  "pearson": "r de Pearson", "intensidade": "|r|"}),
            use_container_width=True, hide_index=True,
        )
    st.caption(
        "Correlação calculada sobre níveis de séries mensais (pelo menos seis pares). "
        "Autocorrelação e não estacionariedade podem induzir correlação espúria."
    )

with aba_dados:
    st.markdown("### Auditoria e exportação dos dados")
    st.write(
        "Período original: 01/01/2020 a 31/12/2023. "
        "Selic: último registro mensal; PTAX: média diária no mês; "
        "demais séries: registros mensais. Nulos não são preenchidos artificialmente, "
        "exceto Selic, que mantém o último valor conhecido entre anúncios."
    )
    st.dataframe(filtrada, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar CSV filtrado", data=filtrada.to_csv(index=False).encode("utf-8-sig"),
        file_name="radar_macro_filtrado.csv", mime="text/csv",
    )
    with st.expander("Dicionário de dados"):
        st.table(pd.DataFrame([
            {"campo": "data", "tipo": "datetime", "significado": "Referência mensal"},
            *[{"campo": k, "tipo": "float", "significado": v} for k, v in CAMPOS.items()],
        ]))

st.divider()
st.caption(
    "Fonte: BCB/SGS, séries 432, 433, 13522, 1 e 24364. "
    "Exercício acadêmico, não recomendação de investimento."
)
