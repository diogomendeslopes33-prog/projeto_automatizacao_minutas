# conformidade/ajuste_directo.py
# Verificação de regras de consulta prévia e ajuste directo
# Art. 112º, 113º, 114º CCP
#
# Versão 2 — Maio 2026
# Estado: Por validar

from .limiares import LIMIARES, _normalizar_tipo_objeto


# ---------------------------------------------------------------------------
# Art. 112º/1 e 114º/1 CCP
# Consulta prévia exige mínimo de três entidades convidadas
# ---------------------------------------------------------------------------

def verificar_numero_convidados(dados):
    # Art. 112º/1 e 114º/1 CCP
    # A consulta prévia é o procedimento em que a entidade adjudicante convida
    # directamente pelo menos três entidades. O ajuste directo convida apenas uma.

    alertas = []

    tipo_procedimento   = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    empresas_convidadas = dados.get("EMPRESAS_CONVIDADAS") or []
    n_convidadas        = len(empresas_convidadas)

    if tipo_procedimento == "Consulta Prévia":
        if n_convidadas < 3:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 112º/1 e art. 114º/1 CCP",
                "campo":    "EMPRESAS_CONVIDADAS",
                "mensagem": (
                    f"A consulta prévia exige o convite a pelo menos três entidades. "
                    f"O procedimento tem apenas {n_convidadas} entidade(s) convidada(s)."
                ),
            })

    elif tipo_procedimento == "Ajuste Directo":
        if n_convidadas == 0:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 112º/2 CCP",
                "campo":    "EMPRESAS_CONVIDADAS",
                "mensagem": "O ajuste directo exige o convite a uma entidade. "
                            "Não foram identificadas entidades convidadas.",
            })
        elif n_convidadas > 1:
            alertas.append({
                "nivel":    "erro",
                "artigo":   "art. 112º/2 CCP",
                "campo":    "EMPRESAS_CONVIDADAS",
                "mensagem": (
                    f"O ajuste directo prevê o convite a uma única entidade. "
                    f"Foram identificadas {n_convidadas} entidades convidadas."
                ),
            })

    return alertas


# ---------------------------------------------------------------------------
# Art. 113º/2 e 113º/6 CCP
# Acumulados por empresa convidada e empresas relacionadas
# ---------------------------------------------------------------------------

def verificar_acumulados_empresas(dados):
    # Art. 113º/2 CCP
    # Não podem ser convidadas entidades às quais a entidade adjudicante já
    # tenha adjudicado, no ano económico em curso e nos dois anos económicos
    # anteriores, contratos cujo preço contratual acumulado seja igual ou
    # superior aos limiares das alíneas c) e d) do art. 19º e 20º CCP.
    #
    # Art. 113º/6 CCP
    # A restrição aplica-se igualmente a entidades especialmente relacionadas
    # com as entidades referidas no n.º 2 — nomeadamente entidades que partilhem
    # representantes legais ou sócios, ou que se encontrem em relação de
    # participação, domínio ou grupo.
    #
    # A verificação corre individualmente para cada empresa convidada e para
    # cada uma das suas empresas relacionadas detectadas via ERP/Informa D&B.
    # Se qualquer uma atingir o limiar, a empresa convidada não pode ser convidada.

    alertas = []

    tipo_objeto         = _normalizar_tipo_objeto(dados.get("TIPO_OBJETO") or "")
    tipo_procedimento   = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    empresas_convidadas = dados.get("EMPRESAS_CONVIDADAS") or []

    if tipo_procedimento not in ("Ajuste Directo", "Consulta Prévia"):
        return alertas

    limiares = LIMIARES.get(tipo_objeto, LIMIARES["Outros"])

    if tipo_procedimento == "Ajuste Directo":
        limiar     = limiares["ajuste_directo"]
        artigo_ref = "art. 113º/2 e alínea d) do art. 19º/20º CCP"
    else:
        limiar     = limiares["consulta_previa"]
        artigo_ref = "art. 113º/2 e alínea c) do art. 19º/20º CCP"

    for empresa in empresas_convidadas:
        nome_convidada = empresa.get("nome", "Empresa sem nome")
        nif_convidada  = empresa.get("nif", "NIF desconhecido")

        # Verificar a própria empresa convidada
        acum_total = empresa.get("acum_total") or 0
        if acum_total >= limiar:
            alertas.append({
                "nivel":    "erro",
                "artigo":   artigo_ref,
                "campo":    "EMPRESAS_CONVIDADAS",
                "mensagem": (
                    f"A entidade '{nome_convidada}' (NIF {nif_convidada}) não pode ser "
                    f"convidada. O acumulado contratual dos últimos três anos económicos "
                    f"({acum_total:,.2f} €) é igual ou superior ao limiar aplicável "
                    f"({limiar:,.2f} €), nos termos do {artigo_ref}."
                ),
            })
            continue

        # Verificar empresas relacionadas
        relacionadas = empresa.get("relacionadas") or []
        for rel in relacionadas:
            nome_rel = rel.get("nome", "Empresa relacionada sem nome")
            nif_rel  = rel.get("nif", "NIF desconhecido")
            acum_rel = rel.get("acum_total") or 0

            if acum_rel >= limiar:
                alertas.append({
                    "nivel":    "erro",
                    "artigo":   "art. 113º/2 e 113º/6 CCP",
                    "campo":    "EMPRESAS_CONVIDADAS",
                    "mensagem": (
                        f"A entidade '{nome_convidada}' (NIF {nif_convidada}) não pode ser "
                        f"convidada. A empresa com ela relacionada '{nome_rel}' (NIF {nif_rel}) "
                        f"apresenta um acumulado contratual dos últimos três anos económicos "
                        f"({acum_rel:,.2f} €) igual ou superior ao limiar aplicável "
                        f"({limiar:,.2f} €), nos termos do art. 113º/2 e 113º/6 CCP."
                    ),
                })
                break

    return alertas


