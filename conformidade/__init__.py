# conformidade/__init__.py
# Agregador principal do pacote de verificação de conformidade CCP
# Sistema de Automação de Contratação Pública — Universidade de Aveiro
#
# Versão 4 — Maio 2026

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from .limiares                            import verificar_limiares                # art. 19º-22º, 46º-A e LOPTC  ✅
from .ajustes_diretos_e_consultas_previas import verificar_ajuste_directo          # art. 112º-117º               ✅
from .juri_gc_sgc                         import verificar_juri                    # art. 67º-69º e 290º-A        ✅
from .caucao                              import verificar_caucao                  # art. 88º-90º e 353º          ✅
from .duracao_contrato                    import verificar_duracao_contrato        # art. 48º, 65º, 440º          ✅
from .execucao_orcamental                 import verificar_execucao_orcamental     # DL 127/2008, DL 13-A/2025    ✅
from .interpretativas                     import verificar_interpretativas         # normas não automatizáveis    ✅


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def verificar_conformidade(dados: dict) -> dict:
    """
    Ponto de entrada único do verificador de conformidade CCP.

    Recebe o dicionário `dados` extraído do formulário PDF e corre
    todas as verificações activas, devolvendo um relatório estruturado.

    Parâmetros
    ----------
    dados : dict
        Dicionário com os campos extraídos do formulário (ver README do projecto).

    Devolve
    -------
    dict com a estrutura:
        {
            "total_erros":   int,
            "total_avisos":  int,
            "total_info":    int,
            "alertas":       list[dict],   # todos os alertas consolidados
            "por_modulo":    dict          # alertas agrupados por módulo
        }
    """

    todos_alertas = []
    por_modulo    = {}

    alertas_limiares = verificar_limiares(dados)
    todos_alertas.extend(alertas_limiares)
    por_modulo["limiares"] = alertas_limiares

    alertas_ajuste = verificar_ajuste_directo(dados)
    todos_alertas.extend(alertas_ajuste)
    por_modulo["ajustes_diretos_e_consultas_previas"] = alertas_ajuste

    alertas_juri = verificar_juri(dados)
    todos_alertas.extend(alertas_juri)
    por_modulo["juri_gc_sgc"] = alertas_juri

    alertas_caucao = verificar_caucao(dados)
    todos_alertas.extend(alertas_caucao)
    por_modulo["caucao"] = alertas_caucao

    alertas_duracao = verificar_duracao_contrato(dados)
    todos_alertas.extend(alertas_duracao)
    por_modulo["duracao_contrato"] = alertas_duracao

    alertas_exec_orc = verificar_execucao_orcamental(dados)
    todos_alertas.extend(alertas_exec_orc)
    por_modulo["execucao_orcamental"] = alertas_exec_orc

    alertas_interpretativas = verificar_interpretativas(dados)
    todos_alertas.extend(alertas_interpretativas)
    por_modulo["interpretativas"] = alertas_interpretativas

    return {
        "total_erros":  sum(1 for a in todos_alertas if a["nivel"] == "erro"),
        "total_avisos": sum(1 for a in todos_alertas if a["nivel"] == "aviso"),
        "total_info":   sum(1 for a in todos_alertas if a["nivel"] == "info"),
        "alertas":      todos_alertas,
        "por_modulo":   por_modulo,
    }


# ---------------------------------------------------------------------------
# Utilitário de diagnóstico — útil durante desenvolvimento e testes
# ---------------------------------------------------------------------------

def imprimir_relatorio(resultado: dict) -> None:
    """
    Imprime no terminal um resumo legível do resultado da verificação.
    Útil para testes rápidos durante o desenvolvimento.
    """

    print("\n" + "=" * 60)
    print("RELATÓRIO DE CONFORMIDADE CCP")
    print("=" * 60)
    print(f"  Erros  : {resultado['total_erros']}")
    print(f"  Avisos : {resultado['total_avisos']}")
    print(f"  Info   : {resultado['total_info']}")
    print("-" * 60)

    if not resultado["alertas"]:
        print("  Nenhum alerta encontrado.")
    else:
        for alerta in resultado["alertas"]:
            nivel    = alerta.get("nivel",    "?").upper()
            artigo   = alerta.get("artigo",   "—")
            campo    = alerta.get("campo",    "—")
            msg      = alerta.get("mensagem", "—")
            juridico = " [ANÁLISE JURÍDICA]" if alerta.get("requer_analise_juridica") else ""
            print(f"  [{nivel}]{juridico} {artigo} | {campo}")
            print(f"    {msg}")
            print()

    print("=" * 60 + "\n")