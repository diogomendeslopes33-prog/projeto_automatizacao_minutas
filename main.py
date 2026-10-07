# main.py
# Orquestrador do sistema de automatização de minutas.
# Fluxo: configuração → selecção de formulários → processamento → supervisão

import sys
import os
sys.path.insert(0, r"Z:\01_python_contratacao")

from sequencia.sequencia import gerar_procedimento_id, registar_evento
import config
from logger import log_tecnico, log_utilizacao, registar_decisao_terminal, log_supervisao
from ler_pdf import ler_dados
from mapeamento import seleccionar_minuta, listar_minutas
from preencher_word import preencher_minuta


def seleccionar_formularios():
    formularios = config.listar_formularios()

    if not formularios:
        print("\n❌ Nenhum formulário encontrado em", config.PASTA_FORMULARIOS)
        return []

    print("\n" + "=" * 60)
    print("FORMULÁRIOS DISPONÍVEIS")
    print("=" * 60)

    for i, f in enumerate(formularios, start=1):
        print(f"  {i}. {os.path.basename(f)}")

    print(f"  {len(formularios) + 1}. Correr todos")
    print("  0. Sair")
    print()

    while True:
        opcao = input("Opção: ").strip()

        if opcao == "0":
            return []

        if opcao == str(len(formularios) + 1):
            return formularios

        try:
            idx = int(opcao) - 1
            if 0 <= idx < len(formularios):
                return [formularios[idx]]
        except ValueError:
            pass

        print("Opção inválida. Tenta novamente.")