# ---------------------------------------------------------------------------
# Art. 114º/2 CCP
# Entidades convidadas não podem ser especialmente relacionadas entre si
# Verificação por cruzamento de NIFs de empresas relacionadas e de sócios/
# administradores entre todas as entidades convidadas
# ---------------------------------------------------------------------------

def verificar_relacao_entre_convidadas(dados):
    # Art. 114º/2 CCP
    # As entidades a convidar não podem ser especialmente relacionadas entre si,
    # considerando-se como tais as entidades que partilhem representantes legais
    # ou sócios, ou que se encontrem em relação de simples participação,
    # de participação recíproca, de domínio ou de grupo.
    #
    # A verificação cruza:
    # 1. NIFs das empresas relacionadas de cada convidada — se o NIF de uma
    #    convidada aparece nas relacionadas de outra, são especialmente relacionadas
    # 2. NIFs de sócios/administradores — se partilham algum sócio ou
    #    administrador, são especialmente relacionadas

    alertas = []

    tipo_procedimento   = (dados.get("TIPO_PROCEDIMENTO") or "").strip()
    empresas_convidadas = dados.get("EMPRESAS_CONVIDADAS") or []

    if tipo_procedimento not in ("Consulta Prévia",):
        # Art. 114º/2 aplica-se à consulta prévia; no ajuste directo
        # só existe uma convidada, pelo que não há cruzamento possível
        return alertas

    if len(empresas_convidadas) < 2:
        return alertas

    # Construir índice: NIF → dados da convidada
    indice_nifs    = {e.get("nif"): e for e in empresas_convidadas if e.get("nif")}
    conflitos_nifs = set()   # pares (nif_a, nif_b) já reportados — evitar duplicados

    for i, empresa_a in enumerate(empresas_convidadas):
        nif_a  = empresa_a.get("nif", "")
        nome_a = empresa_a.get("nome", "Empresa sem nome")

        # NIFs das relacionadas de A e sócios de A
        nifs_rel_a   = {r.get("nif") for r in (empresa_a.get("relacionadas") or []) if r.get("nif")}
        socios_a     = set(empresa_a.get("socios") or [])

        for empresa_b in empresas_convidadas[i + 1:]:
            nif_b  = empresa_b.get("nif", "")
            nome_b = empresa_b.get("nome", "Empresa sem nome")

            par = tuple(sorted([nif_a, nif_b]))
            if par in conflitos_nifs:
                continue

            nifs_rel_b = {r.get("nif") for r in (empresa_b.get("relacionadas") or []) if r.get("nif")}
            socios_b   = set(empresa_b.get("socios") or [])

            # 1. Verificar se uma convidada é relacionada da outra
            if nif_b in nifs_rel_a or nif_a in nifs_rel_b:
                conflitos_nifs.add(par)
                alertas.append({
                    "nivel":    "erro",
                    "artigo":   "art. 114º/2 CCP",
                    "campo":    "EMPRESAS_CONVIDADAS",
                    "mensagem": (
                        f"As entidades '{nome_a}' (NIF {nif_a}) e '{nome_b}' (NIF {nif_b}) "
                        f"são especialmente relacionadas entre si — uma figura na estrutura "
                        f"de participação da outra — e não podem ser convidadas em simultâneo, "
                        f"nos termos do art. 114º/2 CCP."
                    ),
                })
                continue

            # 2. Verificar partilha de sócios/administradores
            socios_comuns = socios_a & socios_b
            if socios_comuns:
                conflitos_nifs.add(par)
                nifs_comuns_str = ", ".join(socios_comuns)
                alertas.append({
                    "nivel":    "erro",
                    "artigo":   "art. 114º/2 CCP",
                    "campo":    "EMPRESAS_CONVIDADAS",
                    "mensagem": (
                        f"As entidades '{nome_a}' (NIF {nif_a}) e '{nome_b}' (NIF {nif_b}) "
                        f"partilham sócio(s) ou administrador(es) (NIF: {nifs_comuns_str}) "
                        f"e não podem ser convidadas em simultâneo, "
                        f"nos termos do art. 114º/2 CCP."
                    ),
                })
                continue

            # 3. Verificar cruzamento entre relacionadas de A e relacionadas de B
            nifs_comuns_rel = nifs_rel_a & nifs_rel_b
            if nifs_comuns_rel:
                conflitos_nifs.add(par)
                alertas.append({
                    "nivel":    "aviso",
                    "artigo":   "art. 114º/2 CCP",
                    "campo":    "EMPRESAS_CONVIDADAS",
                    "mensagem": (
                        f"As entidades '{nome_a}' (NIF {nif_a}) e '{nome_b}' (NIF {nif_b}) "
                        f"partilham empresa(s) relacionada(s) na sua estrutura de participação. "
                        f"Deverá ser avaliado se existe relação de especial proximidade que "
                        f"impeça o convite simultâneo, nos termos do art. 114º/2 CCP."
                    ),
                })

    return alertas


# ---------------------------------------------------------------------------
# Função agregadora
# ---------------------------------------------------------------------------

def verificar_ajuste_directo(dados):
    """
    Agrega todas as verificações de consulta prévia e ajuste directo.
    Cobre os art. 112º, 113º e 114º CCP.
    Devolve lista consolidada de alertas.
    """
    alertas = []
    alertas.extend(verificar_numero_convidados(dados))
    alertas.extend(verificar_acumulados_empresas(dados))
    alertas.extend(verificar_relacao_entre_convidadas(dados))
    return alertas