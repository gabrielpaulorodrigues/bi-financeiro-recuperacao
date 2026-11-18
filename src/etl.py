"""ETL reproduzível das cinco séries oficiais BACEN/SGS (2020–2023).

Todas as operações em disco usam pathlib e caminhos relativos ao projeto.
Sem preenchimento arbitrário de séries mensais: ausência permanece NaN.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Mapping

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
START = "01/01/2020"
END = "31/12/2023"
SERIES: Mapping[str, int] = {
    "selic": 432,
    "ipca_mensal": 433,
    "ipca_12m": 13522,
    "ptax": 1,
    "ibc_br": 24364,
}
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


def criar_sessao() -> requests.Session:
    """Configura timeout (na chamada), tentativas e intervalo entre requisições."""
    sessao = requests.Session()
    politica = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    sessao.mount("https://", HTTPAdapter(max_retries=politica))
    sessao.headers.update({"User-Agent": "BI-Financeiro-Academico/1.0"})
    return sessao


def normalizar_resposta(registros: list[dict], nome: str) -> pd.DataFrame:
    """Converte datas brasileiras e valores do SGS para tipos válidos."""
    if not isinstance(registros, list) or not registros:
        raise ValueError(f"SGS {nome}: retorno vazio ou inválido")
    df = pd.DataFrame(registros)
    if not {"data", "valor"}.issubset(df.columns):
        raise ValueError(f"SGS {nome}: colunas esperadas ausentes")
    df = df.loc[:, ["data", "valor"]].copy()
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df["valor"] = pd.to_numeric(
        df["valor"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    df = df.dropna(subset=["data", "valor"]).drop_duplicates(
        subset="data", keep="last"
    ).sort_values("data").reset_index(drop=True)
    if df.empty:
        raise ValueError(f"SGS {nome}: sem observações numéricas válidas")
    return df


def extrair_serie(nome: str, codigo: int, sessao: requests.Session | None = None,
                  inicio: str = START, fim: str = END) -> pd.DataFrame:
    """Faz uma consulta restrita ao intervalo da atividade (quatro anos)."""
    session = sessao or criar_sessao()
    resposta = session.get(
        URL.format(codigo=codigo),
        params={"formato": "json", "dataInicial": inicio, "dataFinal": fim},
        timeout=(8, 35),
    )
    resposta.raise_for_status()
    return normalizar_resposta(resposta.json(), nome)


def montar_base_mensal(series: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Harmoniza frequências distintas por mês, evitando falsa correlação diária.

    Selic: último registro válido do mês (taxa meta de fim de mês).
    PTAX: média das observações diárias do mês.
    IPCA e IBC-Br: registro mensal, sem interpolação.
    Juro real ex-post: fórmula exata de Fisher com IPCA acumulado 12m.
    """
    faltantes = set(SERIES) - set(series)
    if faltantes:
        raise ValueError(f"Séries ausentes: {', '.join(sorted(faltantes))}")
    meses = pd.date_range("2020-01-01", "2023-12-01", freq="MS")
    mensal = pd.DataFrame({"data": meses}).set_index("data")
    for nome in SERIES:
        serie = series[nome].set_index("data")["valor"].sort_index()
        if nome == "ptax":
            agregado = serie.resample("MS").mean()
        else:
            agregado = serie.resample("MS").last()
        mensal[nome] = agregado.reindex(meses)

    # A Selic é taxa-meta e pode não ter novo registro num mês.
    mensal["selic"] = mensal["selic"].ffill()
    mensal["juro_real"] = (
        ((1 + mensal["selic"] / 100) / (1 + mensal["ipca_12m"] / 100)) - 1
    ) * 100
    return mensal.reset_index()


def salvar_bases(series: Mapping[str, pd.DataFrame],
                 mensal: pd.DataFrame) -> None:
    """Persiste base bruta e tratada para contingência sem credenciais."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for nome, frame in series.items():
        frame.to_csv(RAW_DIR / f"{nome}.csv", index=False, date_format="%Y-%m-%d")
    mensal.to_csv(PROCESSED_DIR / "macroeconomia_mensal.csv",
                  index=False, date_format="%Y-%m-%d")
    series["ptax"].to_csv(PROCESSED_DIR / "ptax_diaria.csv",
                         index=False, date_format="%Y-%m-%d")
    (PROCESSED_DIR / "metadata.json").write_text(
        json.dumps({
            "origem": "Banco Central do Brasil — SGS",
            "series": SERIES,
            "inicio": START,
            "fim": END,
            "executado_em_utc": datetime.now().astimezone().isoformat(),
            "observacoes_mensais": len(mensal),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def executar_etl(sessao: requests.Session | None = None
                 ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Executa o pipeline integral e retorna (mensal, câmbio diário)."""
    cliente = sessao or criar_sessao()
    conjuntos = {
        nome: extrair_serie(nome, codigo, sessao=cliente)
        for nome, codigo in SERIES.items()
    }
    mensal = montar_base_mensal(conjuntos)
    salvar_bases(conjuntos, mensal)
    return mensal, conjuntos["ptax"]


if __name__ == "__main__":
    base, dolar = executar_etl()
    print(f"ETL concluído: {len(base)} meses e {len(dolar)} cotações PTAX.")
