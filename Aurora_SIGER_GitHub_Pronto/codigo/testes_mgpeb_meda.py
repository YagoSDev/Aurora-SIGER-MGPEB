"""Testes do prototipo MGPEB (somente biblioteca padrao unittest)."""
import unittest

from mgpeb_aurora_meda import (
    criar_sistema, insertion_sort, busca_linear, busca_binaria_id,
    reorganizar_fila, avaliar_pouso, processar_proximo, desfazer_ultimo,
    altura, cadastrar_modulo, recolocar_em_espera,
    carregar_referencias_meda, aplicar_observacao_meda, temperatura_superficie_meda,
)


class TestesMGPEB(unittest.TestCase):
    def setUp(self):
        self.sistema = criar_sistema()

    def test_fila_inicial_pela_chegada(self):
        self.assertEqual(self.sistema["fila"], ["M04", "M03", "M01", "M02", "M05"])

    def test_ordenar_prioridade(self):
        reorganizar_fila(self.sistema, "prioridade")
        self.assertEqual(self.sistema["fila"], ["M01", "M02", "M03", "M04", "M05"])

    def test_busca_linear(self):
        self.assertEqual(busca_linear(self.sistema["modulos"], "tipo", "medico")[0]["id"], "M03")

    def test_busca_binaria(self):
        self.assertEqual(busca_binaria_id(self.sistema["modulos"], "M05")["nome"], "Laboratorio cientifico")
        self.assertIsNone(busca_binaria_id(self.sistema["modulos"], "M99"))

    def test_insertion_sort_nao_muda_entrada(self):
        antes = [m["id"] for m in self.sistema["modulos"]]
        ordenados = insertion_sort(self.sistema["modulos"], "combustivel")
        self.assertEqual(ordenados[0]["id"], "M04")
        self.assertEqual([m["id"] for m in self.sistema["modulos"]], antes)

    def test_regra_sensores_redundantes_or(self):
        m = busca_binaria_id(self.sistema["modulos"], "M03")
        autorizado, motivos = avaliar_pouso(m, self.sistema["condicoes"])
        self.assertTrue(autorizado)
        self.assertEqual(motivos, [])

    def test_pouso_na_fila_e_area_ocupada(self):
        reorganizar_fila(self.sistema, "prioridade")
        modulo, resultado, _ = processar_proximo(self.sistema)
        self.assertEqual(modulo["id"], "M01")
        self.assertEqual(resultado, "POUSO AUTORIZADO")
        self.assertFalse(self.sistema["condicoes"]["area_livre"])
        modulo, resultado, motivos = processar_proximo(self.sistema)
        self.assertEqual(modulo["id"], "M02")
        self.assertEqual(resultado, "POUSO ADIADO - EM ESPERA")
        self.assertIn("Area de pouso ocupada", motivos)
        self.assertIn("M02", self.sistema["espera"])

    def test_combustivel_insuficiente_gera_alerta(self):
        modulo, resultado, motivos = processar_proximo(self.sistema)
        self.assertEqual(modulo["id"], "M04")
        self.assertEqual(resultado, "POUSO BLOQUEADO - ALERTA")
        self.assertIn("Combustivel abaixo do minimo simulado", motivos)
        self.assertIn("M04", self.sistema["alertas"])

    def test_integridade_incorreta(self):
        m = busca_binaria_id(self.sistema["modulos"], "M05")
        autorizado, motivos = avaliar_pouso(m, self.sistema["condicoes"])
        self.assertFalse(autorizado)
        self.assertIn("Integridade estrutural comprometida", motivos)

    def test_altitude_influencia_autorizacao(self):
        m = busca_binaria_id(self.sistema["modulos"], "M01")
        self.sistema["condicoes"]["tempo_descida"] = 5
        autorizado, motivos = avaliar_pouso(m, self.sistema["condicoes"])
        self.assertFalse(autorizado)
        self.assertIn("Modulo ainda acima da altitude de aproximacao", motivos)
        self.assertEqual(altura(5), 1500)
        self.assertEqual(altura(8), 0)

    def test_recolocar_em_espera(self):
        reorganizar_fila(self.sistema, "prioridade")
        processar_proximo(self.sistema)
        processar_proximo(self.sistema)
        self.assertTrue(recolocar_em_espera(self.sistema, "M02"))
        self.assertEqual(self.sistema["fila"][-1], "M02")
        self.assertNotIn("M02", self.sistema["espera"])
        self.assertFalse(recolocar_em_espera(self.sistema, "M02"))
        # A operacao de espera ja foi encerrada; desfazer nao a remove da fila.
        self.assertEqual(desfazer_ultimo(self.sistema), "M01")

    def test_desfazer_ultimo(self):
        processar_proximo(self.sistema)
        self.assertEqual(desfazer_ultimo(self.sistema), "M04")
        self.assertNotIn("M04", self.sistema["alertas"])
        self.assertEqual(self.sistema["fila"][0], "M04")

    def test_meda_csv_proveniencia(self):
        registros = carregar_referencias_meda()
        self.assertEqual(len(registros), 4)
        self.assertEqual({r["id"] for r in registros}, {"MEDA01", "MEDA02", "MEDA03", "MEDA04"})
        self.assertTrue(all("jpl.nasa.gov" in r["fonte_url"] for r in registros))

    def test_pressao_meda_real_em_cenario(self):
        parametro, valor = aplicar_observacao_meda(self.sistema, "MEDA03")
        self.assertEqual((parametro, valor), ("pressao_pa", 718))
        self.assertIn("NASA/JPL", self.sistema["condicoes"]["origem"][parametro])
        self.assertEqual(self.sistema["condicoes"]["temperatura_solo_c"], -30.0)

    def test_rajada_em_ms_para_kmh(self):
        parametro, valor = aplicar_observacao_meda(self.sistema, "MEDA04")
        self.assertEqual(parametro, "vento")
        self.assertAlmostEqual(valor, 36.0)

    def test_meda_registro_inexistente(self):
        with self.assertRaises(KeyError):
            aplicar_observacao_meda(self.sistema, "MEDA99")

    def test_pressao_fora_faixa_didatica(self):
        modulo = busca_binaria_id(self.sistema["modulos"], "M01")
        self.sistema["condicoes"]["pressao_pa"] = 490
        autorizado, motivos = avaliar_pouso(modulo, self.sistema["condicoes"])
        self.assertFalse(autorizado)
        self.assertIn("Pressao fora do intervalo didatico", motivos)

    def test_temperatura_fora_faixa_didatica(self):
        modulo = busca_binaria_id(self.sistema["modulos"], "M01")
        self.sistema["condicoes"]["temperatura_solo_c"] = -100
        autorizado, motivos = avaliar_pouso(modulo, self.sistema["condicoes"])
        self.assertFalse(autorizado)
        self.assertIn("Temperatura do solo fora do intervalo didatico", motivos)

    def test_modelo_historico_linear(self):
        self.assertAlmostEqual(temperatura_superficie_meda(0), -20.0)
        self.assertAlmostEqual(temperatura_superficie_meda(15), -22.8)
        self.assertAlmostEqual(temperatura_superficie_meda(30), -25.6)
        with self.assertRaises(ValueError):
            temperatura_superficie_meda(31)

    def test_cadastro_duplicado(self):
        dados = self.sistema["modulos"][0].copy()
        with self.assertRaises(ValueError):
            cadastrar_modulo(self.sistema, dados)


if __name__ == "__main__":
    unittest.main()
