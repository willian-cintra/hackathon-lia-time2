import json
import os
import sys
from unittest.mock import patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-placeholder")

from agent.nodes.score_priority import run as score_run, FAILSAFE_PRIORITY
from agent.nodes.classify_type  import run as classify_run, FAILSAFE_CATEGORY


# ── Estado base reutilizado em todos os testes ────────────────────────────────

def _state(**kwargs) -> dict:
    """Monta um estado mínimo válido. Aceita overrides via kwargs."""
    base = {
        "ticket_id":         "TEST-001",
        "text":              "Não consigo acessar o sistema.",
        "channel":           "OTRS",
        "requester_profile": "aluno",
        "timestamp":         "2026-05-14T09:00:00",
        "tokens_used":       0,
    }
    base.update(kwargs)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# score_priority — caminho feliz (LLM responde corretamente)
# ─────────────────────────────────────────────────────────────────────────────

class TestScorePrioritySucesso:
    """LLM retorna JSON válido com todos os campos corretos."""

    def _mock(self, urgency: str, impact: str, justification: str = "texto ok", tokens: int = 100):
        """Monta a tupla que call_llm retornaria em caso de sucesso."""
        resposta = json.dumps({
            "urgency":       urgency,
            "impact":        impact,
            "justification": justification,
        })
        return (resposta, tokens)

    def test_media_baixo_retorna_medio(self):
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Média", "Baixo")):
            resultado = score_run(_state())
        assert resultado["urgency"]  == "Média"
        assert resultado["impact"]   == "Baixo"
        assert resultado["priority"] == "Médio"

    def test_alta_alto_retorna_critico(self):
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Alta", "Alto")):
            resultado = score_run(_state())
        assert resultado["priority"] == "Crítico"

    def test_alta_medio_retorna_alto(self):
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Alta", "Médio")):
            resultado = score_run(_state())
        assert resultado["priority"] == "Alto"

    def test_baixa_baixo_retorna_baixo(self):
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Baixa", "Baixo")):
            resultado = score_run(_state())
        assert resultado["priority"] == "Baixo"

    def test_tokens_acumulados_corretamente(self):
        # tokens_used inicial = 50, LLM consome mais 100 → total = 150
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Média", "Baixo", tokens=100)):
            resultado = score_run(_state(tokens_used=50))
        assert resultado["tokens_used"] == 150

    def test_justificativa_preservada(self):
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Média", "Baixo", justification="chamado simples")):
            resultado = score_run(_state())
        assert resultado["priority_justification"] == "chamado simples"

    def test_sem_llm_error_no_sucesso(self):
        # quando tudo funciona, llm_error não deve estar presente no retorno
        with patch("agent.nodes.score_priority.call_llm", return_value=self._mock("Média", "Baixo")):
            resultado = score_run(_state())
        assert "llm_error" not in resultado


# ─────────────────────────────────────────────────────────────────────────────
# score_priority — fail-safe (LLM falha de alguma forma)
# ─────────────────────────────────────────────────────────────────────────────

class TestScorePriorityFailsafe:
    """Verifica que o fail-safe é ativado corretamente em cada tipo de falha."""

    def _assert_failsafe(self, resultado: dict):
        """Atalho: verifica que o fail-safe foi aplicado."""
        assert resultado["priority"] == FAILSAFE_PRIORITY   # prioridade máxima
        assert resultado["llm_error"] is not None            # erro registrado
        assert "score_priority" in resultado["llm_error"]    # origem identificada

    def test_excecao_no_llm_ativa_failsafe(self):
        # LLM lança qualquer exceção (timeout, conexão, etc.)
        with patch("agent.nodes.score_priority.call_llm", side_effect=Exception("connection timeout")):
            resultado = score_run(_state())
        self._assert_failsafe(resultado)

    def test_json_invalido_ativa_failsafe(self):
        # LLM retorna texto que não é JSON
        with patch("agent.nodes.score_priority.call_llm", return_value=("isso não é json {{{", 50)):
            resultado = score_run(_state())
        self._assert_failsafe(resultado)

    def test_campo_urgency_ausente_ativa_failsafe(self):
        # LLM retorna JSON válido mas sem o campo urgency
        resposta = json.dumps({"impact": "Baixo", "justification": "ok"})
        with patch("agent.nodes.score_priority.call_llm", return_value=(resposta, 50)):
            resultado = score_run(_state())
        self._assert_failsafe(resultado)

    def test_campo_impact_ausente_ativa_failsafe(self):
        resposta = json.dumps({"urgency": "Média", "justification": "ok"})
        with patch("agent.nodes.score_priority.call_llm", return_value=(resposta, 50)):
            resultado = score_run(_state())
        self._assert_failsafe(resultado)

    def test_urgencia_invalida_ativa_failsafe(self):
        # LLM retorna urgência fora do conjunto válido
        resposta = json.dumps({"urgency": "Extrema", "impact": "Baixo", "justification": "ok"})
        with patch("agent.nodes.score_priority.call_llm", return_value=(resposta, 50)):
            resultado = score_run(_state())
        self._assert_failsafe(resultado)

    def test_impacto_invalido_ativa_failsafe(self):
        resposta = json.dumps({"urgency": "Média", "impact": "Nenhum", "justification": "ok"})
        with patch("agent.nodes.score_priority.call_llm", return_value=(resposta, 50)):
            resultado = score_run(_state())
        self._assert_failsafe(resultado)

    def test_failsafe_preserva_tokens_anteriores(self):
        # tokens acumulados antes da falha não devem ser perdidos
        with patch("agent.nodes.score_priority.call_llm", side_effect=Exception("erro")):
            resultado = score_run(_state(tokens_used=200))
        assert resultado["tokens_used"] == 200

    def test_failsafe_tem_urgency_e_impact_validos(self):
        # o estado retornado pelo fail-safe precisa ter campos válidos
        with patch("agent.nodes.score_priority.call_llm", side_effect=Exception("erro")):
            resultado = score_run(_state())
        assert resultado["urgency"] in {"Alta", "Média", "Baixa"}
        assert resultado["impact"]  in {"Alto", "Médio", "Baixo"}


