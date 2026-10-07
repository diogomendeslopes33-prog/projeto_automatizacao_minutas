# conformidade/limiares.py
# Verificação de limiares por tipo de procedimento e tipo de objecto
# Art. 17º, 19º, 20º, 21º e 22º CCP
# Lei n.º 98/97, de 26 de Agosto (LOPTC) — visto prévio do Tribunal de Contas
#
# NOTA DE REVISÃO LEGISLATIVA:
#   Os limiares do CCP (art. 19º, 20º, 21º e 22º) e os limiares comunitários
#   (art. 474º/3 CCP) estão sujeitos a actualização periódica. Verificar
#   alterações ao CCP antes de reutilizar este ficheiro.
#   Os limiares da LOPTC (art. 44º e 45º) encontram-se em proposta de
#   alteração legislativa à data de Maio de 2026 — verificar publicação
#   em Diário da República antes de reutilizar este ficheiro.
#
# Versão 4 — Junho 2026
# Estado: Por validar

LIMIARES = {
    "Empreitada": {
        "ajuste_directo":  30_000,
        "consulta_previa": 150_000,
    },
    "Aquisição de bens": {
        "ajuste_directo":  20_000,
        "consulta_previa": 75_000,
    },
    "Serviços": {
        "ajuste_directo":  20_000,
        "consulta_previa": 75_000,
    },
    "Outros": {
        "ajuste_directo":  50_000,
        "consulta_previa": 100_000,
    },
}

LIMIARES_JOUE = {
    "Empreitada":        5_404_000,
    "Aquisição de bens":   216_000,
    "Serviços":            216_000,
    "Outros":              216_000,
}

LIMIARES_DISPENSA_22 = {
    "Empreitada":        1_000_000,
    "Aquisição de bens":    80_000,
    "Serviços":             80_000,
    "Outros":               80_000,
}

LIMIAR_TC_CONTRATO   = 750_000
LIMIAR_TC_ACUMULADO  = 950_000

_ALIASES = {
    "empreitada":            "Empreitada",
    "empreitada de obras":   "Empreitada",
    "obras":                 "Empreitada",
    "aquisição de bens":     "Aquisição de bens",
    "bens":                  "Aquisição de bens",
    "bens móveis":           "Aquisição de bens",
    "locação de bens":       "Aquisição de bens",
    "serviços":              "Serviços",
    "aquisição de serviços": "Serviços",
    "prestação de serviços": "Serviços",
}


def _normalizar_tipo_objeto(tipo_objeto: str) -> str:
    """Normaliza o valor de TIPO_OBJETO para uma das chaves de LIMIARES."""
    if not tipo_objeto:
        return "Outros"
    return _ALIASES.get(tipo_objeto.strip().lower(), "Outros")


def _limiar_seguinte(tipo_objeto: str, tipo_procedimento: str) -> tuple:
    """
    Devolve (limiar, descrição) do procedimento imediatamente mais exigente
    face ao procedimento actual. Usado para orientar o técnico nos alertas
    de acumulados e fraccionamento.
    """
    limiares    = LIMIARES[tipo_objeto]
    limiar_joue = LIMIARES_JOUE[tipo_objeto]

    if tipo_procedimento == "Ajuste Directo":
        return (
            limiares["consulta_previa"],
            limiar_joue,
            "consulta prévia",
            "concurso público",
        )
    elif tipo_procedimento == "Consulta Prévia":
        return (
            limiar_joue,
            None,
            "concurso público",
            None,
        )
    elif tipo_procedimento == "Concurso Público":
        return (
            limiar_joue,
            None,
            "concurso público com publicação no JOUE",
            None,
        )
    return (None, None, None, None)


