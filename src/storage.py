"""Camada de dados: Postgres (opcional), API SGS e contingência CSV."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.etl import PROCESSED_DIR, executar_etl

ARQUIVO_MENSAL = PROCESSED_DIR / "macroeconomia_mensal.csv"
ARQUIVO_PTAX = PROCESSED_DIR / "ptax_diaria.csv"


def ler_csv() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Abre bases já tratadas, sem depender do diretório de execução."""
    mensal = pd.read_csv(ARQUIVO_MENSAL, parse_dates=["data"])
    ptax = pd.read_csv(ARQUIVO_PTAX, parse_dates=["data"])
    return mensal, ptax


def carregar_bases(st) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Usa Postgres se configurado; caso contrário API, e CSV em falha.

    Nunca persiste credenciais; Secrets são lidos apenas pela API do Streamlit.
    """
    try:
        configuracoes = st.secrets.get("connections", {})
        if "postgresql" in configuracoes:
            conexao = st.connection("postgresql", type="sql")
            mensal = conexao.query(
                "SELECT data, selic, ipca_mensal, ipca_12m, ptax, ibc_br, juro_real "
                "FROM macroeconomia_mensal ORDER BY data",
                ttl=3600,
            )
            if not mensal.empty and ARQUIVO_PTAX.is_file():
                _, dolar = ler_csv()
                mensal["data"] = pd.to_datetime(mensal["data"])
                return mensal, dolar, "PostgreSQL (Supabase) + série PTAX CSV"
    except (Exception) as exc:
        # Configuração de DB é opcional; não impedir leitura de fontes públicas.
        erro_banco = str(exc)
    else:
        erro_banco = ""

    try:
        mensal, ptax = executar_etl()
        return mensal, ptax, "API SGS do Banco Central (dados consultados nesta sessão)"
    except Exception as exc:
        if ARQUIVO_MENSAL.is_file() and ARQUIVO_PTAX.is_file():
            mensal, ptax = ler_csv()
            return mensal, ptax, (
                "CSV de contingência — coleta online indisponível; "
                "pode não conter atualizações."
            )
        detalhe = f" Banco: {erro_banco}." if erro_banco else ""
        raise RuntimeError(
            "Não foi possível consultar o SGS nem abrir arquivos CSV de contingência."
            f" API: {exc}.{detalhe} Rode 'python -m src.etl' em ambiente com internet "
            "para gerar data/processed/*.csv, depois publique esses dados."
        ) from exc
