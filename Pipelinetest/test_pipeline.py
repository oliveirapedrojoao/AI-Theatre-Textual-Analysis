"""Testes do pipeline — correm sem API, sobre a amostra em `exemplos/`."""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from presepios.config import Config                     # noqa: E402
from presepios.esquemas import ESQUEMAS                 # noqa: E402
from presepios.extracao import extrair_seccoes, extrair_tabelas  # noqa: E402
from presepios.texto import carregar_peca, normalizar, segmentar  # noqa: E402
from presepios.validacao import validar                 # noqa: E402

EXEMPLOS = RAIZ / "exemplos"
PECA = EXEMPLOS / "entremez_exemplo.txt"
RESPOSTAS = EXEMPLOS / "respostas_exemplo"


class TesteTexto(unittest.TestCase):
    def setUp(self):
        self.peca = carregar_peca(PECA)

    def test_numeracao_alinha_com_as_linhas(self):
        numeradas = self.peca.texto_numerado.split("\n")
        self.assertEqual(len(numeradas), self.peca.n_linhas)
        self.assertTrue(numeradas[11].startswith("[L0012] BRAZ."))
        self.assertEqual(self.peca.linha(12), numeradas[11][8:])

    def test_deteccao_de_personagens_e_estrutura(self):
        self.assertEqual(
            self.peca.personagens_detectadas,
            ["ANJO", "BRAZ", "GIL", "MARIANNA", "SACRISTÃO"],
        )
        self.assertIn((8, "CENA I"), self.peca.marcos_estrutura)
        self.assertEqual(self.peca.folios[0], (3, "[fl. 1r]"))

    def test_normalizacao_ignora_ortografia_mas_nao_altera_o_original(self):
        self.assertEqual(normalizar("Ó ceo se abrio"), "o ceo se abrio")
        self.assertEqual(normalizar("thuribulo[sic]"), "thuribulo")
        self.assertIn("Ó compadre Gil", self.peca.texto_bruto)

    def test_segmentacao_cobre_a_peca_sem_lacunas(self):
        segs = segmentar(self.peca, max_linhas=30)
        self.assertGreater(len(segs), 1)
        self.assertEqual(segs[0].linha_inicio, 1)
        self.assertEqual(segs[-1].linha_fim, self.peca.n_linhas)
        for a, b in zip(segs, segs[1:]):
            self.assertEqual(b.linha_inicio, a.linha_fim + 1)

    def test_ficheiro_ausente_interrompe(self):
        with self.assertRaises(FileNotFoundError):
            carregar_peca(EXEMPLOS / "nao_existe.txt")


class TesteExtraccao(unittest.TestCase):
    def setUp(self):
        self.r1 = (RESPOSTAS / "ronda1.md").read_text("utf-8")
        self.r2 = (RESPOSTAS / "ronda2.md").read_text("utf-8")

    def test_seccoes(self):
        s = extrair_seccoes(self.r1)
        self.assertIn("personagens", s)
        self.assertIn("vernaculo_recursos", s)
        self.assertIn("limitacoes", s)
        self.assertIn("BRAZ", s["personagens"])

    def test_todas_as_tabelas_sao_extraidas(self):
        tabelas, avisos = extrair_tabelas(self.r2)
        for nome, esq in ESQUEMAS.items():
            self.assertIn(nome, tabelas)
            self.assertTrue(tabelas[nome], f"{esq.ficheiro} veio vazia")
        self.assertEqual(len(tabelas["recursos_expressivos"]), 32)
        self.assertEqual(len(tabelas["personagens"]), 5)
        self.assertEqual(len(tabelas["relacoes"]), 14)
        self.assertEqual([a for a in avisos if "em falta" in a], [])

    def test_campos_com_virgulas_sobrevivem_ao_csv(self):
        tabelas, _ = extrair_tabelas(self.r2)
        r011 = next(r for r in tabelas["recursos_expressivos"] if r["id"] == "R011")
        self.assertEqual(r011["citacao"], "Tenho na boca o que a vida me poz: sal, filho, muito sal")
        self.assertEqual(r011["personagem"], "MARIANNA")