def verificar_limiar_procedimento(dados):
    alertas = []

    tipo_procedimento = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    tipo_objeto       = _normalizar_tipo_objeto(dados.get("TIPO_OBJETO") or "")
    preco_base        = dados.get("PRECO_BASE")

    if preco_base is None:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 19º/20º/21º CCP",
            "campo":    "PRECO_BASE",
            "mensagem": "Não foi possível determinar o preço base. "
                        "A verificação do limiar aplicável não pode ser efectuada.",
        })
        return alertas

    limiares    = LIMIARES[tipo_objeto]
    limiar_joue = LIMIARES_JOUE[tipo_objeto]

    if tipo_procedimento == "Ajuste Directo":
        limite = limiares["ajuste_directo"]
        if preco_base >= limite:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 19º/20º/21º CCP",
                "campo":    "PRECO_BASE",
                "mensagem": (
                    f"O valor do contrato ({preco_base:,.2f} €) é igual ou superior "
                    f"ao limiar de ajuste directo para '{tipo_objeto}' ({limite:,.2f} €). "
                    f"O procedimento seleccionado não é admissível por via do critério do "
                    f"valor, a menos que exista fundamentação de critério material, caso "
                    f"em que deverá ser alvo de análise do tipo de procedimento escolhido "
                    f"ou da respectiva fundamentação."
                ),
            })

    elif tipo_procedimento == "Consulta Prévia":
        limite = limiares["consulta_previa"]
        if preco_base >= limite:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 19º/20º/21º CCP",
                "campo":    "PRECO_BASE",
                "mensagem": (
                    f"O valor do contrato ({preco_base:,.2f} €) é igual ou superior "
                    f"ao limiar de consulta prévia para '{tipo_objeto}' ({limite:,.2f} €). "
                    f"O procedimento seleccionado não é admissível."
                ),
            })

    elif tipo_procedimento == "Concurso Público":
        if preco_base >= limiar_joue:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 19º/20º CCP e art. 474º/3 CCP",
                "campo":    "TIPO_PROCEDIMENTO",
                "mensagem": (
                    f"O valor do contrato ({preco_base:,.2f} €) é igual ou superior "
                    f"ao limiar comunitário para '{tipo_objeto}' ({limiar_joue:,.2f} €). "
                    f"É obrigatória a publicação de anúncio no Jornal Oficial da União "
                    f"Europeia. O procedimento deve ser qualificado como concurso público "
                    f"com publicação internacional."
                ),
            })

    elif tipo_procedimento == "Concurso Público Internacional":
        if preco_base < limiar_joue:
            alertas.append({
                "nivel":    "info",
                "artigo":   "art. 19º/20º CCP e art. 474º/3 CCP",
                "campo":    "TIPO_PROCEDIMENTO",
                "mensagem": (
                    f"O valor do contrato ({preco_base:,.2f} €) é inferior ao limiar "
                    f"comunitário para '{tipo_objeto}' ({limiar_joue:,.2f} €). "
                    f"A publicação no Jornal Oficial da União Europeia não é obrigatória "
                    f"por força do valor, ainda que seja sempre admissível."
                ),
            })

    return alertas


