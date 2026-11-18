"""Testes de transformação usando entradas construídas apenas para teste."""
import unittest
from unittest.mock import Mock

import pandas as pd

from src.etl import SERIES, extrair_serie, montar_base_mensal, normalizar_resposta
from src.analytics import correlacao_pares


class TestETL(unittest.TestCase):
    def test_normalizacao_e_deduplicacao(self):
        df = normalizar_resposta([
            {"data": "01/01/2020", "valor": "4,50"},
            {"data": "01/01/2020", "valor": "4,25"},
            {"data": "02/01/2020", "valor": "inválido"},
        ], "teste")
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df.loc[0, "valor"], 4.25)

    def test_extracao_params_e_json(self):
        sessao = Mock()
        sessao.get.return_value.json.return_value = [
            {"data": "01/01/2020", "valor": "4,5"}
        ]
        df = extrair_serie("selic", 432, sessao)
        self.assertEqual(len(df), 1)
        self.assertEqual(sessao.get.call_args.kwargs["params"]["dataInicial"], "01/01/2020")

    def test_agregacao_e_fisher(self):
        dados = {}
        for nome in SERIES:
            valores = [1.0, 3.0] if nome == "ptax" else [10.0, 12.0]
            if nome == "ipca_12m":
                valores = [5.0, 6.0]
            dados[nome] = pd.DataFrame({
                "data": pd.to_datetime(["2020-01-10", "2020-01-25"]),
                "valor": valores,
            })
        df = montar_base_mensal(dados)
        self.assertEqual(len(df), 48)
        self.assertAlmostEqual(df.loc[0, "ptax"], 2.0)
        esperado = ((1.12 / 1.06) - 1) * 100
        self.assertAlmostEqual(df.loc[0, "juro_real"], esperado)
        self.assertTrue(pd.isna(df.loc[1, "ibc_br"]))

    def test_correlacao_com_poucas_linhas(self):
        df = pd.DataFrame({c: [1., 2., 3.] for c in
                           ["selic", "ipca_12m", "ptax", "ibc_br", "juro_real"]})
        matriz, pares = correlacao_pares(df)
        self.assertTrue(pares.empty)
        self.assertEqual(matriz.shape, (5, 5))


if __name__ == "__main__":
    unittest.main()
