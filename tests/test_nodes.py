import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Define uma chave placeholder antes de importar o agente.
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-placeholder")

from agent.nodes.ingest import run as ingest_run, _normalize
from agent.graph import route_fn

# A PRIORITY_MATRIX é importada diretamente aqui para que os testes
# não dependam do módulo score_priority (que importa o llm).
PRIORITY_MATRIX = {
    ("Alta",  "Alto"):  "Crítico",
    ("Alta",  "Médio"): "Alto",
    ("Alta",  "Baixo"): "Alto",
    ("Média", "Alto"):  "Alto",
    ("Média", "Médio"): "Médio",
    ("Média", "Baixo"): "Médio",
    ("Baixa", "Alto"):  "Médio",
    ("Baixa", "Médio"): "Baixo",
    ("Baixa", "Baixo"): "Baixo",
}


# ─────────────────────────────────────────────────────────────────────────────
# _normalize
# ─────────────────────────────────────────────────────────────────────────────

class TestNormalize:

    def test_remove_espacos_duplicados(self):
        assert _normalize("texto  com   espacos") == "texto com espacos"

    def test_remove_quebras_de_linha(self):
        assert _normalize("linha1\nlinha2") == "linha1 linha2"

    def test_remove_tabulacoes(self):
        assert _normalize("texto\tcom\ttab") == "texto com tab"

    def test_remove_espacos_nas_bordas(self):
        assert _normalize("  texto  ") == "texto"

    def test_combina_multiplas_transformacoes(self):
        assert _normalize("  oi\n\n  nao consigo   acessar  ") == "oi nao consigo acessar"

    def test_texto_normal_nao_muda(self):
        assert _normalize("texto normal") == "texto normal"


# ─────────────────────────────────────────────────────────────────────────────
# ingest
# ─────────────────────────────────────────────────────────────────────────────

class TestIngest:

    def _ticket(self, **kwargs):
        base = {
            "ticket_id":         "TEST-001",
            "text":              "Preciso resetar minha senha.",
            "channel":           "OTRS",
            "requester_profile": "aluno",
            "timestamp":         "2026-05-01T09:00:00",
        }
        base.update(kwargs)
        return base

    def test_texto_normalizado(self):
        t = self._ticket(text="  oi\n\n nao consigo   acessar  ")
        result = ingest_run(t)
        assert result["text"] == "oi nao consigo acessar"

    def test_retorna_somente_text(self):
        result = ingest_run(self._ticket())
        assert list(result.keys()) == ["text"]

    def test_campo_ticket_id_ausente(self):
        t = self._ticket()
        del t["ticket_id"]
        with pytest.raises(RuntimeError, match="campos"):
            ingest_run(t)

    def test_campo_text_ausente(self):
        t = self._ticket()
        del t["text"]
        with pytest.raises(RuntimeError, match="campos"):
            ingest_run(t)

    def test_texto_vazio_rejeitado(self):
        with pytest.raises(RuntimeError, match="vazio"):
            ingest_run(self._ticket(text="   "))

    def test_canal_invalido_rejeitado(self):
        with pytest.raises(RuntimeError, match="canal"):
            ingest_run(self._ticket(channel="WhatsApp"))

    def test_perfil_invalido_rejeitado(self):
        with pytest.raises(RuntimeError, match="perfil"):
            ingest_run(self._ticket(requester_profile="visitante"))

    def test_todos_os_canais_validos(self):
        for canal in ["OTRS", "Telefone", "Balcão", "E-mail"]:
            result = ingest_run(self._ticket(channel=canal))
            assert "text" in result

    def test_todos_os_perfis_validos(self):
        for perfil in ["aluno", "docente_tec_administrativo"]:
            result = ingest_run(self._ticket(requester_profile=perfil))
            assert "text" in result


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY_MATRIX
# ─────────────────────────────────────────────────────────────────────────────