def verificar_fracionamento_art22(dados):
    alertas = []

    tipo_objeto       = _normalizar_tipo_objeto(dados.get("TIPO_OBJETO") or "")
    tipo_procedimento = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    preco_base        = dados.get("PRECO_BASE") or 0
    acum_cpv          = dados.get("ACUM_CPV")
    acum_objeto       = dados.get("ACUM_OBJETO") or []

    limiares    = LIMIARES[tipo_objeto]
    limiar_disp = LIMIARES_DISPENSA_22[tipo_objeto]
    limiar_joue = LIMIARES_JOUE[tipo_objeto]

    if acum_cpv is None:
        return alertas

    total_acumulado = preco_base + acum_cpv

    dentro_dispensa = (
        preco_base < limiar_disp
        and total_acumulado > 0
        and preco_base / total_acumulado <= 0.20
    )

    if dentro_dispensa:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 22º/2 CCP",
            "campo":    "ACUM_CPV",
            "mensagem": (
                f"O valor do presente procedimento ({preco_base:,.2f} €) é inferior "
                f"ao limiar de dispensa para '{tipo_objeto}' ({limiar_disp:,.2f} €) "
                f"e representa menos de 20% do somatório acumulado ({total_acumulado:,.2f} €). "
                f"Pode aplicar-se a dispensa prevista no art. 22º/2 CCP, mas é necessário "
                f"que o técnico fundamente expressamente essa opção no processo."
            ),
        })

    if tipo_procedimento == "Ajuste Directo":
        limiar_cp   = limiares["consulta_previa"]
        if total_acumulado >= limiar_joue:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 22º/1 CCP",
                "campo":    "ACUM_CPV",
                "mensagem": (
                    f"O somatório do valor do presente procedimento ({preco_base:,.2f} €) "
                    f"com contratos e procedimentos similares acumulados ({acum_cpv:,.2f} €) "
                    f"totaliza {total_acumulado:,.2f} €, valor igual ou superior ao limiar "
                    f"comunitário para '{tipo_objeto}' ({limiar_joue:,.2f} €). "
                    f"Caso estas prestações sejam do mesmo tipo e susceptíveis de constituir "
                    f"objecto de um único contrato, deverá ser avaliada a necessidade de "
                    f"adoptar concurso público com publicação no JOUE."
                ),
            })
        elif total_acumulado >= limiar_cp:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 22º/1 CCP",
                "campo":    "ACUM_CPV",
                "mensagem": (
                    f"O somatório do valor do presente procedimento ({preco_base:,.2f} €) "
                    f"com contratos e procedimentos similares acumulados ({acum_cpv:,.2f} €) "
                    f"totaliza {total_acumulado:,.2f} €, valor igual ou superior ao limiar "
                    f"de consulta prévia para '{tipo_objeto}' ({limiar_cp:,.2f} €). "
                    f"Caso estas prestações sejam do mesmo tipo e susceptíveis de constituir "
                    f"objecto de um único contrato, deverá ser avaliada a necessidade de "
                    f"adoptar consulta prévia ou concurso público, conforme o valor agregado."
                ),
            })
        elif total_acumulado >= limiares["ajuste_directo"]:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 22º/1 CCP",
                "campo":    "ACUM_CPV",
                "mensagem": (
                    f"O somatório do valor do presente procedimento ({preco_base:,.2f} €) "
                    f"com contratos e procedimentos similares acumulados ({acum_cpv:,.2f} €) "
                    f"totaliza {total_acumulado:,.2f} €, valor igual ou superior ao limiar "
                    f"de ajuste directo para '{tipo_objeto}' ({limiares['ajuste_directo']:,.2f} €). "
                    f"Verificar se o procedimento adoptado é adequado ao valor agregado."
                ),
            })

    elif tipo_procedimento == "Consulta Prévia":
        if total_acumulado >= limiar_joue:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 22º/1 CCP",
                "campo":    "ACUM_CPV",
                "mensagem": (
                    f"O somatório do valor do presente procedimento ({preco_base:,.2f} €) "
                    f"com contratos e procedimentos similares acumulados ({acum_cpv:,.2f} €) "
                    f"totaliza {total_acumulado:,.2f} €, valor igual ou superior ao limiar "
                    f"comunitário para '{tipo_objeto}' ({limiar_joue:,.2f} €). "
                    f"Caso estas prestações sejam do mesmo tipo e susceptíveis de constituir "
                    f"objecto de um único contrato, deverá ser avaliada a necessidade de "
                    f"adoptar concurso público com publicação no JOUE."
                ),
            })
        elif total_acumulado >= limiares["consulta_previa"]:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 22º/1 CCP",
                "campo":    "ACUM_CPV",
                "mensagem": (
                    f"O somatório do valor do presente procedimento ({preco_base:,.2f} €) "
                    f"com contratos e procedimentos similares acumulados ({acum_cpv:,.2f} €) "
                    f"totaliza {total_acumulado:,.2f} €, valor igual ou superior ao limiar "
                    f"de consulta prévia para '{tipo_objeto}' ({limiares['consulta_previa']:,.2f} €). "
                    f"Verificar se o procedimento adoptado é adequado ao valor agregado."
                ),
            })

    elif tipo_procedimento == "Concurso Público":
        if total_acumulado >= limiar_joue:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 22º/1 CCP",
                "campo":    "ACUM_CPV",
                "mensagem": (
                    f"O somatório do valor do presente procedimento ({preco_base:,.2f} €) "
                    f"com contratos e procedimentos similares acumulados ({acum_cpv:,.2f} €) "
                    f"totaliza {total_acumulado:,.2f} €, valor igual ou superior ao limiar "
                    f"comunitário para '{tipo_objeto}' ({limiar_joue:,.2f} €). "
                    f"Caso estas prestações sejam do mesmo tipo e susceptíveis de constituir "
                    f"objecto de um único contrato, deverá ser avaliada a necessidade de "
                    f"adoptar concurso público com publicação no JOUE."
                ),
            })

    if acum_objeto:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "art. 22º/1/b) CCP",
            "campo":    "ACUM_OBJETO",
            "mensagem": (
                f"Foram identificados contratos similares celebrados nos últimos 12 meses "
                f"com objecto análogo ao presente procedimento. Deverá ser avaliado se, "
                f"aquando do lançamento do primeiro procedimento, a entidade adjudicante "
                f"devesse ter previsto a necessidade dos procedimentos subsequentes, com "
                f"impacto na escolha do procedimento aplicável (art. 22º/1/b) CCP)."
            ),
        })

    return alertas