def processar(caminho_pdf):
    nome_formulario = os.path.basename(caminho_pdf)
    print(f"\n{'=' * 60}")
    print(f"A processar: {nome_formulario}")
    print(f"{'=' * 60}")

    print("\n→ A ler formulário...")
    try:
        dados = ler_dados(caminho_pdf)
    except Exception as e:
        print(f"❌ Erro ao ler formulário: {e}")
        return

    tipo_procedimento = dados.get("TIPO_PROCEDIMENTO") or "Desconhecido"
    tipo_objeto       = dados.get("TIPO_OBJETO") or "Desconhecido"

    print(f"  Procedimento: {tipo_procedimento}")
    print(f"  Objeto: {tipo_objeto}")
    print(f"  Campos extraídos: {sum(1 for v in dados.values() if v is not None)}")

    procedimento_id = gerar_procedimento_id(
        formulario=nome_formulario,
        tipo_procedimento=tipo_procedimento,
        tipo_contrato=tipo_objeto,
        utilizador=config.UTILIZADOR
    )
    print(f"  ID: {procedimento_id}")

    log_utilizacao(caminho_pdf, tipo_procedimento, tipo_objeto, procedimento_id)

    print("\n→ A enriquecer empresas convidadas (Camada B)...")
    try:
        from apinforma import enriquecer_empresas_convidadas
        empresas_convidadas = dados.get("EMPRESAS_CONVIDADAS") or []
        if empresas_convidadas:
            dados["EMPRESAS_CONVIDADAS"] = enriquecer_empresas_convidadas(empresas_convidadas)
            total_relacionadas = sum(
                len(e.get("relacionadas", [])) for e in dados["EMPRESAS_CONVIDADAS"]
            )
            print(f"  ✅ {len(empresas_convidadas)} empresa(s) processada(s), "
                  f"{total_relacionadas} relacionada(s) identificada(s)")
            registar_evento(procedimento_id, "automatizador_minutas",
                           "camada_b_concluida",
                           {"empresas": len(empresas_convidadas),
                            "relacionadas": total_relacionadas},
                           config.UTILIZADOR)
        else:
            print("  Sem empresas convidadas — Camada B ignorada")
    except Exception as e:
        print(f"⚠️  Erro na Camada B: {e}")
        registar_evento(procedimento_id, "automatizador_minutas",
                       "erro_camada_b", {"erro": str(e)}, config.UTILIZADOR)

    # 3.2 Camada C — Acumulados ERP
    #
    # Três fontes independentes, cada uma opcional — a ausência de
    # qualquer uma delas NUNCA é tratada como "0 acumulado" (isso
    # esconderia um caso real de fraccionamento ou de ultrapassagem de
    # limiar). Fica sempre "não verificado" e é o próprio alerta de
    # conformidade (verificar_acumulado_fornecedor, verificar_
    # fracionamento_art22, verificar_visto_tribunal_contas) que decide o
    # que fazer com essa ausência — nunca este bloco de integração.
    print("\n→ A carregar acumulados ERP (Camada C)...")
    try:
        from acumulados_empresa import carregar_acumulado_fornecedor
        from acumulados_cpv import calcular_acumulado_cpv
        from acumulados_objeto import calcular_acumulado_objeto

        # --- Por fornecedor (uma PDF por NIF, em acumulados_empresa/) ---
        empresas_convidadas = dados.get("EMPRESAS_CONVIDADAS") or []
        n_verificadas = 0
        for empresa in empresas_convidadas:
            nif_empresa = empresa.get("nif")
            if not nif_empresa:
                continue
            caminho_pdf_acum = os.path.join(
                config.PASTA_ACUMULADOS_EMPRESA, f"{nif_empresa}.PDF"
            )
            if os.path.isfile(caminho_pdf_acum):
                empresa["acum_fornecedor"] = carregar_acumulado_fornecedor(caminho_pdf_acum)
                if empresa["acum_fornecedor"] is not None:
                    n_verificadas += 1
            else:
                empresa["acum_fornecedor"] = None
        print(f"  Fornecedor: {n_verificadas}/{len(empresas_convidadas)} empresa(s) com acumulado verificado")

        # --- Por CPV (um .xlsx por código CPV, em acumulados_cpv/) ---
        cpv_actual = dados.get("CPV")
        if cpv_actual:
            caminho_cpv = os.path.join(config.PASTA_ACUMULADOS_CPV, f"{cpv_actual}.xlsx")
            if os.path.isfile(caminho_cpv):
                dados["ACUM_CPV"] = calcular_acumulado_cpv(caminho_cpv)
                print(f"  CPV {cpv_actual}: acumulado = "
                      f"{dados['ACUM_CPV']:,.2f} €" if dados["ACUM_CPV"] is not None
                      else f"  CPV {cpv_actual}: não verificado")
            else:
                dados["ACUM_CPV"] = None
                print(f"  CPV {cpv_actual}: ficheiro não encontrado — não verificado")
        else:
            dados["ACUM_CPV"] = None

        # --- Por objecto (pasta com um .xlsx por termo, em acumulados_objetos/{REFERENCIA}/) ---
        referencia = dados.get("REFERENCIA")
        objeto_actual = dados.get("OBJETO")
        if referencia and objeto_actual:
            pasta_objeto = os.path.join(config.PASTA_ACUMULADOS_OBJETOS, referencia)
            if os.path.isdir(pasta_objeto):
                dados["ACUM_OBJETO"] = calcular_acumulado_objeto(pasta_objeto, objeto_actual)
                n_similares = len(dados["ACUM_OBJETO"]) if dados["ACUM_OBJETO"] is not None else 0
                print(f"  Objecto: {n_similares} contrato(s) semanticamente semelhante(s)"
                      if dados["ACUM_OBJETO"] is not None
                      else "  Objecto: não verificado")
            else:
                dados["ACUM_OBJETO"] = None
                print(f"  Objecto: pasta '{referencia}/' não encontrada — não verificado")
        else:
            dados["ACUM_OBJETO"] = None

        registar_evento(procedimento_id, "automatizador_minutas",
                       "camada_c_concluida",
                       {
                           "empresas_verificadas": n_verificadas,
                           "acum_cpv_verificado": dados.get("ACUM_CPV") is not None,
                           "acum_objeto_verificado": dados.get("ACUM_OBJETO") is not None,
                       },
                       config.UTILIZADOR)

    except Exception as e:
        print(f"⚠️  Erro na Camada C: {e}")
        registar_evento(procedimento_id, "automatizador_minutas",
                       "erro_camada_c", {"erro": str(e)}, config.UTILIZADOR)
        dados.setdefault("ACUM_CPV", None)
        dados.setdefault("ACUM_OBJETO", None)

    print("\n→ A verificar conformidade...")
    try:
        from conformidade import verificar_conformidade, imprimir_relatorio

        dados_conformidade = dict(dados)
        dados_conformidade["GESTOR_CONTRATO"]            = dados.get("GESTOR_NOME")
        dados_conformidade["SUBSTITUTO_GESTOR_CONTRATO"] = dados.get("SUBSTITUTO_NOME")

        _reverter_tipo_objeto = {
            "Bens":       "Aquisição de bens",
            "Serviços":   "Aquisição de serviços",
            "Empreitada": "Empreitada",
        }
        dados_conformidade["TIPO_OBJETO"] = _reverter_tipo_objeto.get(
            dados.get("TIPO_OBJETO", ""), dados.get("TIPO_OBJETO", "")
        )

        resultado_conformidade = verificar_conformidade(dados_conformidade)
        imprimir_relatorio(resultado_conformidade)

        # CORRECÇÃO: deixou de perguntar "Continuar mesmo assim?" quando há
        # erros de conformidade. O processamento avança sempre e gera a
        # minuta e o relatório — o relatório de conformidade já lista os
        # erros com destaque, e é aí que o técnico os revê antes de aprovar
        # o procedimento, não num prompt de terminal que bloqueia o fluxo.
        # O registo de auditoria mantém-se: fica sempre gravado no
        # sequencia/ que houve erros e que se avançou apesar deles, para
        # que a história do procedimento continue completa e rastreável.
        if resultado_conformidade["total_erros"] > 0:
            print(f"⚠️  {resultado_conformidade['total_erros']} erro(s) de conformidade detectado(s).")
            print("   O técnico deve verificar os alertas no relatório antes de aprovar o procedimento.")
            print("   A minuta e o relatório de conformidade serão gerados na mesma, para consulta.")
            registar_evento(procedimento_id, "automatizador_minutas",
                           "avancado_apesar_de_erros_conformidade",
                           {"erros": resultado_conformidade["total_erros"]},
                           config.UTILIZADOR)

        log_tecnico("conformidade_verificada", {
            "erros":  resultado_conformidade["total_erros"],
            "avisos": resultado_conformidade["total_avisos"],
            "info":   resultado_conformidade["total_info"],
        }, procedimento_id)

        registar_evento(procedimento_id, "automatizador_minutas",
                       "conformidade_verificada",
                       {
                           "erros":   resultado_conformidade["total_erros"],
                           "avisos":  resultado_conformidade["total_avisos"],
                           "info":    resultado_conformidade["total_info"],
                           # Lista completa dos alertas, não só as contagens —
                           # necessário para a Verificação 2 (analisar_minuta.py)
                           # calcular o delta real (resolvidos/novos/persistentes).
                           "alertas": resultado_conformidade["alertas"],
                           # Dados que a Verificação 2 REUTILIZA sem re-extrair
                           # da minuta (ver âmbito em analisar_minuta.py) — vêm
                           # de fontes externas (Camada B/C) que podem mudar
                           # entretanto na origem; para a comparação ser justa,
                           # a Verificação 2 tem de usar exactamente os mesmos
                           # valores que a Verificação 1 usou, não valores
                           # recalculados no momento da própria Verificação 2.
                           "dados_reutilizaveis": {
                               "TIPO_PROCEDIMENTO":  dados_conformidade.get("TIPO_PROCEDIMENTO"),
                               "TIPO_OBJETO":        dados_conformidade.get("TIPO_OBJETO"),
                               "PRECO_BASE":         dados_conformidade.get("PRECO_BASE"),
                               "EMPRESAS_CONVIDADAS": dados_conformidade.get("EMPRESAS_CONVIDADAS"),
                               "ACUM_CPV":           dados_conformidade.get("ACUM_CPV"),
                               "ACUM_OBJETO":        dados_conformidade.get("ACUM_OBJETO"),
                           },
                       },
                       config.UTILIZADOR)

    except Exception as e:
        print(f"⚠️  Não foi possível verificar conformidade: {e}")
        resultado_conformidade = None

    print("\n→ A seleccionar minuta...")
    try:
        caminho_minuta = seleccionar_minuta(tipo_procedimento, tipo_objeto)
        print(f"  Minuta: {os.path.basename(caminho_minuta)}")
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ {e}")
        registar_evento(procedimento_id, "automatizador_minutas", "erro_minuta",
                       {"erro": str(e)}, config.UTILIZADOR)
        return

    print("\n→ A preencher minuta...")
    nome_output   = f"minuta_{procedimento_id}.docx"
    caminho_output = os.path.join(config.PASTA_OUTPUT, nome_output)

    try:
        preencher_minuta(caminho_minuta, dados, caminho_output, procedimento_id)
        print(f"  ✅ Minuta gerada: {nome_output}")
    except Exception as e:
        print(f"❌ Erro ao preencher minuta: {e}")
        registar_evento(procedimento_id, "automatizador_minutas", "erro_preenchimento",
                       {"erro": str(e)}, config.UTILIZADOR)
        return

    registar_evento(
        procedimento_id,
        "automatizador_minutas",
        "minuta_gerada",
        {"ficheiro": nome_output, "minuta_base": os.path.basename(caminho_minuta)},
        config.UTILIZADOR
    )

    nome_relatorio    = f"relatorio_{procedimento_id}.docx"
    caminho_relatorio = os.path.join(config.PASTA_OUTPUT, nome_relatorio)
    if resultado_conformidade:
        try:
            from relatorio import gerar_relatorio
            gerar_relatorio(procedimento_id, dados, resultado_conformidade,
                            caminho_relatorio, procedimento_id)
            print(f"  ✅ Relatório gerado: {nome_relatorio}")
        except Exception as e:
            print(f"⚠️  Erro ao gerar relatório: {e}")
            caminho_relatorio = None
    else:
        caminho_relatorio = None

    print()
    decisao = registar_decisao_terminal()
    log_supervisao(caminho_pdf, tipo_procedimento, decisao, procedimento_id)

    if decisao:
        registar_evento(
            procedimento_id,
            "automatizador_minutas",
            "supervisao_registada",
            decisao,
            config.UTILIZADOR
        )

    print(f"\n{'=' * 60}")
    print(f"✅ Concluído — {procedimento_id}")
    print(f"   Minuta:    {caminho_output}")
    print(f"   Relatório: {caminho_relatorio}")
    print(f"{'=' * 60}\n")

    return procedimento_id


