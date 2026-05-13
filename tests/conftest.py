# tests/conftest.py
import pytest

@pytest.fixture
def ticket_valido():
    return {
        "ticket_id":         "TEST-001",
        "text":              "Preciso resetar minha senha do Passaporte UFMS.",
        "channel":           "OTRS",
        "requester_profile": "aluno",
        "timestamp":         "2026-05-01T09:00:00",
    }