def verificar_visto_tribunal_contas(dados):
    alertas = []

    preco_base = dados.get("PRECO_BASE") or 0
    acum_cpv   = dados.get("ACUM_CPV") or 0
    acum_objeto = dados.get("ACUM_OBJETO") or []

    if preco_base >= LIMIAR_TC_CONTRATO:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "Lei n.º 98/97, de 26 de Agosto (LOPTC)",
            "campo":    "PRECO_BASE",
            "mensagem": (
                f"O valor do contrato ({preco_base:,.2f} €) é igual ou superior a "
                f"{LIMIAR_TC_CONTRATO:,.2f} €. O contrato está sujeito a fiscalização "
                f"prévia do Tribunal de Contas antes da sua celebração. "
                f"NOTA: os limiares da LOPTC encontram-se em proposta de alteração "
                f"legislativa — verificar publicação em Diário da República."
            ),
        })

    total_relacionados = preco_base + acum_cpv + sum(
        c.get("valor", 0) for c in acum_objeto if isinstance(c, dict)
    )

    if total_relacionados >= LIMIAR_TC_ACUMULADO and preco_base < LIMIAR_TC_CONTRATO:
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "Lei n.º 98/97, de 26 de Agosto (LOPTC)",
            "campo":    "ACUM_CPV",
            "mensagem": (
                f"O somatório do valor do presente contrato ({preco_base:,.2f} €) com "
                f"contratos relacionados acumulados totaliza {total_relacionados:,.2f} €, "
                f"valor igual ou superior a {LIMIAR_TC_ACUMULADO:,.2f} €. "
                f"Deverá ser avaliado se o conjunto está sujeito a fiscalização prévia "
                f"do Tribunal de Contas. "
                f"NOTA: os limiares da LOPTC encontram-se em proposta de alteração "
                f"legislativa — verificar publicação em Diário da República."
            ),
        })

    return alertas


