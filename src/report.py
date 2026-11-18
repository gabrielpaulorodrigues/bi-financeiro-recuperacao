"""Atualiza seção de achados do README exclusivamente com dados reais do ETL."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
from src.analytics import conclusoes

RAIZ = Path(__file__).resolve().parents[1]
INICIO = "<!-- RESULTADOS_START -->"
FIM = "<!-- RESULTADOS_END -->"


def gerar():
    df = pd.read_csv(RAIZ / "data" / "processed" / "macroeconomia_mensal.csv",
                     parse_dates=["data"])
    ptax = pd.read_csv(RAIZ / "data" / "processed" / "ptax_diaria.csv",
                       parse_dates=["data"])
    achados = conclusoes(df, ptax)
    valores = [
        f"- **Pergunta {numero}:** {texto}"
        for numero, texto in achados.items()
    ]
    texto = (
        "\n" + f"Base validada: **{len(df)} meses**, "
        f"**{len(ptax)} observações diárias PTAX**. "
        "Recorte histórico de 2020 a 2023.\n\n" + "\n".join(valores)
        + "\n"
    )
    destino = RAIZ / "README.md"
    readme = destino.read_text(encoding="utf-8")
    if INICIO not in readme or FIM not in readme:
        raise ValueError("Marcadores de resultados não encontrados no README")
    antes, resto = readme.split(INICIO, 1)
    _, depois = resto.split(FIM, 1)
    destino.write_text(antes + INICIO + texto + FIM + depois, encoding="utf-8")
    print("Resultados oficiais inseridos no README.")


if __name__ == "__main__":
    gerar()
