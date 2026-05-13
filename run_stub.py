from dotenv import load_dotenv
from agent.graph import graph

load_dotenv()

TEST_TICKETS = [
    {
        "ticket_id":         "STUB-001",
        "text":              "Preciso resetar minha senha do e-mail institucional, esqueci depois das férias, mas ainda consigo usar o e-mail",
        "channel":           "OTRS",
        "requester_profile": "docente_tec_administrativo",
        "timestamp":         "2026-05-07T09:00:00",
    },
    {
        "ticket_id":         "STUB-002",
        "text":              "O SIGProj está completamente fora do ar desde as 8h. Todo o departamento está parado.",
        "channel":           "Telefone",
        "requester_profile": "docente_tec_administrativo",
        "timestamp":         "2026-05-07T09:30:00",
    },
    {
        "ticket_id":         "STUB-003",
        "text":              "Oi, não tô conseguindo entrar no portal do aluno.",
        "channel":           "E-mail",
        "requester_profile": "aluno",
        "timestamp":         "2026-05-07T10:00:00",
    },
]

for ticket in TEST_TICKETS:
    print(f"\n── {ticket['ticket_id']} ────────────────────────────────")
    print(f"Texto:  {ticket['text']}...")
    print(f"Canal:  {ticket['channel']} | Perfil: {ticket['requester_profile']}")

    result = graph.invoke(ticket)

    print(f"Urgência:      {result.get('urgency')} × Impacto: {result.get('impact')}")
    print(f"Prioridade:    {result.get('priority')}")
    print(f"Categoria:     {result.get('category')}")
    print(f"Serviço:       {result.get('service_type')}")
    print(f"Fila:          {result.get('queue')}")
    print(f"Rota:          {result.get('route_decision')}")

    if result.get("draft_response"):
        print(f"Draft:         {result['draft_response']}...")
