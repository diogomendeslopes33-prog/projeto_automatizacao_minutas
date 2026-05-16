# conformidade/execucao_orcamental.py
# Verificação de regras de execução orçamental
# Decreto-Lei n.º 127/2008, de 21 de Julho — regime da assunção de compromissos
# Lei de Enquadramento Orçamental (LEO)
#
# NOTA DE REVISÃO LEGISLATIVA:
#   O limiar de extensão de encargos (€ 500 000) pode ser alterado anualmente
#   pela Lei do Orçamento do Estado. Valor actualmente fixado pelo Decreto-Lei
#   n.º 13-A/2025 (Lei de Execução do Orçamento do Estado para 2025).
#   Verificar diploma de execução orçamental vigente antes de reutilizar
#   este ficheiro.
#
# Versão 2 — Maio 2026
# Estado: Por validar

# ---------------------------------------------------------------------------
# Limiares (em euros)
# ---------------------------------------------------------------------------

# Limiar de extensão de encargos — DL 127/2008 e DL n.º 13-A/2025
# Despesa plurianual com qualquer ano subsequente ao corrente > este valor
# obriga a despacho de extensão de encargos antes da decisão de contratar.
# NOTA: verificar diploma de execução orçamental vigente — valor confirmado para 2025.
LIMIAR_EXTENSAO_ENCARGOS = 500_000


# ---------------------------------------------------------------------------
# Extensão de encargos — DL 127/2008 e DL n.º 13-A/2025
# Despesa plurianual com qualquer ano subsequente > 500 000 €
# obriga a despacho de extensão de encargos antes da decisão de contratar
# ---------------------------------------------------------------------------

def verificar_extensao_encargos(dados):
    # DL 127/2008, de 21 de Julho, e DL n.º 13-A/2025
    # Em contratos com despesa plurianual, se a despesa prevista em qualquer
    # ano subsequente ao ano corrente for superior a 500 000 €, é obrigatória
    # a emissão de despacho de extensão de encargos antes da decisão de contratar.
    # DESPESA_PLURIANUAL_VALORES é uma lista ordenada a partir do primeiro
    # ano do contrato. O primeiro elemento corresponde ao ano de início;
    # os subsequentes aos anos seguintes.

    alertas = []

    despesa_plurianual = (dados.get("DESPESA_PLURIANUAL") or "").strip().lower()

    if despesa_plurianual != "sim":
        return alertas

    valores = dados.get("DESPESA_PLURIANUAL_VALORES") or []

    if not valores:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "DL 127/2008, de 21 de Julho",
            "campo":    "DESPESA_PLURIANUAL_VALORES",
            "mensagem": "O procedimento tem despesa plurianual assinalada mas não foram "
                        "identificados os valores por ano. Não é possível verificar a "
                        "obrigatoriedade de despacho de extensão de encargos.",
        })
        return alertas

    # O primeiro elemento é o ano de início do contrato — os anos subsequentes
    # são os que determinam a obrigação de extensão de encargos
    anos_subsequentes = valores[1:]

    anos_com_obrigacao = []
    for i, valor in enumerate(anos_subsequentes):
        ano_relativo = i + 2  # ano 2, 3, 4, ... do contrato
        if valor is not None and valor > LIMIAR_EXTENSAO_ENCARGOS:
            anos_com_obrigacao.append((ano_relativo, valor))

    if anos_com_obrigacao:
        detalhe = "; ".join(
            f"ano {a} do contrato: {v:,.2f} €"
            for a, v in anos_com_obrigacao
        )
        alertas.append({
            "nivel":    "erro",
            "artigo":   "DL 127/2008, de 21 de Julho e DL n.º 13-A/2025",
            "campo":    "DESPESA_PLURIANUAL_VALORES",
            "mensagem": (
                f"A despesa prevista em ano(s) subsequente(s) ao ano corrente supera o "
                f"limiar de {LIMIAR_EXTENSAO_ENCARGOS:,.2f} €, sendo obrigatória a emissão "
                f"de despacho de extensão de encargos antes da decisão de contratar. "
                f"Anos em incumprimento: {detalhe}. "
                f"NOTA: verificar diploma de execução orçamental vigente quanto ao limiar aplicável."
            ),
        })

    return alertas


