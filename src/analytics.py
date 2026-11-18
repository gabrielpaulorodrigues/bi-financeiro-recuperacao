"""Cálculos explícitos, estatística descritiva e insights sem causalidade indevida."""
from __future__ import annotations

import numpy as np
import pandas as pd

CAMPOS = {
    "selic": "Selic meta (% a.a.)",
    "ipca_mensal": "IPCA mensal (%)",
    "ipca_12m": "IPCA acumulado 12 meses (%)",
    "ptax": "PTAX média do mês (R$/US$)",
    "ibc_br": "IBC-Br dessazonalizado (índice)",
    "juro_real": "Juro real ex-post (% a.a.)",
}


def ultimo_valor(base: pd.DataFrame, coluna: str) -> float | None:
    valores = base[coluna].dropna()
    return float(valores.iloc[-1]) if not valores.empty else None


def variacao_pontos(base: pd.DataFrame, coluna: str) -> float | None:
    valores = base[coluna].dropna()
    return float(valores.iloc[-1] - valores.iloc[0]) if len(valores) > 1 else None


def correlacao_pares(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Correlação Pearson apenas de observações pareadas disponíveis."""
    colunas = ["selic", "ipca_12m", "ptax", "ibc_br", "juro_real"]
    correlacao = base[colunas].corr(method="pearson", min_periods=6)
    pares = (
        correlacao.where(np.triu(np.ones(correlacao.shape), k=1).astype(bool))
        .stack()
        .reset_index()
    )
    pares.columns = ["variavel_1", "variavel_2", "pearson"]
    pares["intensidade"] = pares["pearson"].abs()
    return correlacao, pares.sort_values("intensidade", ascending=False)


def conclusoes(base: pd.DataFrame, ptax_diaria: pd.DataFrame) -> dict[str, str]:
    """Responde às quatro perguntas com números calculados do recorte ativo."""
    if base.empty:
        return {str(i): "Não há dados suficientes para este filtro." for i in range(1, 5)}

    selic = base.dropna(subset=["selic"])
    juro = base.dropna(subset=["juro_real"])
    selic_txt = (
        f"Selic: {selic.iloc[0]['selic']:.2f}% no início do recorte e "
        f"{selic.iloc[-1]['selic']:.2f}% no fim."
    ) if not selic.empty else "Sem dados de Selic."
    if not juro.empty:
        maior = juro.loc[juro["juro_real"].idxmax()]
        selic_txt += (
            f" Maior juro real ex-post observado: {maior['juro_real']:.2f}% "
            f"em {maior['data']:%m/%Y} (Selic versus IPCA de 12 meses, Fisher)."
        )

    if not ptax_diaria.empty:
        media = ptax_diaria["valor"].mean()
        proporcao = (ptax_diaria["valor"] > media).mean() * 100
        dolar_txt = (
            f"PTAX média das {len(ptax_diaria)} observações do período: "
            f"R$ {media:.3f}/US$. Em {proporcao:.1f}% dos dias observados "
            "a cotação ficou acima dessa média."
        )
    else:
        dolar_txt = "Sem cotações PTAX para o período."

    atividade = base.dropna(subset=["ibc_br"])
    if len(atividade) >= 2:
        inicio, fim = atividade.iloc[0], atividade.iloc[-1]
        dif = (fim["ibc_br"] / inicio["ibc_br"] - 1) * 100
        atividade_txt = (
            f"O IBC-Br passou de {inicio['ibc_br']:.2f} para "
            f"{fim['ibc_br']:.2f} no recorte ({dif:+.2f}%). "
            "A comparação visual com Selic é descritiva; não prova que os juros "
            "causaram a variação da atividade."
        )
    else:
        atividade_txt = "Série IBC-Br insuficiente para medir a variação."

    _, pares = correlacao_pares(base)
    if not pares.empty:
        par = pares.iloc[0]
        correlacao_txt = (
            f"Maior correlação absoluta de Pearson (níveis mensais): "
            f"{CAMPOS[par['variavel_1']]} × {CAMPOS[par['variavel_2']]} = "
            f"{par['pearson']:+.3f}. A tendência comum e a autocorrelação "
            "podem produzir associações espúrias; não há inferência causal."
        )
    else:
        correlacao_txt = "Amostra insuficiente para calcular correlações."

    return {"1": selic_txt, "2": dolar_txt, "3": atividade_txt,
            "4": correlacao_txt}
