# conformidade/__init__.py
# Agregador principal do pacote de verificação de conformidade CCP
# Sistema de Automação de Contratação Pública — Universidade de Aveiro
#
# Versão 2 — Maio 2026
# Estado: ESQUELETO — completar à medida que cada módulo for validado

# ---------------------------------------------------------------------------
# Imports — descomentar à medida que cada módulo for implementado e validado
# ---------------------------------------------------------------------------

from .limiares        import verificar_limiares        # art. 19º-22º e LOPTC  ✅
from .interpretativas import verificar_interpretativas  # normas não automatizáveis ✅

# from .ajuste_directo  import verificar_ajuste_directo  # art. 112º-129º
# from .consulta_previa import verificar_consulta_previa # art. 130º-132º
# from .juri            import verificar_juri            # art. 67º-69º
# from .caucao          import verificar_caucao          # art. 88º-91º
# from .prazos          import verificar_prazos          # art. 63º-66º
# from .execucao        import verificar_execucao        # art. 290º-313º
# from .empreitadas     import verificar_empreitadas     # art. 343º+


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

    # ------------------------------------------------------------------
    # Módulos activos
    # ------------------------------------------------------------------

    alertas_limiares = verificar_limiares(dados)
    todos_alertas.extend(alertas_limiares)
    por_modulo["limiares"] = alertas_limiares

    alertas_interpretativas = verificar_interpretativas(dados)
    todos_alertas.extend(alertas_interpretativas)
    por_modulo["interpretativas"] = alertas_interpretativas

    # ------------------------------------------------------------------
    # Módulos por activar — descomentar quando validados
    # ------------------------------------------------------------------

    # alertas_ajuste = verificar_ajuste_directo(dados)
    # todos_alertas.extend(alertas_ajuste)
    # por_modulo["ajuste_directo"] = alertas_ajuste

    # alertas_consulta = verificar_consulta_previa(dados)
    # todos_alertas.extend(alertas_consulta)
    # por_modulo["consulta_previa"] = alertas_consulta

    # alertas_juri = verificar_juri(dados)
    # todos_alertas.extend(alertas_juri)
    # por_modulo["juri"] = alertas_juri

    # alertas_caucao = verificar_caucao(dados)
    # todos_alertas.extend(alertas_caucao)
    # por_modulo["caucao"] = alertas_caucao

    # alertas_prazos = verificar_prazos(dados)
    # todos_alertas.extend(alertas_prazos)
    # por_modulo["prazos"] = alertas_prazos

    # alertas_execucao = verificar_execucao(dados)
    # todos_alertas.extend(alertas_execucao)
    # por_modulo["execucao"] = alertas_execucao

    # alertas_empreitadas = verificar_empreitadas(dados)
    # todos_alertas.extend(alertas_empreitadas)
    # por_modulo["empreitadas"] = alertas_empreitadas

    # ------------------------------------------------------------------
    # Consolidar resultados
    # ------------------------------------------------------------------

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
            nivel  = alerta.get("nivel",    "?").upper()
            artigo = alerta.get("artigo",   "—")
            campo  = alerta.get("campo",    "—")
            msg    = alerta.get("mensagem", "—")
            juridico = " [ANÁLISE JURÍDICA]" if alerta.get("requer_analise_juridica") else ""
            print(f"  [{nivel}]{juridico} {artigo} | {campo}")
            print(f"    {msg}")
            print()

    print("=" * 60 + "\n")