# ---------------------------------------------------------------------------
# Cabimento por ano — DL 127/2008
# Em despesas plurianuais, cada ano deve ter cabimento orçamental assegurado.
# A responsabilidade pela correcta distribuição dos encargos pelos anos do
# contrato é da unidade requisitante e do técnico de contratação pública.
# ---------------------------------------------------------------------------

def verificar_cabimento_plurianual(dados):
    # DL 127/2008, de 21 de Julho
    # Em contratos com despesa plurianual, deve existir cabimento orçamental
    # para cada ano de execução do contrato. A ausência de cabimento em
    # qualquer dos anos impede a assunção do compromisso.
    # A responsabilidade pela correcta distribuição dos encargos pelos anos
    # do contrato é da unidade requisitante e do técnico de contratação pública.

    alertas = []

    despesa_plurianual = (dados.get("DESPESA_PLURIANUAL") or "").strip().lower()

    if despesa_plurianual != "sim":
        return alertas

    anos    = dados.get("DESPESA_PLURIANUAL_ANOS")
    valores = dados.get("DESPESA_PLURIANUAL_VALORES") or []

    if not anos:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "DL 127/2008, de 21 de Julho",
            "campo":    "DESPESA_PLURIANUAL_ANOS",
            "mensagem": "O procedimento tem despesa plurianual assinalada mas o número "
                        "de anos não foi declarado. Não é possível verificar o cabimento "
                        "orçamental por ano.",
        })
        return alertas

    if len(valores) != anos:
        alertas.append({
            "nivel":    "erro",
            "artigo":   "DL 127/2008, de 21 de Julho",
            "campo":    "DESPESA_PLURIANUAL_VALORES",
            "mensagem": (
                f"O número de anos declarado ({anos}) não corresponde ao número de valores "
                f"por ano fornecidos ({len(valores)}). A unidade requisitante e o técnico "
                f"de contratação pública devem verificar se todos os anos da despesa "
                f"plurianual têm valor declarado para efeitos de cabimento orçamental."
            ),
        })
        return alertas

    # Verificar se algum valor por ano é zero ou negativo
    anos_sem_valor = [
        i + 1 for i, v in enumerate(valores)
        if v is None or v <= 0
    ]

    if anos_sem_valor:
        anos_str = ", ".join(f"ano {a}" for a in anos_sem_valor)
        alertas.append({
            "nivel":    "aviso",
            "artigo":   "DL 127/2008, de 21 de Julho",
            "campo":    "DESPESA_PLURIANUAL_VALORES",
            "mensagem": (
                f"Os seguintes anos da despesa plurianual apresentam valor zero ou não "
                f"declarado: {anos_str}. A unidade requisitante e o técnico de contratação "
                f"pública devem confirmar que o cabimento orçamental está assegurado para "
                f"cada ano de execução do contrato."
            ),
        })

    alertas.append({
        "nivel":    "info",
        "artigo":   "DL 127/2008, de 21 de Julho",
        "campo":    "DESPESA_PLURIANUAL_VALORES",
        "mensagem": (
            f"Contrato com despesa plurianual de {anos} ano(s). "
            f"A correcta distribuição dos encargos pelos anos do contrato e a confirmação "
            f"do cabimento orçamental por ano são da responsabilidade da unidade "
            f"requisitante e do técnico de contratação pública."
        ),
    })

    return alertas


# ---------------------------------------------------------------------------
# Função agregadora
# ---------------------------------------------------------------------------

def verificar_execucao_orcamental(dados):
    """
    Agrega todas as verificações de execução orçamental.
    Cobre o DL 127/2008, de 21 de Julho, e o DL n.º 13-A/2025.
    Devolve lista consolidada de alertas.
    """
    alertas = []
    alertas.extend(verificar_extensao_encargos(dados))
    alertas.extend(verificar_cabimento_plurianual(dados))
    return alertas