# ─────────────────────────────────────────────────────────────────────────────
# classify_type — caminho feliz
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyTypeSucesso:
    """LLM retorna JSON válido com todos os campos corretos."""

    def _mock(self, category: str, service_type: str = "Suporte de Sistema",
              queue: str = "N1", justification: str = "texto ok", tokens: int = 120):
        resposta = json.dumps({
            "category":     category,
            "service_type": service_type,
            "queue":        queue,
            "justification": justification,
        })
        return (resposta, tokens)

    def test_retorna_requisicao(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=self._mock("Requisição")):
            resultado = classify_run(_state())
        assert resultado["category"] == "Requisição"

    def test_retorna_incidente(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=self._mock("Incidente")):
            resultado = classify_run(_state())
        assert resultado["category"] == "Incidente"

    def test_retorna_problema(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=self._mock("Problema")):
            resultado = classify_run(_state())
        assert resultado["category"] == "Problema"

    def test_campos_retornados_corretamente(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=self._mock("Requisição", "Acesso ao Sistema", "N2", "justificativa aqui")):
            resultado = classify_run(_state())
        assert resultado["service_type"] == "Acesso ao Sistema"
        assert resultado["queue"]        == "N2"
        assert resultado["classification_justification"] == "justificativa aqui"

    def test_tokens_acumulados_corretamente(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=self._mock("Requisição", tokens=120)):
            resultado = classify_run(_state(tokens_used=100))
        assert resultado["tokens_used"] == 220

    def test_sem_llm_error_no_sucesso(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=self._mock("Requisição")):
            resultado = classify_run(_state())
        assert "llm_error" not in resultado


# ─────────────────────────────────────────────────────────────────────────────
# classify_type — fail-safe
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyTypeFailsafe:
    """Verifica que o fail-safe é ativado corretamente em cada tipo de falha."""

    def _assert_failsafe(self, resultado: dict):
        assert resultado["category"] == FAILSAFE_CATEGORY    # categoria conservadora
        assert resultado["llm_error"] is not None             # erro registrado
        assert "classify_type" in resultado["llm_error"]      # origem identificada

    def test_excecao_no_llm_ativa_failsafe(self):
        with patch("agent.nodes.classify_type.call_llm", side_effect=Exception("rate limit")):
            resultado = classify_run(_state())
        self._assert_failsafe(resultado)

    def test_json_invalido_ativa_failsafe(self):
        with patch("agent.nodes.classify_type.call_llm", return_value=("não é json", 50)):
            resultado = classify_run(_state())
        self._assert_failsafe(resultado)

    def test_campo_category_ausente_ativa_failsafe(self):
        resposta = json.dumps({"service_type": "X", "queue": "N1", "justification": "ok"})
        with patch("agent.nodes.classify_type.call_llm", return_value=(resposta, 50)):
            resultado = classify_run(_state())
        self._assert_failsafe(resultado)

    def test_campo_service_type_ausente_ativa_failsafe(self):
        resposta = json.dumps({"category": "Requisição", "queue": "N1", "justification": "ok"})
        with patch("agent.nodes.classify_type.call_llm", return_value=(resposta, 50)):
            resultado = classify_run(_state())
        self._assert_failsafe(resultado)

    def test_categoria_invalida_ativa_failsafe(self):
        # LLM retorna categoria fora do conjunto válido
        resposta = json.dumps({"category": "Sugestão", "service_type": "X", "queue": "N1", "justification": "ok"})
        with patch("agent.nodes.classify_type.call_llm", return_value=(resposta, 50)):
            resultado = classify_run(_state())
        self._assert_failsafe(resultado)

    def test_failsafe_preserva_tokens_anteriores(self):
        with patch("agent.nodes.classify_type.call_llm", side_effect=Exception("erro")):
            resultado = classify_run(_state(tokens_used=300))
        assert resultado["tokens_used"] == 300

    def test_failsafe_categoria_nunca_vai_para_draft(self):
        # a categoria do fail-safe deve garantir roteamento para fila humana
        # ou seja, nunca pode ser "Requisição" (que poderia ir para draft)
        with patch("agent.nodes.classify_type.call_llm", side_effect=Exception("erro")):
            resultado = classify_run(_state())
        assert resultado["category"] != "Requisição"