def verificar_lotes(dados):
    # Art. 46º-A/2 CCP
    # Na formação de contratos de aquisição ou locação de bens ou aquisição
    # de serviços de valor superior a € 135 000, e empreitadas de valor
    # superior a € 500 000, a decisão de não contratar por lotes deve ser
    # fundamentada.
    #
    # CORRECÇÃO (Junho 2026): o nível do alerta passou de "aviso" para
    # "erro". A obrigação de fundamentação prevista no art. 46º-A/2 não é
    # uma faculdade dispensável — é sempre exigida acima do limiar, e a
    # ausência de fundamentação não fica sanada só por o técnico optar por
    # não dividir em lotes. A fundamentação (quando exista) é precisamente
    # o que resolve este erro no processo — não é uma alternativa a ele.
    # Por isso o alerta deve bloquear o avanço como qualquer outro erro de
    # conformidade, tal como já acontecia, por exemplo, com a obrigação de
    # caução do art. 88º/1 CCP (ver verificar_obrigatoriedade_caucao em
    # caucao.py, que já usa "erro" no mesmo género de situação).
    #
    # Nota: o n.º 3 isenta as entidades dos art. 7º e 12º CCP — a UA não
    # é uma dessas entidades.

    alertas = []

    tipo_objeto = _normalizar_tipo_objeto(dados.get("TIPO_OBJETO") or "")
    preco_base  = dados.get("PRECO_BASE")
    tem_lotes   = dados.get("TEM_LOTES")

    if preco_base is None:
        return alertas

    if tem_lotes:
        return alertas

    if tipo_objeto == "Empreitada":
        limiar_lotes = 500_000
    elif tipo_objeto in ("Aquisição de bens", "Serviços"):
        limiar_lotes = 135_000
    else:
        return alertas

    if preco_base > limiar_lotes:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "art. 46º-A/2 CCP",
            "campo":    "TEM_LOTES",
            "mensagem": (
                f"O valor do contrato ({preco_base:,.2f} €) é superior ao limiar de "
                f"{limiar_lotes:,.2f} € para '{tipo_objeto}'. A decisão de não dividir "
                f"o contrato em lotes tem de ser expressamente fundamentada no processo, "
                f"nos termos do art. 46º-A/2 CCP — a fundamentação é obrigatória acima "
                f"deste limiar e não pode ser omitida. Constituem fundamento admissível, "
                f"designadamente, a incindibilidade técnica ou funcional das prestações "
                f"ou a maior eficiência da gestão de um único contrato."
            ),
        })

    return alertas


