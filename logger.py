# logger.py
# Notário do sistema — regista todas as acções em três ficheiros .jsonl distintos.
# Todos os módulos importam daqui. Nenhum módulo escreve logs directamente.
# Ponto de evolução futuro: só este ficheiro muda quando o sistema de logging crescer.

import json
import os
from datetime import datetime
import config


def _timestamp():
    """Devolve timestamp no formato ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")


def _escrever(caminho_ficheiro, entrada):
    """
    Escreve uma linha JSON no ficheiro de log indicado.
    Cria o ficheiro se não existir. Append sempre — nunca sobrescreve.
    """
    os.makedirs(os.path.dirname(caminho_ficheiro), exist_ok=True)
    with open(caminho_ficheiro, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def log_tecnico(evento, dados=None, procedimento_id=None):
    """
    Regista um evento interno do sistema.

    Eventos esperados:
        ficheiro_lido, minuta_seleccionada, campo_preenchido,
        campo_sem_valor, erro, duracao

    Exemplo:
        log_tecnico("campo_preenchido", {"campo": "OBJETO", "valor": "Aquisição de cadeiras"})
    """
    entrada = {
        "timestamp": _timestamp(),
        "utilizador": config.UTILIZADOR,
        "procedimento_id": procedimento_id,
        "evento": evento,
        "dados": dados or {}
    }
    caminho = os.path.join(config.PASTA_LOGS, "tecnico.jsonl")
    _escrever(caminho, entrada)


def log_utilizacao(formulario, tipo_procedimento, tipo_contrato, procedimento_id=None):
    """
    Regista uma execução do sistema — um formulário processado.

    Exemplo:
        log_utilizacao("form_001.pdf", "Ajuste Directo", "Serviços")
    """
    entrada = {
        "timestamp": _timestamp(),
        "utilizador": config.UTILIZADOR,
        "procedimento_id": procedimento_id,
        "formulario": os.path.basename(formulario),
        "tipo_procedimento": tipo_procedimento,
        "tipo_contrato": tipo_contrato
    }
    caminho = os.path.join(config.PASTA_LOGS, "utilizacao.jsonl")
    _escrever(caminho, entrada)


def registar_decisao_terminal():
    """
    Apresenta menu de supervisão no terminal e captura a decisão do técnico.
    Isolada para futura substituição por botões Streamlit sem alterar o resto.

    Devolve dict com decisao e fundamentacao, ou None se ignorado.
    """
    print("\n" + "=" * 50)
    print("REGISTO DE SUPERVISÃO")
    print("=" * 50)
    print("O que fez com o output gerado?")
    print("  1 — Aceitei sem alterações")
    print("  2 — Editei antes de usar")
    print("  3 — Rejeitei")
    print("  Enter — Ignorar este registo")

    opcao = input("\nOpção: ").strip()

    if opcao not in ("1", "2", "3"):
        return None

    mapa = {"1": "aceite", "2": "editado", "3": "rejeitado"}
    decisao = mapa[opcao]

    fundamentacao = ""
    if opcao in ("2", "3"):
        fundamentacao = input("Motivo (opcional): ").strip()

    return {
        "decisao": decisao,
        "fundamentacao": fundamentacao
    }


def log_supervisao(formulario, tipo_procedimento, decisao, procedimento_id=None):
    """
    Regista a decisão de supervisão do técnico sobre o output gerado.
    Dados de treino para futuros modelos especializados.

    Exemplo:
        log_supervisao("form_001.pdf", "Ajuste Directo", {"decisao": "editado", "fundamentacao": "..."})
    """
    if decisao is None:
        return

    entrada = {
        "timestamp": _timestamp(),
        "utilizador": config.UTILIZADOR,
        "procedimento_id": procedimento_id,
        "formulario": os.path.basename(formulario),
        "tipo_procedimento": tipo_procedimento,
        "decisao": decisao.get("decisao"),
        "fundamentacao": decisao.get("fundamentacao", "")
    }
    caminho = os.path.join(config.PASTA_LOGS, "supervisao.jsonl")
    _escrever(caminho, entrada)