class TesteValidacao(unittest.TestCase):
    def setUp(self):
        peca = carregar_peca(PECA)
        tabelas, avisos = extrair_tabelas((RESPOSTAS / "ronda2.md").read_text("utf-8"))
        self.tabelas, self.rel = validar(tabelas, peca, Config(peca=str(PECA)), avisos)

    def test_cotejo_apanha_a_citacao_inventada(self):
        m = self.rel.metricas
        self.assertEqual(m["citacoes_testadas"], 32)
        self.assertEqual(m["citacoes_nao_encontradas"], 1)
        self.assertEqual(m["citacoes_deslocadas"], 1)
        recs = {r["id"]: r for r in self.tabelas["recursos_expressivos"]}
        self.assertEqual(recs["R031"]["_verificacao"], "não encontrada")
        self.assertEqual(recs["R032"]["_verificacao"], "deslocada")
        self.assertEqual(recs["R001"]["_verificacao"], "verificada")
        self.assertFalse(self.rel.valido)   # a citação inventada é erro, não aviso

    def test_localizacao_fora_do_intervalo_gera_aviso(self):
        self.assertTrue(any("L0090" in a for a in self.rel.avisos))

    def test_frequencias_sao_recalculadas(self):
        freq = {r["tipo_recurso"]: int(r["n_ocorrencias"])
                for r in self.tabelas["frequencias_recursos"]}
        reais = {}
        for r in self.tabelas["recursos_expressivos"]:
            reais[r["tipo_recurso"]] = reais.get(r["tipo_recurso"], 0) + 1
        self.assertEqual(freq, reais)
        self.assertEqual(freq["metáfora"], 11)   # a resposta declarava 9
        self.assertTrue(any("recalculada" in n for n in self.rel.notas))

    def test_integridade_referencial(self):
        nomes = {p["personagem"] for p in self.tabelas["personagens"]}
        for r in self.tabelas["relacoes"]:
            self.assertIn(r["origem"], nomes)
            self.assertIn(r["destino"], nomes)
        for r in self.tabelas["recursos_expressivos"]:
            if r["personagem"] and not r["personagem"].startswith("("):
                self.assertIn(r["personagem"], nomes)

    def test_grau_de_certeza_normalizado(self):
        for v in self.tabelas["vernaculo"]:
            self.assertIn(v["grau_certeza"], ("seguro", "provável", "hipotético"))


class TestePrompts(unittest.TestCase):
    def test_prompts_compilam_e_contem_o_essencial(self):
        from presepios.prompts import SISTEMA, prompt_ronda1, prompt_ronda2

        peca = carregar_peca(PECA)
        cfg = Config(titulo="Amostra", datacao="c. 1770", proveniencia="BPE",
                     genero="presépio teatral", peca=str(PECA))
        r1 = prompt_ronda1(cfg, peca.resumo(), peca.personagens_detectadas)
        r2 = prompt_ronda2(cfg)
        self.assertIn("[L0001]", SISTEMA)
        self.assertIn("Não normalizes a ortografia", SISTEMA)
        for campo in ("Amostra", "c. 1770", "BPE", "presépio teatral"):
            self.assertIn(campo, r1)
        self.assertIn("<personagens>", r1)
        self.assertIn("BRAZ", r1)                      # rubricas detectadas
        for esq in ESQUEMAS.values():
            self.assertIn(esq.ficheiro, r2)
            self.assertIn(esq.cabecalho, r2)
        self.assertIn("<analise_ronda1>", prompt_ronda2(cfg, "análise prévia"))

    def test_cli_importa_sem_erros(self):
        from presepios import cli
        with self.assertRaises(SystemExit):
            cli.main(["--versao"])


class TesteDashboard(unittest.TestCase):
    def test_html_autocontido_e_sem_dependencias(self):
        import tempfile
        from presepios.dashboard import gerar_dashboard

        peca = carregar_peca(PECA)
        cfg = Config(titulo="Amostra", peca=str(PECA))
        tabelas, avisos = extrair_tabelas((RESPOSTAS / "ronda2.md").read_text("utf-8"))
        tabelas, rel = validar(tabelas, peca, cfg, avisos)
        seccoes = extrair_seccoes((RESPOSTAS / "ronda1.md").read_text("utf-8"))
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "x.html"
            gerar_dashboard(cfg, tabelas, rel, seccoes, destino)
            html = destino.read_text("utf-8")
        self.assertNotIn("__DADOS_JSON__", html)
        self.assertNotIn("localStorage", html)
        self.assertNotIn("src=\"http", html)      # nenhum script externo
        self.assertNotIn("\x00", html)
        self.assertIn("R001", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