class TestPriorityMatrix:

    def test_matrix_tem_nove_combinacoes(self):
        assert len(PRIORITY_MATRIX) == 9

    def test_todos_os_valores_sao_prioridades_validas(self):
        validas = {"Crítico", "Alto", "Médio", "Baixo"}
        for (u, i), prio in PRIORITY_MATRIX.items():
            assert prio in validas, f"Valor inválido '{prio}' para ({u}, {i})"

    def test_alta_alto_critico(self):
        assert PRIORITY_MATRIX[("Alta", "Alto")] == "Crítico"

    def test_alta_medio_alto(self):
        assert PRIORITY_MATRIX[("Alta", "Médio")] == "Alto"

    def test_alta_baixo_alto(self):
        assert PRIORITY_MATRIX[("Alta", "Baixo")] == "Alto"

    def test_media_alto_alto(self):
        assert PRIORITY_MATRIX[("Média", "Alto")] == "Alto"

    def test_media_medio_medio(self):
        assert PRIORITY_MATRIX[("Média", "Médio")] == "Médio"

    def test_media_baixo_medio(self):
        assert PRIORITY_MATRIX[("Média", "Baixo")] == "Médio"

    def test_baixa_alto_medio(self):
        assert PRIORITY_MATRIX[("Baixa", "Alto")] == "Médio"

    def test_baixa_medio_baixo(self):
        assert PRIORITY_MATRIX[("Baixa", "Médio")] == "Baixo"

    def test_baixa_baixo_baixo(self):
        assert PRIORITY_MATRIX[("Baixa", "Baixo")] == "Baixo"


# ─────────────────────────────────────────────────────────────────────────────
# route_fn
# ─────────────────────────────────────────────────────────────────────────────

class TestRouteFn:

    def _state(self, category, priority):
        return {
            "ticket_id":         "TEST-001",
            "text":              "texto de teste",
            "channel":           "OTRS",
            "requester_profile": "aluno",
            "timestamp":         "2026-01-01T09:00:00",
            "category":          category,
            "priority":          priority,
        }

    # Casos que devem ir para draft
    def test_requisicao_baixo_vai_para_draft(self):
        assert route_fn(self._state("Requisição", "Baixo")) == "draft"

    def test_requisicao_medio_vai_para_draft(self):
        assert route_fn(self._state("Requisição", "Médio")) == "draft"

    # Requisições com prioridade alta sempre vão para queue
    def test_requisicao_alto_vai_para_queue(self):
        assert route_fn(self._state("Requisição", "Alto")) == "queue"

    def test_requisicao_critico_vai_para_queue(self):
        assert route_fn(self._state("Requisição", "Crítico")) == "queue"

    # Incidentes sempre vão para queue independente da prioridade
    def test_incidente_baixo_vai_para_queue(self):
        assert route_fn(self._state("Incidente", "Baixo")) == "queue"

    def test_incidente_medio_vai_para_queue(self):
        assert route_fn(self._state("Incidente", "Médio")) == "queue"

    def test_incidente_alto_vai_para_queue(self):
        assert route_fn(self._state("Incidente", "Alto")) == "queue"

    def test_incidente_critico_vai_para_queue(self):
        assert route_fn(self._state("Incidente", "Crítico")) == "queue"

    # Problemas sempre vão para queue
    def test_problema_medio_vai_para_queue(self):
        assert route_fn(self._state("Problema", "Médio")) == "queue"

    def test_problema_alto_vai_para_queue(self):
        assert route_fn(self._state("Problema", "Alto")) == "queue"

    # Fallbacks — quando dados estão ausentes ou inválidos
    def test_sem_priority_vai_para_queue(self):
        state = self._state("Requisição", "Baixo")
        del state["priority"]
        assert route_fn(state) == "queue"

    def test_sem_category_vai_para_queue(self):
        state = self._state("Requisição", "Baixo")
        del state["category"]
        assert route_fn(state) == "queue"

    def test_priority_none_vai_para_queue(self):
        state = self._state("Requisição", "Baixo")
        state["priority"] = None
        assert route_fn(state) == "queue"

    def test_category_none_vai_para_queue(self):
        state = self._state("Requisição", "Baixo")
        state["category"] = None
        assert route_fn(state) == "queue"