def verificar_minuta_final(procedimento_id):
    """
    Verificação 2 — double-check sobre a minuta final já gerada.
    Invocado separadamente da geração original, tipicamente depois de o
    técnico ter revisto o relatório da Verificação 1 e, se necessário,
    corrigido algo directamente na minuta Word.

    Não depende de nenhum estado em memória de uma execução anterior —
    tudo vem do sequencia/ e da própria minuta no disco.
    """
    from analisar_minuta import comparar_com_verificacao_1, gerar_relatorio_verificacao2

    print(f"\n{'=' * 60}")
    print(f"VERIFICAÇÃO 2 — {procedimento_id}")
    print(f"{'=' * 60}")

    caminho_minuta = os.path.join(config.PASTA_OUTPUT, f"minuta_{procedimento_id}.docx")
    if not os.path.isfile(caminho_minuta):
        print(f"❌ Minuta não encontrada: {caminho_minuta}")
        return

    print("\n→ A re-analisar a minuta e a comparar com a Verificação 1...")
    resultado = comparar_com_verificacao_1(procedimento_id, caminho_minuta)

    if resultado is None:
        print("❌ Não foi possível comparar — procedimento não encontrado no "
              "sequencia/, ou a Verificação 1 deste procedimento não tem "
              "dados detalhados guardados (procedimentos gerados antes desta "
              "funcionalidade não são compatíveis).")
        return

    if resultado["campos_inconsistentes"]:
        print(f"\n⚠️  Campos com valores inconsistentes na minuta "
              f"(aparecem contraditórios em sítios diferentes): "
              f"{', '.join(resultado['campos_inconsistentes'])}")

    print(f"\n  Resolvidos:   {len(resultado['resolvidos'])}")
    print(f"  Novos:        {len(resultado['novos'])}")
    print(f"  Persistentes: {len(resultado['persistentes'])}")

    nome_relatorio_v2 = f"relatorio_verificacao2_{procedimento_id}.docx"
    caminho_relatorio_v2 = os.path.join(config.PASTA_OUTPUT, nome_relatorio_v2)
    gerar_relatorio_verificacao2(procedimento_id, resultado, caminho_relatorio_v2)
    print(f"\n  ✅ Relatório gerado: {nome_relatorio_v2}")

    registar_evento(procedimento_id, "automatizador_minutas",
                   "verificacao2_concluida",
                   {
                       "resolvidos":   len(resultado["resolvidos"]),
                       "novos":        len(resultado["novos"]),
                       "persistentes": len(resultado["persistentes"]),
                       "campos_inconsistentes": resultado["campos_inconsistentes"],
                   },
                   config.UTILIZADOR)

    print(f"\n{'=' * 60}\n")


def main():
    # Uso: python main.py                      → fluxo normal (Verificação 1)
    #      python main.py --verificar UA-2026-0030  → Verificação 2 sobre um
    #                                                  procedimento já gerado
    if len(sys.argv) >= 3 and sys.argv[1] == "--verificar":
        verificar_minuta_final(sys.argv[2])
        return

    print("\n" + "=" * 60)
    print("  AUTOMATIZADOR DE MINUTAS — Universidade de Aveiro")
    print("=" * 60)

    if not config.validar_configuracao():
        sys.exit(1)

    formularios = seleccionar_formularios()
    if not formularios:
        print("\nSaindo.\n")
        return

    resultados = []
    for caminho_pdf in formularios:
        resultado = processar(caminho_pdf)
        if resultado:
            resultados.append(resultado)

    if len(formularios) > 1:
        print(f"\n{'=' * 60}")
        print(f"SUMÁRIO — {len(resultados)}/{len(formularios)} formulários processados")
        for r in resultados:
            print(f"  ✅ {r}")
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()