def verificar_acumulado_fornecedor(dados):
    # Art. 113º/2, 113º/6 e 114º/2 CCP
    # Limite de acumulação do valor contratado com o MESMO fornecedor,
    # através da MESMA forma de adjudicação (ajuste directo ou consulta
    # prévia), no período de referência do ERP (ano económico + 2 anos
    # anteriores).
    #
    # DECISÃO DE ARQUITECTURA: este limite reutiliza os MESMOS valores já
    # definidos em LIMIARES (art. 19º-21º) — não existe um sistema de
    # limiares próprio para este artigo. O valor que não pode ser
    # excedido, acumulado com o mesmo fornecedor, é o mesmo que define se
    # o procedimento é, em geral, admissível por via do valor. Confirmado
    # nos próprios dados do ERP: o relatório por fornecedor mostra
    # "Limite: 19 999,99 €" para Bens/Serviços + Ajuste Directo, que
    # corresponde a LIMIARES["Aquisição de bens"]["ajuste_directo"] =
    # 20 000 (convenção do ERP de expressar "inferior a" como valor-0,01).
    #
    # Este procedimento só se aplica a Ajuste Directo e Consulta Prévia —
    # Concurso Público não tem este limite por fornecedor específico.
    #
    # Fonte de dados: cada empresa em dados["EMPRESAS_CONVIDADAS"] pode
    # ter a chave "acum_fornecedor" (produzida por
    # acumulados_empresa.carregar_acumulado_fornecedor a partir do
    # relatório PDF do ERP), com a estrutura:
    #   {"categorias": {"Bens ou Serviços": {"Ajuste Direto": {...}}, ...}}
    #
    # Se a empresa não tiver "acum_fornecedor" (PDF não obtido/não
    # verificado), gera-se um AVISO a pedir confirmação manual — nunca se
    # assume 0 silenciosamente (mesmo princípio já aplicado ao campo
    # CAUCAO em ler_pdf.py).

    alertas = []

    tipo_procedimento = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    tipo_objeto        = _normalizar_tipo_objeto(dados.get("TIPO_OBJETO") or "")
    preco_base         = dados.get("PRECO_BASE")
    empresas           = dados.get("EMPRESAS_CONVIDADAS") or []

    # Mapeamento tipo_objeto (interno) → categoria do ERP no relatório PDF
    _MAPA_CATEGORIA_ERP = {
        "Aquisição de bens": "Bens ou Serviços",
        "Serviços":          "Bens ou Serviços",
        "Empreitada":        "Empreitadas de obras públicas",
    }
    # Mapeamento tipo_procedimento (interno) → forma de adjudicação do ERP
    _MAPA_FORMA_ERP = {
        "Ajuste Directo":  "Ajuste Direto",
        "Consulta Prévia": "Consulta Prévia",
    }

    categoria_erp = _MAPA_CATEGORIA_ERP.get(tipo_objeto)
    forma_erp     = _MAPA_FORMA_ERP.get(tipo_procedimento)

    if categoria_erp is None or forma_erp is None or preco_base is None:
        # "Outros", Concurso Público, ou preço base indeterminado — este
        # limite por fornecedor não se aplica ou não pode ser calculado
        return alertas

    for empresa in empresas:
        nome            = empresa.get("nome", "[sem nome]")
        acum_fornecedor = empresa.get("acum_fornecedor")

        if acum_fornecedor is None:
            alertas.append({
                "nivel":    "aviso",
                "artigo":   "art. 113º/2, 113º/6 e 114º/2 CCP",
                "campo":    "EMPRESAS_CONVIDADAS",
                "mensagem": (
                    f"Não foi possível verificar o valor já acumulado, por "
                    f"esta forma de adjudicação, com a entidade '{nome}'. "
                    f"Confirmar manualmente no ERP antes de convidar esta "
                    f"entidade, nos termos do art. 113º/2, 113º/6 e "
                    f"114º/2 CCP."
                ),
            })
            continue

        dados_categoria = (
            acum_fornecedor.get("categorias", {})
            .get(categoria_erp, {})
            .get(forma_erp)
        )
        if dados_categoria is None:
            continue  # sem histórico nesta categoria — nada a acumular

        disponivel = dados_categoria.get("disponivel")
        if disponivel is None:
            continue

        if preco_base > disponivel:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 113º/2, 113º/6 e 114º/2 CCP",
                "campo":    "EMPRESAS_CONVIDADAS",
                "mensagem": (
                    f"O valor do presente procedimento ({preco_base:,.2f} €) "
                    f"excede o valor ainda disponível para contratar com "
                    f"'{nome}' por {tipo_procedimento.lower()} em "
                    f"'{tipo_objeto}' ({disponivel:,.2f} €), face ao "
                    f"acumulado já contratado com esta entidade no período "
                    f"de referência do ERP "
                    f"({dados_categoria.get('total', 0):,.2f} € de "
                    f"{dados_categoria.get('limite', 0):,.2f} €). Não é "
                    f"admissível manter esta entidade convidada por esta "
                    f"via sem recorrer a procedimento mais exigente."
                ),
            })

    return alertas


def verificar_limiares(dados):
    """
    Agrega todas as verificações de limiares, fraccionamento, lotes e visto prévio.
    Cobre os art. 19º, 20º, 21º, 22º, 46º-A e 474º/3 CCP
    e a Lei n.º 98/97, de 26 de Agosto (LOPTC).
    Devolve lista consolidada de alertas.
    """
    alertas = []
    alertas.extend(verificar_limiar_procedimento(dados))
    alertas.extend(verificar_fracionamento_art22(dados))
    alertas.extend(verificar_lotes(dados))
    alertas.extend(verificar_visto_tribunal_contas(dados))
    alertas.extend(verificar_acumulado_fornecedor(dados))
    return alertas